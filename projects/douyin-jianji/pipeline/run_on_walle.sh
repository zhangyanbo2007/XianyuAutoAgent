#!/bin/bash
# 抖音视频生成 - 一键运行脚本（在walle上执行）
# 使用方法: bash run_on_walle.sh

set -e

echo "=========================================="
echo "  抖音视频生成 Pipeline v2"
echo "=========================================="

# 配置
WORK_DIR="/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/projects/douyin-jianji/pipeline"
VENV_DIR="$WORK_DIR/.venv"
DEMAND_DIR="$WORK_DIR/../demand"

# 检查Python
echo "[1/5] 检查Python环境..."
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11未安装"
    exit 1
fi
echo "✅ Python 3.11已安装"

# 创建虚拟环境
echo "[2/5] 创建虚拟环境..."
if [ ! -d "$VENV_DIR" ]; then
    cd "$WORK_DIR"
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
    source "$VENV_DIR/bin/activate"
fi

# 检查环境变量
echo "[3/5] 检查环境变量..."
if [ -z "$MIMO_API_KEY" ]; then
    echo "⚠️  MIMO_API_KEY未设置，将使用默认Key"
    export MIMO_API_KEY="tp-c1kaznnjsvndkjgih8no34aj4530rk5u9ay61pma0eh3qjhb"
fi

# 运行Pipeline（批量处理所有需求）
echo "[4/5] 运行视频生成Pipeline..."
cd "$WORK_DIR"

# 处理所有Excel文件
python pipeline.py "$DEMAND_DIR/douyinwenanjiaoben.xlsx" "$DEMAND_DIR/618.xlsx" --batch

# 检查输出
echo "[5/5] 检查输出文件..."
OUTPUT_DIR="$WORK_DIR/output"
if [ -d "$OUTPUT_DIR" ]; then
    echo "✅ 视频已生成:"
    find "$OUTPUT_DIR" -name "*.mp4" -exec ls -lh {} \;
else
    echo "❌ 视频生成失败"
    exit 1
fi

# 完成
echo "=========================================="
echo "  所有视频生成完成!"
echo "=========================================="
