# MLsystem - PIU Risk Classification MLOps Project

**最后更新**: 2026-06-11
**当前状态**: P1 完成；P2 本地可复现 MLOps 流程完成。

## 项目概览

本项目面向 Kaggle Child Mind Institute PIU 风险分类任务，包含两个阶段：

- P1: 多系统对比，已生成可复现实验表格、图表和中期汇报材料。
- P2: MLOps 实践，已完成本地 MLflow/Optuna/Registry/FastAPI-compatible model/artifact/report/visualization 证据链。

## P2 关键结果

- Formal study: `p2-formal-mlops-20260612`
- Formal Optuna search: 10 local trials, 5-fold CV
- Baseline: `baseline_logreg_v1`, QWK `0.3651`
- Champion: `candidate_logreg_v1`, QWK `0.3672`
- Registry aliases: `baseline -> v7`, `candidate -> v8`, `champion -> v9`
- Champion URI: `models:/piu-risk@champion`

主要报告和图表：

- [P2 final report](/home/er/桌面/MLsystem/reports/P2/p2_final_report.md)
- [P2 audit summary](/home/er/桌面/MLsystem/reports/P2/p2_summary_report.md)
- [metric comparison](/home/er/桌面/MLsystem/reports/P2/figures/p2_metric_comparison.png)
- [Optuna trace](/home/er/桌面/MLsystem/reports/P2/figures/p2_optuna_trace.png)
- [champion confusion matrix](/home/er/桌面/MLsystem/reports/P2/figures/p2_champion_confusion_matrix.png)
- [MLflow run status](/home/er/桌面/MLsystem/reports/P2/figures/p2_mlflow_run_status.png)

## 常用命令

```bash
# P1 多系统对比
python -m src.experiments.run_p1_systemwise

# P2 完整管道
python -m src.experiments.run_p2_full_pipeline \
  --trials 10 --folds 5 --study-name p2-formal-mlops-20260612

# 导出 P2 审计报告
python scripts/export_p2_reports.py

# 加载 champion 验证
python - <<'PY'
import mlflow, pandas as pd
from src.config import MLFLOW_TRACKING_URI
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
model = mlflow.pyfunc.load_model("models:/piu-risk@champion")
print(model.predict(pd.DataFrame([{"age": 12.5, "sex": 1.0, "bmi": 18.5}])))
PY
```

## 项目结构

```text
MLsystem/
├── src/                    # 数据、模型、实验、部署和 MLOps 代码
├── scripts/                # 报告导出和工具脚本
├── tests/                  # 测试代码
├── docker/                 # Docker 配置
├── reports/P1/             # P1 静态报告产物
├── reports/P2/             # P2 结果、图表、模型副本和审计导出
├── mlruns.db               # MLflow SQLite backend
├── mlruns_artifacts/       # MLflow artifacts
└── 00_docs/                # 计划、过程记录和归档文档
```

## 解释口径

P2 的主要价值是完成 MLOps 闭环，而不是大幅提升模型性能。Champion 相比 baseline 的 QWK 提升为 `+0.0022`，应如实汇报为小幅调参收益。
