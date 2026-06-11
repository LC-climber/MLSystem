# P2 Reports

本目录保存 P2 MLOps 实践的最终结果、图表、模型副本和审计导出。

## 最终结论

- P2 本地可复现 MLOps 流程已完成。
- Formal study: `p2-formal-mlops-20260612`
- Baseline QWK: `0.3651`
- Champion QWK: `0.3672`
- Champion URI: `models:/piu-risk@champion`
- Registry aliases: `baseline -> v7`, `candidate -> v8`, `champion -> v9`

## 核心文件

| 文件 | 用途 |
| --- | --- |
| `p2_final_report.md` | 最终汇报用报告 |
| `p2_summary_report.md` | 数据库/artifact 审计摘要 |
| `p2_model_comparison.csv` | baseline vs champion 指标表 |
| `p2_formal_optuna_trials.csv` | formal study 的 Optuna trials |
| `p2_mlflow_runs_summary.csv` | MLflow runs 摘要 |
| `p2_mlflow_model_versions.csv` | Registry 版本和 alias |
| `figures/p2_metric_comparison.png` | 指标对比图 |
| `figures/p2_optuna_trace.png` | Optuna 搜索过程图 |
| `figures/p2_champion_confusion_matrix.png` | Champion 混淆矩阵 |
| `figures/p2_mlflow_run_status.png` | MLflow run 状态图 |

## 重新生成

```bash
python -m src.experiments.run_p2_full_pipeline \
  --trials 10 --folds 5 --study-name p2-formal-mlops-20260612

python scripts/export_p2_reports.py
```

## 汇报注意

P2 的目标是展示完整 MLOps 闭环。Champion 相比 baseline 的 QWK 只提升 `+0.0022`，不应夸大为显著建模突破。
