# P2 汇报讲稿要点

## 1. 开场

P2 的目标不是重新做一个单点模型，而是把 P1 的可复现实验推进到 MLOps 闭环：实验追踪、超参搜索、模型注册、artifact 管理、服务可加载模型和可视化报告。

## 2. 实验设置

- 使用 P1 的 canonical StratifiedGroupKFold，5-fold CV。
- Tracking backend 为本地 `mlruns.db`，artifact root 为 `mlruns_artifacts/`。
- Formal Optuna study 为 `p2-formal-mlops-20260612`。
- 本地正式搜索规模为 10 trials。

## 3. 核心结果

- Baseline 是 `baseline_logreg_v1`，QWK 为 `0.3651`。
- Champion 是 `candidate_logreg_v1`，QWK 为 `0.3672`。
- 提升为 `+0.0022` QWK，幅度很小。
- 因此汇报重点应放在 MLOps 流程完整性，而不是夸大模型性能提升。

## 4. 可视化说明

- `p2_metric_comparison.png`: 展示 baseline 与 champion 在 QWK、Macro-F1、Balanced Accuracy 上的对比。
- `p2_optuna_trace.png`: 展示每个 Optuna trial 的 QWK 和 best-so-far 曲线。
- `p2_champion_confusion_matrix.png`: 展示 champion 的 5-fold CV 错误结构。
- `p2_mlflow_run_status.png`: 展示 MLflow 中 P2 runs 的状态分布，说明历史 smoke/失败 runs 被保留为审计记录。

## 5. Registry 和可服务模型

- 注册模型名为 `piu-risk`。
- `baseline` alias 指向版本 4。
- `candidate` alias 指向版本 5。
- `champion` alias 指向版本 6。
- Champion 可通过 `models:/piu-risk@champion` 加载并完成预测。

## 6. 风险与局限

- 搜索规模是本地正式 10 trials，不是早期计划中的 100 trials。
- Champion 提升很小，需要如实说明。
- 类别不平衡仍然明显，混淆矩阵显示相邻 severity level 间仍有混淆。
- 后续可以扩展更大搜索空间、校准概率、针对 minority classes 做重采样或损失函数改进。

## 7. 结尾

P2 最终交付的是一条可审计、可复现、可服务的 MLOps 链路。所有关键证据都放在 `reports/P2/`，模型和运行记录保存在 `mlruns.db` 与 `mlruns_artifacts/`。
