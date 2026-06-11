# MLsystem 项目进度快照 - 2026-06-11

**快照时间**: 2026-06-11  
**项目状态**: P1 完成，P2 本地 MLOps 流程完成。

## 进度概览

| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| P1 多系统对比 | 完成 | 报告、图表、表格和中期材料齐全 |
| P2 正式实验 | 完成 | `p2-formal-mlops-20260612`, 10 trials, 5-fold CV |
| P2 模型注册 | 完成 | `baseline/candidate/champion` aliases 已设置 |
| P2 交付证据 | 完成 | 报告、CSV、图表、MLflow artifacts 已生成 |
| P2 API-compatible model | 完成 | `models:/piu-risk@champion` 可加载并预测 |

## P2 关键指标

- Baseline QWK: `0.3651`
- Champion QWK: `0.3672`
- QWK improvement: `+0.0022`
- Formal Optuna best trial: `logreg_v1`, `C=1.115861961007209`

## 交付位置

- `reports/P2/p2_final_report.md`
- `reports/P2/p2_summary_report.md`
- `reports/P2/p2_model_comparison.csv`
- `reports/P2/p2_formal_optuna_trials.csv`
- `reports/P2/figures/`
- `mlruns.db`
- `mlruns_artifacts/`

## 注意事项

- 早期 smoke/失败 trial 保留在数据库中作为审计历史；最终汇报使用 formal study `p2-formal-mlops-20260612`。
- 10-trial 是本地正式可复现搜索规模，不再宣称完成 100-trial 搜索。
- 模型性能提升很小，应重点汇报 MLOps 闭环完整性。
