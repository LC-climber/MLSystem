#!/bin/bash
set -e

echo "=========================================="
echo "MLsystem Project - Data Acquisition"
echo "=========================================="
echo ""

# Check Kaggle credentials
if [ ! -f ~/.kaggle/kaggle.json ]; then
    echo "❌ Kaggle credentials not found!"
    echo ""
    echo "Please follow these steps:"
    echo "1. Login to Kaggle: https://www.kaggle.com"
    echo "2. Go to Account → Create New API Token"
    echo "3. Download kaggle.json"
    echo "4. Place it at: ~/.kaggle/kaggle.json"
    echo "5. Run: chmod 600 ~/.kaggle/kaggle.json"
    echo ""
    exit 1
fi

chmod 600 ~/.kaggle/kaggle.json
echo "✅ Kaggle credentials found"
echo ""

# Check competition rules acceptance
echo "⚠️  IMPORTANT: You must accept competition rules first!"
echo "   Visit: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use/rules"
echo "   Click 'I Understand and Accept'"
echo ""
read -p "Have you accepted the rules? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please accept the rules first, then run this script again."
    exit 1
fi

# Download PIU dataset
echo "Downloading PIU dataset (this may take 10-30 minutes)..."
mkdir -p data/raw
cd data/raw

kaggle competitions download -c child-mind-institute-problematic-internet-use

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Download failed. Possible reasons:"
    echo "   1. Competition rules not accepted"
    echo "   2. Network connection issues"
    echo "   3. Kaggle API credentials invalid"
    echo ""
    echo "Fallback option: Manual download"
    echo "   1. Visit: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use/data"
    echo "   2. Download all files manually"
    echo "   3. Place in: data/raw/"
    exit 1
fi

echo "Extracting dataset..."
unzip -q child-mind-institute-problematic-internet-use.zip
rm child-mind-institute-problematic-internet-use.zip  # Save ~6 GiB
echo "✅ Dataset extracted (saved 6 GiB by removing zip)"
echo ""

# Verify integrity
echo "Verifying data integrity..."
if [ -f train.csv ] && [ -f test.csv ]; then
    md5sum train.csv test.csv > ../data_checksums.md5
    echo "✅ Data integrity checksums saved"
else
    echo "⚠️  Warning: Expected files not found"
    ls -lh
fi

cd ../..

# Initialize DVC (optional, for version control)
if command -v dvc &> /dev/null; then
    echo ""
    echo "Initializing DVC for data versioning..."
    dvc init 2>/dev/null || echo "DVC already initialized"
    dvc add data/raw
    echo "✅ DVC tracking configured"
    echo ""
    echo "To commit DVC changes:"
    echo "  git add data/raw.dvc .gitignore .dvc/config"
    echo "  git commit -m 'dvc: track raw PIU data'"
else
    echo ""
    echo "⚠️  DVC not found (optional). Install with: pip install dvc"
fi

echo ""
echo "=========================================="
echo "✅ Data acquisition complete!"
echo "=========================================="
echo ""
echo "Dataset location: data/raw/"
echo "Next steps:"
echo "  1. Run: bash scripts/check_disk.sh"
echo "  2. Run: bash scripts/start_mlflow.sh"
echo "  3. Begin development: src/config.py"
