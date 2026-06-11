# P2 Optuna Best Trials

This file is generated from `src/optuna.db`.

- Total trials: 30
- Complete trials: 17
- Failed trials: 11
- Best QWK: 0.3858

## Top Complete Trials

| study_name               |   trial_id |   number | state    | datetime_start             | datetime_complete          |    value |         C |         alpha |   batch_size |   dropout | feature_version   |   hidden_dim_1 |   hidden_dim_2 |   learning_rate_init |   lr |   max_iter | model_type   |   weight_decay |
|:-------------------------|-----------:|---------:|:---------|:---------------------------|:---------------------------|---------:|----------:|--------------:|-------------:|----------:|:------------------|---------------:|---------------:|---------------------:|-----:|-----------:|:-------------|---------------:|
| p2-smoke-pipeline-2      |         20 |        0 | COMPLETE | 2026-06-12 00:03:08.610121 | 2026-06-12 00:03:48.655878 | 0.385788 |   8.0839  | nan           |          nan |       nan | v1                |            nan |            nan |        nan           |  nan |        nan | logreg       |            nan |
| p2-formal-mlops-20260612 |         28 |        7 | COMPLETE | 2026-06-12 00:08:58.127675 | 2026-06-12 00:09:44.731580 | 0.367216 |   1.11586 | nan           |          nan |       nan | v1                |            nan |            nan |        nan           |  nan |        nan | logreg       |            nan |
| p2-formal-mlops-20260612 |         30 |        9 | COMPLETE | 2026-06-12 00:09:45.783743 | 2026-06-12 00:11:21.763504 | 0.343912 |   6.26814 | nan           |          nan |       nan | v2                |            nan |            nan |        nan           |  nan |        nan | logreg       |            nan |
| p2-formal-mlops-20260612 |         25 |        4 | COMPLETE | 2026-06-12 00:06:44.848622 | 2026-06-12 00:07:57.061479 | 0.342105 |   2.61244 | nan           |          nan |       nan | v2                |            nan |            nan |        nan           |  nan |        nan | logreg       |            nan |
| p2-formal-mlops-20260612 |         26 |        5 | COMPLETE | 2026-06-12 00:07:57.070371 | 2026-06-12 00:08:56.778620 | 0.34113  |   1.95597 | nan           |          nan |       nan | v2                |            nan |            nan |        nan           |  nan |        nan | logreg       |            nan |
| p2-smoke-pipeline        |         19 |        0 | COMPLETE | 2026-06-12 00:02:19.075736 | 2026-06-12 00:02:20.478308 | 0.301919 | nan       |   1.81789e-05 |          128 |       nan | v2                |            128 |            128 |          0.00189803  |  nan |        160 | mlp          |            nan |
| p2-formal-mlops-20260612 |         23 |        2 | COMPLETE | 2026-06-12 00:06:40.236154 | 2026-06-12 00:06:42.711005 | 0.275042 | nan       |   0.000279731 |          128 |       nan | v2                |            256 |             32 |          0.000885938 |  nan |        120 | mlp          |            nan |
| p2-formal-mlops-20260612 |         24 |        3 | COMPLETE | 2026-06-12 00:06:42.719816 | 2026-06-12 00:06:44.839699 | 0.260755 | nan       |   7.13971e-05 |           64 |       nan | v2                |            128 |            128 |          0.00156271  |  nan |        200 | mlp          |            nan |
| p2-formal-mlops-20260612 |         21 |        0 | COMPLETE | 2026-06-12 00:06:35.079790 | 2026-06-12 00:06:37.070918 | 0.200066 | nan       |   0.00358602  |          256 |       nan | v1                |            128 |             32 |          0.000193558 |  nan |        160 | mlp          |            nan |
| p2-formal-mlops-20260612 |         22 |        1 | COMPLETE | 2026-06-12 00:06:37.082047 | 2026-06-12 00:06:40.227088 | 0.167058 | nan       |   0.00283533  |          128 |       nan | v1                |            128 |            128 |          0.000105406 |  nan |        160 | mlp          |            nan |
