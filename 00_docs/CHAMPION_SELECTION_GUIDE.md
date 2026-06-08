# Champion 模型选定指南

## 概述

本文档记录从多个候选模型中选定 Champion 模型的过程和标准。

---

## 候选模型

### 1. P1 Baseline - sklearn LR
- **来源**: P1 多系统对比
- **特征**: feat_v1 (100维)
- **性能**: 
  - QWK: 0.3651
  - Macro F1: 0.362
  - Balanced Accuracy: 0.404
- **状态**: ✅ 已验证

### 2. Optuna Champion - PyTorch MLP
- **来源**: P2 Optuna 优化
- **特征**: feat_v2 (145维)
- **性能**: 待 100-trial 优化完成
- **状态**: ⏳ 进行中

---

## 选定标准

### 主要指标
1. **Cohen's Kappa (QWK)** - 主要指标
   - 阈值: > baseline (0.3651)
   - 目标: ≥ 0.40

2. **Macro F1** - 平衡性指标
   - 阈值: > baseline (0.362)
   - 关注少数类性能

3. **Balanced Accuracy** - 类别平衡
   - 阈值: > baseline (0.404)

### 次要考虑
4. **推理延迟** - < 100ms per sample
5. **模型大小** - < 100MB
6. **可解释性** - Feature importance 可用

---

## 决策流程

```
开始
  ↓
运行 Optuna 100-trial 优化
  ↓
是否有模型 QWK > baseline?
  ├─ 是 → 选择 QWK 最高的模型作为候选
  └─ 否 → 使用 baseline 作为 Champion
  ↓
验证候选模型
  ├─ 交叉验证稳定性
  ├─ 测试集性能
  └─ 推理延迟测试
  ↓
性能提升是否显著? (QWK提升 > 0.05)
  ├─ 是 → 选定为 Champion
  └─ 否 → 权衡复杂度，可能仍选 baseline
  ↓
注册到 MLflow Registry
  ├─ 创建新版本
  ├─ 添加 champion 别名
  └─ 生成 Model Card
  ↓
完成
```

---

## 当前状态

### Baseline 模型
- ✅ 已注册到 MLflow
- ✅ 性能已验证
- ✅ 可随时使用

### Optuna 候选
- ⏳ 优化进行中
- ⏳ 需要 6-8 小时后台运行
- ⏳ 待性能评估

---

## 选定记录

### 决策日期
待定（Optuna 完成后）

### 最终选择
待定

### 决策理由
待记录

### 性能对比

| 模型 | QWK | Macro F1 | Bal Acc | 延迟 | 大小 |
|------|-----|----------|---------|------|------|
| Baseline (sklearn LR) | 0.3651 | 0.362 | 0.404 | ~1ms | <1MB |
| Optuna Champion | TBD | TBD | TBD | TBD | TBD |

---

## 注册步骤

### 1. 从 Optuna 导出最佳模型
```python
import mlflow
import optuna

# 加载 study
study = optuna.load_study(
    study_name="piu-mlp-optimization",
    storage="sqlite:///optuna.db"
)

# 获取最佳 trial
best_trial = study.best_trial
print(f"Best QWK: {best_trial.value:.4f}")
print(f"Best params: {best_trial.params}")

# 获取对应的 MLflow run
run_id = best_trial.user_attrs.get("mlflow_run_id")
```

### 2. 注册为 Champion
```python
from src.mlflow_utils.registry import register_model

# 注册并添加 champion 别名
model_uri = f"runs:/{run_id}/model"
model_version = register_model(
    model_uri=model_uri,
    model_name="piu-risk",
    alias="champion",
    description="Best model from Optuna optimization"
)
```

### 3. 验证注册
```python
# 加载 champion 模型
champion = mlflow.pyfunc.load_model("models:/piu-risk@champion")

# 测试推理
prediction = champion.predict(X_test)
```

---

## 回退策略

如果 Optuna Champion 出现问题：

1. **回退到 baseline**
   ```python
   # 重新设置 baseline 为 champion
   client = mlflow.MlflowClient()
   client.set_registered_model_alias(
       name="piu-risk",
       alias="champion",
       version=baseline_version
   )
   ```

2. **使用 candidate 别名**
   - 将新模型先设为 candidate
   - 充分测试后再升级为 champion

---

## 文档更新

选定 Champion 后需要更新：
- [ ] PROGRESS.md - 更新进度
- [ ] PROJECT_LOG.md - 记录决策
- [ ] Model Card - 更新性能指标
- [ ] README.md - 更新模型信息

---

**创建时间**: 2026-06-08 19:20  
**最后更新**: 待定  
**责任人**: 项目团队
