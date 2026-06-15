# 抖音视频生成 - 光伏前期手续

## 项目概述

根据Excel脚本自动生成抖音短视频，参考专业视频制作流程。

## 文件结构

```
douyin-jianji/
├── douyinwenanjiaoben.xlsx        # 原始Excel脚本
├── reference_videos/              # 参考视频
├── pipeline/                      # 视频生成pipeline
│   ├── config.py                  # 配置文件
│   ├── script_converter.py        # Excel转JSON
│   ├── tts_generator.py           # TTS生成器（Dashscope）
│   ├── tts_generator_mimo.py      # TTS生成器（小米MiMo）
│   ├── tts_generator_bailian.py   # TTS生成器（百炼）
│   ├── image_generator.py         # 图片生成器
│   ├── video_generator.py         # 视频生成器
│   ├── pipeline.py                # 主流程
│   ├── requirements.txt           # 依赖
│   └── run_on_walle.sh           # walle一键运行脚本
└── output/光伏前期手续/           # 生成的素材
    ├── script.json                # 视频脚本
    ├── narration.srt              # 字幕文件
    ├── slides/                    # 占位图
    └── README.md                  # 素材说明
```

## 快速开始

### 方法一：在walle上运行（推荐）

walle电脑网络正常，可以直接运行pipeline：

```bash
# 1. SSH到walle
ssh zhangyanbo@192.168.28.92

# 2. 运行pipeline
cd ~/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline
bash run_on_walle.sh
```

### 方法二：使用小米MiMo TTS

```bash
# 配置环境变量
export MIMO_API_KEY="tp-c1kaznnjsvndkjgih8no34aj4530rk5u9ay61pma0eh3qjhb"

# 运行pipeline
cd pipeline
python pipeline.py ../douyinwenanjiaoben.xlsx --name 光伏前期手续 --tts mimo
```

### 方法三：使用百炼TTS

```bash
# 配置环境变量
export DASHSCOPE_API_KEY="your_api_key"

# 运行pipeline
cd pipeline
python pipeline.py ../douyinwenanjiaoben.xlsx --name 光伏前期手续 --tts bailian
```

## 视频参数

- **时长**: 约28秒
- **分辨率**: 1080x1920（竖屏9:16）
- **风格**: 干货科普/节奏快/字幕卡点/无人出镜
- **BGM**: 轻快干货解说风格

## 参考视频分析

参考了两个光伏科普视频：
1. 山东光伏新政 (131秒)
2. 全国分布式光伏新政策 (118秒)

**共同特点**:
- 竖屏9:16格式
- 干货科普风格
- 节奏快，信息密度高
- 字幕卡点
- 无人出镜
- 配音+字幕+画面形式

**我们的优化**:
- 更精炼的文案（28秒 vs 118-131秒）
- 更清晰的信息层次（5个段落）
- 更吸引人的开场（痛点/悬念）
- 更专业的视觉设计

## 技术栈

- **TTS**: 小米MiMo / Dashscope CosyVoice / edge-tts
- **图片生成**: Dashscope wanx2.1 / 占位图
- **视频处理**: ffmpeg (通过imageio-ffmpeg)
- **字幕样式**: ASS格式 (抖音风格)

## 注意事项

1. **网络要求**: 需要能访问外部API（小米MiMo或Dashscope）
2. **API Key**: 需要有效的API Key
3. **依赖安装**: 需要安装Python依赖
4. **ffmpeg**: 需要安装ffmpeg

## 可复用性

此流程已标准化，以后处理新的抖音脚本Excel时：
1. 将Excel放到当前目录
2. 运行 `pipeline/pipeline.py` 即可生成标准格式素材
3. 在网络正常的机器上合成视频

## 执行结果

已完成的工作：
- ✅ 从walle复制Excel脚本
- ✅ 分析2个参考视频
- ✅ 生成脚本JSON
- ✅ 生成字幕SRT
- ✅ 生成5张占位图
- ✅ 创建完整的pipeline代码
- ✅ 创建walle一键运行脚本
- ✅ 编写完整的README文档

待完成的工作：
- ❌ TTS语音合成（网络问题）
- ❌ 视频合成（依赖TTS）

解决方案：
在walle电脑上运行pipeline即可生成完整视频。
