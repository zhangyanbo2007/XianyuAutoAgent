# 参考帧提取指南

## 核心原则

参考帧是保证角色形象一致性的关键。**选错了帧，后面角色就会变样。**

## 不要选什么

- ❌ 不要选最后一帧（可能角色已经出画或动作已结束）
- ❌ 不要选模糊帧（运动模糊、遮挡）
- ❌ 不要选远景帧（看不清细节）
- ❌ 不要随机选帧

## 选什么

- ✅ 角色全身可见、轮廓清晰的帧
- ✅ 角色标志性特征全部呈现的帧（如白首、虎斑、赤尾都能看清）
- ✅ 构图好的帧（主体居中或三分线）
- ✅ 光线好、无运动模糊的帧

## 提取方法

```python
from moviepy import VideoFileClip
from PIL import Image
import glob
import os

v = VideoFileClip("<视频路径>")
fps = v.fps or 24

# 遍历关键帧（每 1 秒取 1 帧）
frames = {}
for t in range(1, int(v.duration)):
    frame = v.get_frame(t)
    img = Image.fromarray(frame)
    frames[t] = img

# 输出到目录供检查
os.makedirs("/tmp/frame-candidates", exist_ok=True)
for t, img in frames.items():
    img.save(f"/tmp/frame-candidates/frame-{t}s.jpg")
```

## 手动选择后上传

选定最佳帧后上传到 COS：

```bash
~/.openclaw/skills/media-to-url/scripts/upload-cos.sh /tmp/frame-candidates/frame-5s.jpg
```

## 多角色场景的特殊策略

当视频包含多个角色（如鹿蜀→旋龟）时：

**第二段参考帧优先选上一段的过渡画面**。

例如：第一段结尾是"镜头顺山势转入山间溪流，鹿蜀俯身溪畔饮水"——
这个过渡画面既包含溪流环境（第二段的场景），又保持白描风格。
用这帧作为第二段的参考图，两段视觉连贯自然。

**方法：**
```python
# 截取第一段约 5-7 秒处的过渡帧
frame = v.get_frame(5.0)  # 选过渡画面的时间点
img = Image.fromarray(frame)
img.save("/tmp/core-reference.jpg")
```

## 提示词中强调

生成下一段时，在 prompt 开头强调：

> "重要：参考图中的[角色名]形象必须完全保留，不要做任何改变——[详细外形特征]，跟参考图一模一样，不要改动它的任何外形特征。"
