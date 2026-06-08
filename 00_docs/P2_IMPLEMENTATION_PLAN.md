# P2 MLOps 实施计划与进度跟踪

> **文档定位**: P2 阶段的详细实施计划、任务分解和进度跟踪
> **对应方案**: [`v2/04_plan_p2_v2.md`](./v2/04_plan_p2_v2.md)
> **更新时间**: 2026-06-08

---

## P2 目标概览

构建完整的 MLOps 闭环，包括：
- MLflow 深度集成（Tracking + Registry + 别名管理）
- Optuna 超参数优化（100+ trials）
- FastAPI 推理服务
- Docker 容器化（训练镜像 + 推理镜像）
- ModelScope + HuggingFace Hub 双渠道发布

**关键指标**: Champion 模型 QWK ≥ baseline + 0.05

---

## 实施阶段

### ✅ 阶段 1: MLflow 深度集成（2026-06-08 完成）

**目标**: 建立完整的实验追踪和模型注册体系

**已完成**:
- [x] `src/mlflow_utils/tracking.py` - 增强的实验追踪
  - `log_experiment()`: 统一实验记录接口
  - `log_cv_results()`: CV 结果批量记录
  - `log_confusion_matrix()`: 混淆矩阵可视化
  - `log_feature_importance()`: 特征重要性图
  - `log_training_curve()`: 训练曲线
  - `log_pr_curve()`: Precision-Recall 曲线

- [x] `src/mlflow_utils/registry.py` - Model Registry 管理
  - `init_registry()`: 初始化注册模型
  - `register_model()`: 注册模型到 Registry
  - `set_alias()`: 设置/更新别名（baseline/candidate/champion/demo）
  - `get_model_by_alias()`: 按别名加载模型
  - `promote_model()`: 模型晋升逻辑
  - `list_models_by_tag()`: 按标签筛选模型
  - `get_model_metadata()`: 获取模型元数据

- [x] `src/mlflow_utils/artifacts.py` - Artifact 管理
  - `save_model_summary()`: 模型架构摘要
  - `create_model_card()`: 自动生成 Model Card
  - `save_inference_script()`: 最小推理脚本
  - `save_input_example()`: 示例输入

- [x] `scripts/register_baseline.py` - Baseline 注册脚本
  - 从 P1 报告 CSV 自动选择最佳模型
  - 在 MLflow 中搜索对应 run
  - 注册到 Registry 并设置 `baseline` 别名
  - 保存 baseline 信息到 `models/baseline_info.json`

- [x] `src/experiments/run_p2_optuna.py` - Optuna 集成框架
  - 定义搜索空间（hidden_dims, dropout, lr, batch_size, weight_decay）
  - 集成 Optuna + MLflow（每个 trial 自动记录）
  - MedianPruner 早停
  - 5-fold CV 作为 objective
  - 自动将 best trial 注册为 `candidate`

**验证**:
```bash
# 语法检查
python -m compileall -q src/mlflow_utils/ scripts/register_baseline.py src/experiments/run_p2_optuna.py

# Dry-run 测试
python scripts/register_baseline.py --dry-run
# ✓ 成功选择 sklearn LR on feat_v1 (QWK=0.3651)
```

**交付物**:
- 3 个 MLflow 工具模块（tracking, registry, artifacts）
- 1 个 baseline 注册脚本
- 1 个 Optuna 优化脚本

---

### 🔄 阶段 2: Baseline 注册与验证（进行中）

**目标**: 将 P1 最佳模型注册为 baseline，建立对比基准

**待执行**:
- [ ] 确保 MLflow server 运行
- [ ] 执行 `python scripts/register_baseline.py`
- [ ] 验证 MLflow UI 中出现 `piu-risk` 模型
- [ ] 验证 `baseline` 别名可正常加载
- [ ] 测试 `get_model_by_alias('piu-risk', 'baseline')`

**预期产物**:
- MLflow Registry 中注册 `piu-risk` 模型
- `baseline` 别名指向 sklearn LR feat_v1 (QWK=0.3651)
- `models/baseline_info.json` 记录 baseline 元数据

**验证命令**:
```bash
# 启动 MLflow server（如未运行）
bash scripts/start_mlflow.sh

# 注册 baseline
python scripts/register_baseline.py

# 验证加载
python -c "
from src.mlflow_utils.registry import get_model_by_alias
model = get_model_by_alias('piu-risk', 'baseline')
print(f'Baseline model loaded successfully: {model}')
"
```

---

### ⏳ 阶段 3: Optuna 超参数优化（待启动）

**目标**: 对 PyTorch MLP 进行 100 trials 超参优化

**搜索空间**:
```python
{
    "hidden_dim_1": [64, 128, 256, 512],
    "hidden_dim_2": [32, 64, 128, 256],
    "dropout": [0.0, 0.1, 0.2, 0.3, 0.5],
    "lr": (1e-4, 1e-2),  # log-uniform
    "weight_decay": (1e-6, 1e-3),  # log-uniform
    "batch_size": [64, 128, 256, 512],
}
```

**执行计划**:
```bash
# 小规模测试（10 trials）
python -m src.experiments.run_p2_optuna --feature v2 --trials 10 --study-name test-optuna

# 完整运行（100 trials，预计 4-6 小时）
nohup python -m src.experiments.run_p2_optuna --feature v2 --trials 100 --study-name piu-mlp-v2 > logs/optuna_v2.log 2>&1 &

# 监控进度
tail -f logs/optuna_v2.log
```

**预期结果**:
- MLflow UI 中出现 100 个 nested runs
- Optuna study 完成，best trial QWK > baseline + 0.03
- `candidate` 别名自动更新到 best trial

