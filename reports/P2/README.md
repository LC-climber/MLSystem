# P2 Reports

P2 阶段（MLOps 实践）已完成代码实现，数据存储在数据库中。

## P2 数据位置

P2 阶段的实验数据和模型信息存储在以下位置：

| 类型 | 位置 | 说明 |
| --- | --- | --- |
| Optuna 优化记录 | `../../src/optuna.db` | SQLite 数据库，包含所有 trial 的超参数和结果 |
| MLflow 实验追踪 | `../../mlruns/` | MLflow 数据目录，包含实验、运行、指标和 artifacts |
| MLflow 模型注册 | `../../mlruns/models/` | 注册的模型版本和元数据 |

## 可选：导出报告文件

如需生成可读的报告文件，可运行以下脚本：

```bash
# 导出 Optuna trials
python -c "
import sqlite3
import pandas as pd
conn = sqlite3.connect('../../src/optuna.db')
df = pd.read_sql_query('SELECT * FROM trials', conn)
df.to_csv('p2_optuna_trials.csv', index=False)
print(f'Exported {len(df)} trials')
"

# 查看 MLflow 实验
mlflow ui --backend-store-uri file://../../mlruns
```

## P2 关键成果

### 1. MLflow 深度集成
- 实验追踪与参数管理
- 模型注册与四别名体系（baseline/candidate/champion/archive）
- 自动生成 Model Card
- 6 种可视化图表（混淆矩阵、ROC 曲线等）

### 2. Optuna 超参数优化
- 支持 100-trial 自动优化
- MedianPruner 早停机制
- 与 MLflow 无缝集成
- 完整的试验记录和分析

### 3. FastAPI 推理服务
- 5 个 REST API 端点
- 完整的特征工程流程
- 健康检查与模型热重载
- E2E 测试覆盖

### 4. Docker 容器化部署
- 推理镜像（CPU 版本，~1.5GB）
- 训练镜像（GPU 版本，~8GB）
- docker-compose 一键启动
- 完整的测试脚本

### 5. 模型发布方案
- ModelScope + HuggingFace 双渠道
- 28 项发布清单
- 完整的发布指南文档

## 报告位置说明

**当前状态**：P2 代码实现已完成，实验数据存储在数据库中（Optuna DB 和 MLflow），但尚未导出为独立的报告文件（如 P1 的 CSV 和图表）。

**与 P1 的区别**：
- P1：有独立的 CSV、图表、PPT 等静态报告文件
- P2：数据存储在 Optuna DB 和 MLflow 中，通过工具查询和可视化

如需生成类似 P1 的报告文件，可以添加导出脚本将数据库内容导出为 CSV/Markdown。

相关文档：
- 技术指南：`../../00_docs/v2/04_plan_p2_v2.md`
- 模型发布：`../../00_docs/MODEL_PUBLISHING_GUIDE.md`
- Champion 选定：`../../00_docs/CHAMPION_SELECTION_GUIDE.md`
- 实施计划：`../../00_docs/P2_IMPLEMENTATION_PLAN.md`
