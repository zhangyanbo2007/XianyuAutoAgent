#!/usr/bin/env python3
"""
照片分类服务 — 在home-computer-ubuntu上运行，提供CLIP分类和人脸聚类API
"""

import os
import io
import base64
import json
import torch
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from PIL import Image
import uvicorn

app = FastAPI()

# 全局模型
clip_model = None
clip_processor = None
face_app = None

# CLIP分类类别
CLIP_CATEGORIES = {
    '人物': 'a photo of a person, portrait, selfie, human face',
    '风景': 'a photo of landscape, nature, mountain, sea, sky, sunset, forest',
    '美食': 'a photo of food, meal, dish, restaurant, cooking',
    '建筑': 'a photo of building, architecture, room, street, house',
    '动物': 'a photo of animal, pet, cat, dog, bird, fish',
    '截图': 'a screenshot of phone or computer screen, UI, app',
    '文档': 'a photo of document, text, paper, receipt, book',
    '表情包': 'a meme, sticker, emoji, cartoon, comic',
}

@app.on_event("startup")
async def load_models():
    global clip_model, clip_processor, face_app

    print("加载CLIP模型...")
    from transformers import CLIPProcessor, CLIPModel
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = clip_model.to("cuda")
    clip_model.eval()
    print("CLIP模型加载完成")

    print("加载人脸检测模型...")
    from insightface.app import FaceAnalysis
    face_app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider'])
    face_app.prepare(ctx_id=0, det_size=(640, 640))
    print("人脸检测模型加载完成")

@app.post("/classify")
async def classify_image(file: UploadFile = File(...)):
    """CLIP分类单张图片"""
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')

        categories = list(CLIP_CATEGORIES.keys())
        texts = list(CLIP_CATEGORIES.values())

        inputs = clip_processor(text=texts, images=image, return_tensors="pt", padding=True)
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = clip_model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)[0].cpu().numpy()

        max_idx = probs.argmax()
        return {
            "category": categories[max_idx],
            "confidence": float(probs[max_idx]),
            "all_scores": {c: float(p) for c, p in zip(categories, probs)}
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/classify_batch")
async def classify_batch(files: list[UploadFile] = File(...)):
    """批量CLIP分类"""
    try:
        images = []
        for file in files:
            contents = await file.read()
            image = Image.open(io.BytesIO(contents)).convert('RGB').resize((224, 224))
            images.append(image)

        categories = list(CLIP_CATEGORIES.keys())
        texts = list(CLIP_CATEGORIES.values())

        inputs = clip_processor(text=texts, images=images, return_tensors="pt", padding=True)
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = clip_model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1).cpu().numpy()

        results = []
        for i in range(len(images)):
            max_idx = probs[i].argmax()
            results.append({
                "category": categories[max_idx],
                "confidence": float(probs[i][max_idx])
            })

        return {"results": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/detect_faces")
async def detect_faces(file: UploadFile = File(...)):
    """检测人脸"""
    try:
        import cv2
        import numpy as np

        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        faces = face_app.get(image)

        results = []
        for face in faces:
            results.append({
                "bbox": face.bbox.tolist(),
                "det_score": float(face.det_score),
                "embedding": face.embedding.tolist()
            })

        return {"faces": results, "count": len(results)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "cuda": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8899)
