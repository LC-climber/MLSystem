#!/bin/bash

PROJECT_DIR="/home/er/桌面/MLsystem"
AVAIL=$(df --output=avail "$PROJECT_DIR" | tail -1)
AVAIL_GB=$((AVAIL / 1024 / 1024))

echo "=========================================="
echo "MLsystem Project - Disk Space Check"
echo "=========================================="
echo "Project directory: $PROJECT_DIR"
echo "Available disk space: ${AVAIL_GB} GiB"
echo ""

if [ $AVAIL_GB -lt 10 ]; then
    echo "🚨 CRITICAL: Less than 10 GiB available!"
    echo "   Action: Trigger WISDM fallback immediately"
    echo "   See: 00_docs/v2/06_risk_and_eval_v2.md §6"
    exit 1
elif [ $AVAIL_GB -lt 20 ]; then
    echo "⚠️  WARNING: Less than 20 GiB available"
    echo "   Action: Monitor closely, consider cleanup"
    exit 0
elif [ $AVAIL_GB -lt 30 ]; then
    echo "⚠️  CAUTION: Less than 30 GiB available"
    echo "   Action: Normal monitoring"
    exit 0
else
    echo "✅ Disk space OK (${AVAIL_GB} GiB available)"
    exit 0
fi
