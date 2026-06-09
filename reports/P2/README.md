# P2 Reports

P2 阶段也需要类似 P1 的分析报告,但重点不同。

建议沉淀的 P2 产物:

| 类型 | 建议文件 | 说明 |
| --- | --- | --- |
| Optuna 汇总 | `p2_optuna_trials.csv`, `p2_optuna_best_trial.md` | 记录 trial 排名、best params、目标指标和搜索空间结论 |
| 模型注册 | `p2_model_registry_summary.md` | 记录候选模型、版本、注册状态和选择理由 |
| 部署评估 | `p2_deployment_eval.csv`, `p2_api_smoke_report.md` | 记录 API 延迟、吞吐、错误样例和 smoke test 结果 |
| 监控分析 | `p2_monitoring_report.md` | 记录输入分布、预测分布、漂移风险和告警阈值 |
| 最终验收 | `p2_final_report.md` | 汇总 MLOps 流程、关键指标、复现实验入口和遗留风险 |

当前目录先作为 P2 报告落点保留。后续可以把 `run_p2_optuna.py` 的 best-trial 和 trials dataframe 自动导出到这里。
