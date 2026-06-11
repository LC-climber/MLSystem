# P2 MLOps 实践总结报告

**生成时间**: 2026-06-11

## 数据来源

- ✅ Optuna DB: `src/optuna.db`
  - Trials 数量: 18
  - 完成 Trials: 7
  - 最佳 QWK: 0.0000 ⚠️
- ⚠️ MLflow: `mlruns/` (目录为空，未实际运行实验追踪)

## 实际完成状态

### 已实现的代码（100%）
- ✅ MLflow 工具包代码（tracking, registry, model_card, visualizations）
- ✅ Optuna 优化框架代码
- ✅ FastAPI 推理服务（5个端点）
- ✅ Docker 容器化配置（推理+训练镜像）
- ✅ 模型发布指南文档（双渠道）

### 已执行的实验
- ✅ Optuna 超参数优化（18 trials，7 完成）
  - ⚠️ 所有完成的 trials QWK=0，需检查目标函数
- ❌ MLflow 实验追踪（未实际记录数据）
- ❌ 模型注册到 MLflow Registry（未执行）
- ❌ MLflow 可视化生成（未执行）

## 发现的问题

1. **Optuna QWK=0**: 所有完成的 trials 返回值都是 0，可能原因：
   - 目标函数实现有误
   - 模型训练失败但未抛出异常
   - 评估指标计算错误

2. **MLflow 未使用**: mlruns 目录为空，说明：
   - Optuna 脚本可能没有正确集成 MLflow logging
   - 或者实验运行时没有启用 MLflow 追踪

## 生成的报告文件

- `p2_optuna_trials.csv` - 完整的 Optuna trials 数据（从 DB 导出）
- `p2_optuna_best_trials.md` - Top 5 最佳 trials（虽然都是 0）
- `p2_summary_report.md` - 本报告

## 后续建议

1. **修复 Optuna 目标函数**
   - 检查 `src/experiments/run_p2_optuna.py` 的 objective 函数
   - 确认 QWK 计算和返回值正确

2. **启用 MLflow 追踪**
   - 在 Optuna objective 中添加 `mlflow.log_params()` 和 `mlflow.log_metrics()`
   - 或使用 MLflow callback: `mlflow.set_tracking_uri()` + `mlflow.start_run()`

3. **重新运行完整实验**
   - 修复后重新运行 Optuna 优化
   - 确保 MLflow 正确记录每个 trial

## 查看方式

```bash
# 查看 Optuna 数据库
sqlite3 src/optuna.db "SELECT * FROM trials;"

# 如果 MLflow 有数据，启动 UI
mlflow ui
```
