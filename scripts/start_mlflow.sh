#!/bin/bash

echo "=========================================="
echo "MLsystem Project - MLflow Server"
echo "=========================================="
echo ""

# Get conda base path
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# Activate mlsys_cpu environment
conda activate mlsys_cpu

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Starting MLflow server..."
echo "  Backend: SQLite (mlruns.db)"
echo "  Artifacts: mlruns_artifacts/"
echo "  Host: 0.0.0.0"
echo "  Port: 5000"
echo ""
echo "Access UI at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

mlflow server \
  --backend-store-uri sqlite:///$PROJECT_ROOT/mlruns.db \
  --default-artifact-root $PROJECT_ROOT/mlruns_artifacts \
  --host 0.0.0.0 \
  --port 5000
