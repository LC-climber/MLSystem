# P2 阶段 1 完成总结与下一步行动

**日期**: 2026-06-08
**阶段**: P2 MLOps - 阶段 1 (MLflow 深度集成)

---

## ✅ 已完成工作

### 1. MLflow 工具包开发

已创建完整的 MLflow 工具包，位于 `src/mlflow_utils/`:

**tracking.py** - 增强的实验追踪
- ✅ `log_experiment()` - 统一实验记录接口
- ✅ `log_cv_results()` - CV 结果批量记录
- ✅ `log_confusion_matrix()` - 混淆矩阵可视化
- ✅ `log_feature_importance()` - 特征重要性图
- ✅ `log_training_curve()` - 训练曲线
- ✅ `log_pr_curve()` - Precision-Recall 曲线

**registry.py** - Model Registry 管理
- ✅ `init_registry()` - 初始化注册模型
- ✅ `register_model()` - 注册模型到 Registry
- ✅ `set_alias()` - 设置/更新别名（baseline/candidate/champion/demo）
- ✅ `get_model_by_alias()` - 按别名加载模型
- ✅ `promote_model()` - 模型晋升逻辑
- ✅ `list_models_by_tag()` - 按标签筛选模型
- ✅ `get_model_metadata()` - 获取模型元数据

**artifacts.py** - Artifact 管理
- ✅ `save_model_summary()` - 模型架构摘要
- ✅ `create_model_card()` - 自动生成 Model Card
- ✅ `save_inference_script()` - 最小推理脚本
- ✅ `save_input_example()` - 示例输入

### 2. Baseline 注册脚本

**scripts/register_baseline.py**
- ✅ 从 P1 报告 CSV 自动选择最佳模型（sklearn LR on feat_v1, QWK=0.3651）
- ✅ Dry-run 模式验证通过
- ⚠️  实际注册受阻：P1 runs 未保存模型 artifact

### 3. Optuna 优化框架

**src/experiments/run_p2_optuna.py**
- ✅ 完整的超参数搜索框架
- ✅ 搜索空间定义（hidden_dims, dropout, lr, batch_size, weight_decay）
- ✅ 与 MLflow 深度集成（每个 trial 自动记录）
- ✅ MedianPruner 早停支持
- ✅ 5-fold CV 作为优化目标

### 4. 文档更新

- ✅ `00_docs/PROJECT_LOG.md` - 新增 2026-06-08 条目
- ✅ `00_docs/P2_IMPLEMENTATION_PLAN.md` - 完整的 7 阶段实施计划
- ✅ `00_docs/PROGRESS.md` - 更新当前状态为 P2 阶段

### 5. 代码质量

- ✅ 所有新增 Python 文件语法检查通过
- ✅ MLflow server 成功启动（http://localhost:5000）
- ✅ 确认现有 P1 实验数据（piu-p1-systemwise，多个 finished runs）

---

## 🔍 发现的问题

### 问题 1: P1 runs 未保存模型 artifact

**现象**: 
- MLflow 中有 P1 的 runs（参数、指标已记录）
- 但没有保存模型 artifact（`mlruns_artifacts/` 为空）
- 导致无法直接注册为 baseline

**原因**:
P1 实验主要关注系统对比，使用的是简单的 `mlflow.log_param/log_metric`，没有使用 `mlflow.sklearn.log_model()` 等保存模型。

**影响**:
无法从 P1 runs 直接注册 baseline 到 Model Registry

**解决方案**（3 个选项）:

**选项 A: 重跑一个 P1 最佳模型并保存** ⭐ **推荐**
```bash
# 使用增强的 tracking 重跑 sklearn LR on feat_v1
python -m src.experiments.run_p1_systemwise --feature v1 --system sklearn --algo lr --save-model
```

**选项 B: 直接训练 P2 模型作为起点**
- 跳过 baseline 注册
- 直接用 Optuna 优化，第一个较好的模型设为 baseline
- 适合：想快速推进到 P2 核心任务

**选项 C: Mock baseline（仅用于流程验证）**
- 训练一个简单模型并保存，仅作为 Registry 流程测试
- 不用于实际对比

---

## 📋 下一步行动计划

### 立即执行（今天）

#### 方案 1: 使用选项 A（完整流程）

1. **修改 `run_p1_systemwise.py` 支持模型保存**
   ```python
   # 在 _log_mlflow() 中添加
   if save_model:
       mlflow.sklearn.log_model(model, "model")
   ```

2. **重跑 sklearn LR feat_v1 并保存模型**
   ```bash
   python -m src.experiments.run_p1_systemwise --feature v1 --folds 2 --save-model
   ```

