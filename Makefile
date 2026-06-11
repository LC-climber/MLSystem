.PHONY: help setup data features train evaluate clean test lint format

# Default target
help:
	@echo "MLsystem Project - Makefile Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup & Environment:"
	@echo "  make setup          - Create conda environments"
	@echo "  make check-disk     - Check available disk space"
	@echo ""
	@echo "Data Pipeline:"
	@echo "  make data           - Download PIU dataset from Kaggle"
	@echo "  make features       - Generate feature versions (v1/v2/v3)"
	@echo ""
	@echo "Training & Evaluation:"
	@echo "  make train-p1       - Run P1 system-wise comparison"
	@echo "  make train-p2       - Run P2 MLOps pipeline"
	@echo "  make evaluate       - Evaluate trained models"
	@echo ""
	@echo "MLflow:"
	@echo "  make mlflow-start   - Start MLflow tracking server"
	@echo "  make mlflow-ui      - Open MLflow UI in browser"
	@echo ""
	@echo "Development:"
	@echo "  make test           - Run unit tests"
	@echo "  make lint           - Run code linting"
	@echo "  make format         - Format code with black"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove generated files"
	@echo "  make clean-all      - Remove all artifacts including data"

# Setup
setup:
	@echo "Creating conda environments..."
	bash scripts/setup_envs.sh

check-disk:
	@bash scripts/check_disk.sh

# Data pipeline
data:
	@echo "Downloading PIU dataset..."
	bash scripts/fetch_data.sh

features:
	@echo "Generating features (requires data to be downloaded first)..."
	conda run -n mlsys_cpu python -m src.data.feature_engineering

# Training
train-p1:
	@echo "Running P1 system-wise comparison..."
	conda run -n mlsys_cpu python -m src.experiments.run_p1_systemwise

train-p2:
	@echo "Running P2 MLOps pipeline..."
	python -m src.experiments.run_p2_full_pipeline --trials 10 --folds 5 --study-name p2-formal-mlops-20260612

# Evaluation
evaluate:
	@echo "Evaluating models..."
	conda run -n mlsys_cpu python -m src.scripts.evaluate

# MLflow
mlflow-start:
	@echo "Starting MLflow server..."
	bash scripts/start_mlflow.sh

mlflow-ui:
	@echo "Opening MLflow UI..."
	xdg-open http://localhost:5000 || open http://localhost:5000

# Development
test:
	@echo "Running tests..."
	conda run -n mlsys_cpu pytest tests/ -v

lint:
	@echo "Running linting..."
	conda run -n mlsys_cpu flake8 src/ tests/

format:
	@echo "Formatting code..."
	conda run -n mlsys_cpu black src/ tests/

# Cleanup
clean:
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf data/interim/*
	rm -rf data/processed/*

clean-all: clean
	@echo "Removing all artifacts including data..."
	rm -rf data/raw/*
	rm -rf mlruns_artifacts/*
	rm -rf models/*
	rm -f mlruns.db
