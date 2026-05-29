#!/bin/bash

echo "=========================================="
echo "PIU 数据集下载进度监控"
echo "=========================================="
echo ""

TARGET_DIR="/home/er/桌面/MLsystem/data/raw"
ZIP_FILE="$TARGET_DIR/child-mind-institute-problematic-internet-use.zip"
EXPECTED_SIZE_GB=6.21

while true; do
    if [ -f "$ZIP_FILE" ]; then
        CURRENT_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
        CURRENT_SIZE_BYTES=$(stat -c%s "$ZIP_FILE")
        CURRENT_SIZE_GB=$(echo "scale=2; $CURRENT_SIZE_BYTES / 1024 / 1024 / 1024" | bc)
        PROGRESS=$(echo "scale=1; $CURRENT_SIZE_GB / $EXPECTED_SIZE_GB * 100" | bc)

        echo -ne "\r当前大小: $CURRENT_SIZE ($CURRENT_SIZE_GB GB / $EXPECTED_SIZE_GB GB) - 进度: ${PROGRESS}%   "

        # 检查是否下载完成
        if (( $(echo "$CURRENT_SIZE_GB >= $EXPECTED_SIZE_GB" | bc -l) )); then
            echo ""
            echo ""
            echo "✅ 下载完成!"
            break
        fi
    else
        echo -ne "\r等待下载开始...   "
    fi

    sleep 5
done

echo ""
echo "=========================================="
echo "下一步: 解压数据"
echo "  cd data/raw"
echo "  unzip child-mind-institute-problematic-internet-use.zip"
echo "=========================================="
