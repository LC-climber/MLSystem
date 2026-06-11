# MLsystem 项目完成总结

**更新日期**: 2026-06-11
**结论**: P1 已完成；P2 本地可复现 MLOps 流程已完成。

## 总体状态

| 阶段 | 状态 | 关键证据 |
| --- | --- | --- |
| P1 多系统对比 | 完成 | `reports/P1/` 中的 CSV、图表、PPT |
| P2 MLOps 实践 | 完成 | `reports/P2/p2_final_report.md`、MLflow Registry aliases、P2 图表 |

## P1 结果

- QWK: 0.3651
- Macro F1: 0.362
- Balanced Accuracy: 0.404
- 结论：Spark 适合大规模特征工程，不适合当前小表格训练和低延迟推理。

## P2 结果

- Formal Optuna study: `p2-formal-mlops-20260612`
- Formal search scale: 10 local Optuna trials, 5-fold CV
- Baseline: `baseline_logreg_v1`, QWK `0.3651`
- Champion: `candidate_logreg_v1`, QWK `0.3672`
- Registry aliases: `baseline`, `candidate`, `champion`
- Champion URI: `models:/piu-risk@champion`

## P2 交付物

- [Final report](/home/er/桌面/MLsystem/reports/P2/p2_final_report.md)
- [Status audit](/home/er/桌面/MLsystem/reports/P2/p2_summary_report.md)
- [Optuna trials](/home/er/桌面/MLsystem/reports/P2/p2_formal_optuna_trials.csv)
- [Model comparison](/home/er/桌面/MLsystem/reports/P2/p2_model_comparison.csv)
- [Metric comparison figure](/home/er/桌面/MLsystem/reports/P2/figures/p2_metric_comparison.png)
- [Optuna trace figure](/home/er/桌面/MLsystem/reports/P2/figures/p2_optuna_trace.png)
- [Champion confusion matrix](/home/er/桌面/MLsystem/reports/P2/figures/p2_champion_confusion_matrix.png)
- [MLflow run status figure](/home/er/桌面/MLsystem/reports/P2/figures/p2_mlflow_run_status.png)

## 汇报口径

P2 的模型提升幅度很小：Champion 相比 baseline QWK 提升 `+0.0022`。汇报时应强调 MLOps 过程完整性：tracking、search、registry、artifact、API-compatible packaging、visualization，而不是夸大模型性能提升。
