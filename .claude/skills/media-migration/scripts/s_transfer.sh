#!/bin/bash
# s_transfer.sh - 跨机器媒体传输脚本
# 用法: ./s_transfer.sh <source> <target_user@target_host:target_path> [password]
#
# 示例:
#   ./s_transfer.sh /path/to/photos zhangyanbo@192.168.3.182:D:/PhotosAll/photos_from_hcu mypassword
#   ./s_transfer.sh /path/to/videos xiaowangzi@192.168.3.67:/home/.../VideosAll mypassword

set -e

SOURCE="$1"
TARGET="$2"
PASSWORD="$3"

if [ -z "$SOURCE" ] || [ -z "$TARGET" ]; then
    echo "Usage: $0 <source> <user@host:path> [password]"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/photos zhangyanbo@192.168.3.182:D:/PhotosAll/target_dir pass"
    echo "  $0 /path/to/videos xiaowangzi@192.168.3.67:/home/.../VideosAll pass"
    exit 1
fi

# 设置UTF-8编码
export LC_ALL=en_US.UTF-8

# SCP参数
SCP_OPTS="-o StrictHostKeyChecking=no -o ServerAliveInterval=10 -o ServerAliveCountMax=5 -r"

echo "=== Media Transfer ==="
echo "Source: $SOURCE"
echo "Target: $TARGET"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查源目录
if [ ! -d "$SOURCE" ]; then
    echo "Error: Source directory does not exist: $SOURCE"
    exit 1
fi

# 统计源文件
PHOTO_COUNT=$(find "$SOURCE" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.bmp" -o -iname "*.gif" -o -iname "*.webp" -o -iname "*.heic" \) 2>/dev/null | wc -l)
VIDEO_COUNT=$(find "$SOURCE" -type f \( -iname "*.mp4" -o -iname "*.avi" -o -iname "*.mkv" -o -iname "*.mov" -o -iname "*.wmv" \) 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$SOURCE" 2>/dev/null | cut -f1)

echo "Source stats:"
echo "  Photos: $PHOTO_COUNT"
echo "  Videos: $VIDEO_COUNT"
echo "  Total size: $TOTAL_SIZE"
echo ""

# 执行传输
echo "Starting transfer..."
if [ -n "$PASSWORD" ]; then
    sshpass -p "$PASSWORD" scp $SCP_OPTS "$SOURCE" "$TARGET"
else
    scp $SCP_OPTS "$SOURCE" "$TARGET"
fi

echo ""
echo "Transfer complete!"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
