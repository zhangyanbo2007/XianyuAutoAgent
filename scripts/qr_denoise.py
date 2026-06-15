#!/usr/bin/env python3
"""QR code denoising - clean up noisy QR code images."""

import sys
import numpy as np
from PIL import Image, ImageFilter


def denoise_qr(input_path: str, output_path: str):
    img = Image.open(input_path).convert("L")  # grayscale
    arr = np.array(img, dtype=np.float64)

    # 1. Median filter to remove salt-and-pepper noise
    img_med = img.filter(ImageFilter.MedianFilter(size=3))
    arr = np.array(img_med, dtype=np.float64)

    # 2. Adaptive thresholding (local mean)
    block = 25
    from scipy.ndimage import uniform_filter
    local_mean = uniform_filter(arr, size=block)
    # pixels darker than local mean - offset → black, else white
    threshold = local_mean - 12
    binary = ((arr < threshold) * 0 + (arr >= threshold) * 255).astype(np.uint8)

    # 3. Morphological cleanup: remove isolated small blobs
    from scipy.ndimage import label, binary_opening, binary_closing
    from scipy.ndimage import generate_binary_structure

    struct = generate_binary_structure(2, 1)
    bw = binary == 0  # True = black pixels
    bw = binary_closing(bw, structure=struct, iterations=1)
    bw = binary_opening(bw, structure=struct, iterations=1)

    # Remove small connected components (noise)
    labeled, n = label(bw, structure=struct)
    min_pixels = 8  # components smaller than this are noise
    for i in range(1, n + 1):
        if np.sum(labeled == i) < min_pixels:
            bw[labeled == i] = False

    result = np.where(bw, 0, 255).astype(np.uint8)
    out = Image.fromarray(result)
    out.save(output_path)
    print(f"Saved: {output_path} ({out.size[0]}x{out.size[1]})")


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "qr_noisy.jpg"
    out = sys.argv[2] if len(sys.argv) > 2 else "qr_clean.png"
    denoise_qr(inp, out)
