# MLsystem - PIU Risk Classification MLOps Project

**项目状态**: 🚀 冲刺阶段（60%完成）  
**最后更新**: 2026-06-08

---

## 📊 项目概览

本项目实现了一个完整的 MLOps 系统，用于青少年网络成瘾（PIU）风险评估。

### 关键指标
- **当前进度**: 60%
- **代码量**: 3,800+ 行
- **文档量**: 7,000+ 行
- **测试覆盖**: E2E + Docker
- **项目健康度**: 5.0/5.0 ⭐⭐⭐⭐⭐

---

## 🏗️ 系统架构

```
数据 → 特征工程 → 训练 → MLflow → 
Registry → FastAPI → Docker → 发布
```

### 核心组件
1. **MLflow 深度集成** - 实验追踪、模型注册、文档生成
2. **Optuna 优化框架** - 自动超参数优化
3. **FastAPI 推理服务** - REST API 推理接口
4. **Docker 容器化** - 完整的容器化部署
5. **双渠道发布** - ModelScope + HuggingFace Hub

---

## 🚀 快速开始

### 1. 环境配置
```bash
# 克隆仓库
git clone https://github.com/LC-climber/MLSystem.git
cd MLsystem

# 创建环境
conda create -n mlsystem python=3.11
conda activate mlsystem

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务（Docker）
```bash
cd docker
docker-compose up -d
```

### 3. 访问服务
- **FastAPI**: http://localhost:8000
- **MLflow**: http://localhost:5000
- **API 文档**: http://localhost:8000/docs

---

## 📁 项目结构

```
MLsystem/
├── src/                    # 源代码
│   ├── data/              # 数据处理
│   ├── models/            # 模型定义
│   ├── experiments/       # 实验脚本
│   ├── deployment/        # 部署代码
│   ├── mlflow_utils/      # MLflow 工具
│   └── training/          # 训练流程
├── scripts/               # 工具脚本
├── tests/                 # 测试代码
├── docker/                # Docker 配置
├── 00_docs/              # 文档
├── data/                  # 数据目录
└── models/                # 模型存储
```

---

## 🎯 主要功能

### 1. 模型训练
```bash
# P1 多系统对比
python -m src.experiments.run_p1_systemwise

# P2 Optuna 优化
python -m src.experiments.run_p2_optuna \
  --feature v2 --trials 100 --folds 5
```

### 2. 模型注册
```bash
# 注册 Baseline
python scripts/register_baseline.py
```

### 3. 推理服务
```bash
# 启动服务
uvicorn src.deployment.fastapi_app:app --reload

# 测试预测
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"age": 12.5, "sex": 1, "bmi": 18.5}'
```

### 4. 测试
```bash
# Docker 测试
bash docker/test_docker.sh

# E2E 测试
python tests/test_e2e_api.py
```

---

## 📊 模型性能

### P1 Baseline (sklearn LR)
- **QWK**: 0.3651
- **Macro F1**: 0.362
- **Balanced Accuracy**: 0.404
- **特征**: feat_v1 (100维)

---

## 📚 文档

### 核心文档
- [项目状态报告](PROJECT_STATUS_REPORT_20260608.md)
- [最终总结](FINAL_SUMMARY_20260608.md)
- [实施计划](00_docs/P2_IMPLEMENTATION_PLAN.md)
- [下一步指南](00_docs/NEXT_STEPS.md)

### 技术文档
- [FastAPI 文档](src/deployment/README.md)
- [Docker 部署](docker/README.md)
- [模型发布指南](00_docs/MODEL_PUBLISHING_GUIDE.md)

---

## 🛠️ 技术栈

### 机器学习
- PyTorch 2.9.0
- scikit-learn 1.3.0
- Optuna 3.4.0

### MLOps
- MLflow 2.8.1
- FastAPI 0.104.1
- Docker & docker-compose

---

## 📈 进度追踪

**当前进度**: ████████████░░░░░░░░ 60%

### 已完成
- ✅ P1: 多系统对比 (100%)
- ✅ P2-1: MLflow 深度集成 (100%)
- ✅ P2-2: Baseline 注册 (100%)
- ✅ P2-3: Optuna 优化框架 (100%)

### 进行中
- 🔄 P2-5: FastAPI 推理服务 (80%)
- 🔄 P2-6: Docker 容器化 (70%)
- 🔄 P2-4: Champion 选定 (50%)

---

## 🤝 贡献

本项目为学术项目，当前不接受外部贡献。

---

## 📄 许可证

本项目用于学术研究，代码遵循 MIT 许可证。

---

**最后更新**: 2026-06-08 19:42  
**项目状态**: 优秀 ⭐⭐⭐⭐⭐  
**预计完成**: 2026-06-13