3. **注册为 baseline**
   ```bash
   python scripts/register_baseline.py
   ```

4. **验证 baseline 可用**
   ```bash
   python -c "from src.mlflow_utils.registry import get_model_by_alias; model = get_model_by_alias('piu-risk', 'baseline'); print('✓ Baseline loaded')"
   ```

#### 方案 2: 使用选项 B（快速推进）

1. **直接启动 Optuna 小规模测试**
   ```bash
   python -m src.experiments.run_p2_optuna --feature v2 --trials 10 --study-name test-optuna
   ```

2. **从 Optuna 结果中选择第一个较好模型作为 baseline**
   ```bash
   # 在 10 trials 完成后手动设置
   python -c "from src.mlflow_utils.registry import set_alias; set_alias('piu-risk', version=<best_version>, alias='baseline')"
   ```

3. **继续 Optuna 完整优化**
   ```bash
   nohup python -m src.experiments.run_p2_optuna --feature v2 --trials 100 --study-name piu-mlp-v2 > logs/optuna_v2.log 2>&1 &
   ```

### 短期目标（本周）

- [ ] 完成 baseline 注册（通过方案 1 或方案 2）
- [ ] 完成 Optuna 10 trials 测试
- [ ] 启动 Optuna 100 trials 完整优化（后台运行）
- [ ] 开始设计 FastAPI 推理服务接口

### 中期目标（下周）

- [ ] 选定 champion 模型（从 Optuna 最佳结果）
- [ ] 完成 FastAPI 推理服务实现
- [ ] 完成 Docker 容器化

---

## 🎯 推荐执行路径

我建议采用**方案 2（选项 B）**，理由：

1. **时间效率高**: 不需要修改 P1 代码，直接进入 P2 核心任务
2. **P2 原生**: baseline 来自 P2 框架，更能体现 MLOps 改进
3. **流程完整**: 10 trials → baseline，100 trials → candidate/champion，体现迭代优化
4. **答辩叙事**: "P2 从零开始构建 MLOps 流程，通过 Optuna 找到最佳模型"

### 具体执行步骤（方案 2）

```bash
# Step 1: 确保环境就绪
conda activate openpi_311
curl http://localhost:5000/health  # 确认 MLflow 运行中

# Step 2: 创建日志目录
mkdir -p logs

# Step 3: 小规模 Optuna 测试（10 trials，约 30-60 分钟）
python -m src.experiments.run_p2_optuna \
  --feature v2 \
  --trials 10 \
  --study-name test-optuna \
  --folds 3  # 用 3-fold 加速测试

# Step 4: 查看结果并设置 baseline
# （在 10 trials 完成后执行）
python -c "
import optuna
study = optuna.load_study('test-optuna', storage='sqlite:///optuna.db')
print(f'Best trial: {study.best_trial.number}')
print(f'Best QWK: {study.best_value:.4f}')
print(f'Best params: {study.best_trial.params}')
"

# Step 5: 手动将 best trial 的 MLflow run 注册为 baseline
# （需要从 MLflow UI 或命令行找到对应 run_id）
python -c "
from src.mlflow_utils.registry import register_model
register_model(
    run_id='<best_run_id>',  # 从 MLflow UI 复制
    model_name='piu-risk',
    alias='baseline',
    description='Initial baseline from 10-trial Optuna test'
)
"

# Step 6: 启动完整 Optuna 优化（100 trials，后台运行）
nohup python -m src.experiments.run_p2_optuna \
  --feature v2 \
  --trials 100 \
  --study-name piu-mlp-v2 \
  --folds 5 \
  > logs/optuna_v2_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Step 7: 监控进度
tail -f logs/optuna_v2_*.log
```

---

## 📊 当前项目状态

**P1**: ✅ 完成（已汇报）
**P2 阶段 1**: ✅ 90% 完成（工具包已就绪，baseline 注册待执行）
**P2 阶段 2-3**: ⏳ 待启动（Optuna 优化）
**P2 阶段 4-7**: ⏳ 待开始（推理服务、容器化、发布）

**总体进度**: ~15%
**预计完成时间**: 10-14 天

---

## 📝 记录更新

- [x] PROJECT_LOG.md 新增 2026-06-08 条目
- [x] P2_IMPLEMENTATION_PLAN.md 创建
- [x] PROGRESS.md 更新状态
- [ ] 待补充：baseline 注册完成后的验证记录
- [ ] 待补充：Optuna 测试结果

---

**建议下一步**: 执行方案 2 的 Step 3（小规模 Optuna 测试），验证完整流程后启动 100 trials 优化。