**时间预算**: 4-6 小时（GPU）

---

### ⏳ 阶段 4: Champion 选定（待执行）

**目标**: 从 Optuna 结果中选定 champion 模型

**选定标准**:
- QWK ≥ baseline + 0.05
- 模型大小 < 50 MB
- 训练时间合理（< 20s per fold）

**执行步骤**:
```bash
# 查看 Optuna 结果
python -c "
import optuna
study = optuna.load_study('piu-mlp-v2', storage='sqlite:///optuna.db')
print(f'Best trial: {study.best_trial.number}')
print(f'Best QWK: {study.best_value:.4f}')
print(f'Best params: {study.best_trial.params}')
"

# 手动设置 champion（选定后）
python -c "
from src.mlflow_utils.registry import set_alias
set_alias('piu-risk', version=<best_version>, alias='champion')
"
```

**交付物**:
- Champion 模型锁定
- `champion` 别名设置
- Champion 模型元数据记录

---

### ⏳ 阶段 5: 推理服务（待开始）

**目标**: 构建 FastAPI 推理服务

**需要创建的文件**:
- `src/deployment/inference.py` - 推理逻辑
- `src/deployment/schemas.py` - Pydantic 数据模型
- `src/deployment/fastapi_app.py` - FastAPI 应用
- `src/deployment/sample_input.json` - 示例输入

**API 设计**:
```
GET  /health         - 健康检查
GET  /model_info     - 模型元信息
POST /predict        - 推理端点
```

**验证方式**:
```bash
# 启动服务
uvicorn src.deployment.fastapi_app:app --host 0.0.0.0 --port 8000

# 测试
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @src/deployment/sample_input.json
```

**时间预算**: 2-3 天

---

### ⏳ 阶段 6: Docker 容器化（待开始）

**目标**: 构建训练镜像和推理镜像

**需要创建的文件**:
- `docker/Dockerfile.train` - GPU 训练镜像
- `docker/Dockerfile.infer` - CPU 推理镜像
- `docker/requirements-infer.txt` - 精简依赖
- `docker/docker-compose.yml` - 本地测试编排

**验证方式**:
```bash
# 构建镜像
docker build -f docker/Dockerfile.train -t piu-train-gpu:v1 .
docker build -f docker/Dockerfile.infer -t piu-infer-cpu:v1 .

# 测试推理镜像
docker run -p 8000:8000 piu-infer-cpu:v1

# docker-compose 整体测试
cd docker && docker-compose up
```

**时间预算**: 2 天

---

### ⏳ 阶段 7: 双渠道模型发布（待开始）

**目标**: 将 champion 模型发布到 ModelScope 和 HuggingFace Hub

**需要创建的文件**:
- `src/deployment/model_card_template.md` - Model Card 模板
- `src/deployment/export_champion.py` - 模型导出脚本
- `src/deployment/publish_modelscope.py` - ModelScope 发布
- `src/deployment/publish_huggingface.py` - HuggingFace 发布

**发布流程**:
```bash
# 导出模型
python -m src.deployment.export_champion --output models/export/

# 发布到 ModelScope
python -m src.deployment.publish_modelscope --repo mlsys-2026s/piu-risk-classifier

# 发布到 HuggingFace
python -m src.deployment.publish_huggingface --repo mlsys-2026s/piu-risk-classifier
```

**交付物**:
- ModelScope 仓库 URL
- HuggingFace Hub 仓库 URL
- 双平台对比报告

**时间预算**: 2-3 天

---

## 总体进度

| 阶段 | 状态 | 完成度 | 预计时间 |
|------|------|--------|----------|
| 1. MLflow 深度集成 | ✅ 已完成 | 100% | 已完成 |
| 2. Baseline 注册 | 🔄 进行中 | 90% | 0.5 天 |
| 3. Optuna 优化 | ⏳ 待启动 | 0% | 1 天（框架）+ 4-6 小时（运行） |
| 4. Champion 选定 | ⏳ 待执行 | 0% | 0.5 天 |
| 5. 推理服务 | ⏳ 待开始 | 0% | 2-3 天 |
| 6. Docker 容器化 | ⏳ 待开始 | 0% | 2 天 |
| 7. 双渠道发布 | ⏳ 待开始 | 0% | 2-3 天 |

**总体进度**: ~15% (1/7 阶段完成)

**关键路径**: 1 → 2 → 3 → 4 → 5 → 6 → 7

**预计剩余时间**: 10-14 天

---

## 下一步行动

### 立即执行（今天）
1. ✅ 启动 MLflow server: `bash scripts/start_mlflow.sh`
2. ⏳ 注册 baseline: `python scripts/register_baseline.py`
3. ⏳ 验证 baseline 加载成功

### 短期目标（本周）
1. 运行 Optuna 小规模测试（10 trials）
2. 启动 Optuna 完整优化（100 trials，后台运行）
3. 开始设计 FastAPI 推理服务接口

### 中期目标（下周）
1. 选定 champion 模型
2. 完成 FastAPI 推理服务
3. 完成 Docker 容器化

### 长期目标（两周内）
1. 完成双渠道模型发布
2. 撰写 P2 报告
3. 准备最终答辩材料

---

## 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| Optuna 100 trials 超时 | 延期 | 降至 50 trials 或使用 3-fold CV |
| Champion QWK 提升不足 | 说服力下降 | 强调 MLOps 完整性，Ensemble 方案 |
| Docker 镜像过大 | 部署困难 | 多阶段构建，精简依赖 |
| 模型发布平台限制 | 发布受阻 | 优先 HuggingFace，降级 ModelScope 方案 |

---

**最后更新**: 2026-06-08
**下次更新**: Baseline 注册完成后或 Optuna 优化启动后
