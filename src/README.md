# src/ — 源代码目录说明

本目录是 PIU 项目的 Python 包源码,包名为 `src`。P1 多系统对比和 P2 MLOps 全流程均已完成实现，包括数据处理、模型训练、实验脚本、MLflow 集成、FastAPI 部署和完整测试。

## 顶层文件

| 文件 | 作用 |
|---|---|
| `config.py` | 全局配置:项目路径、随机种子、MLflow experiment、特征版本、P1/P2 指标、CV 折数、模型默认超参、Spark 配置和部署常量。 |
| `__init__.py` | 将 `src/` 标记为 Python package,支持 `python -m src.<module>` 形式运行。 |
| `README.md` | 本文件,解释 `src/` 下源码结构和入口。 |

## 子目录总览

| 目录 | 当前角色 | 状态 |
|---|---|---|
| `data/` | PIU 数据常量、加载、切分、tabular 特征、actigraphy 特征和 feat_v1/feat_v2 构建。 | ✅ P1 已完成 |
| `models/` | 统一模型接口和 sklearn / Spark / PyTorch baseline。 | ✅ P1 已完成 |
| `training/` | 共享 5-fold CV 训练评估循环,保证三系统公平对比。 | ✅ P1 已完成 |
| `evaluation/` | 分类指标实现:Macro-F1、QWK、Balanced Accuracy、Log Loss 和 CV 汇总。 | ✅ P1/P2 完成 |
| `experiments/` | P1 实验入口脚本:系统对比、特征阶段对比、A5/A6、可视化；P2 Optuna 优化。 | ✅ P1/P2 已完成 |
| `utils/` | I/O、日志、随机种子、系统指标、Spark 会话等通用工具。 | ✅ P1 已完成 |
| `mlflow_utils/` | MLflow Tracking、Registry、可视化、Model Card 生成等工具。 | ✅ P2 已完成 |
| `deployment/` | FastAPI 推理服务、模型加载、特征工程、健康检查等部署代码。 | ✅ P2 已完成 |
| `scripts/` | Python package 占位目录。根目录 shell 脚本在 `../scripts/`。 | 占位 |

`__pycache__/` 是 Python 运行缓存,不是项目源码,不用维护。

## data/

| 文件 | 作用 |
|---|---|
| `constants.py` | 数据路径、ID/target 列名、SII 类别、actigraphy 字段、PCIAT 标签泄漏列和 SII 分箱阈值。 |
| `loader.py` | 加载 `train.csv`、`test.csv` 和单个参与者 actigraphy parquet;提供数据完整性检查和可用特征列筛选。 |
| `splits.py` | 构建并读取统一 5-fold `StratifiedGroupKFold` 切分文件,只对有 `sii` 标签样本做监督学习切分。 |
| `feature_engineering.py` | 构建 `feat_v1_tabular`:去除泄漏列、one-hot 类别字段,并保留数值缺失供 fold 内 imputer 处理。 |
| `preprocess_tabular.py` | 通用 tabular 预处理类,包含缺失填补、标准化和高缺失列处理;部分早期/备用逻辑仍在此处。 |
| `actigraphy_features.py` | `feat_v2` actigraphy 聚合特征的单一规格来源:6 个信号 x 统计量 + non-wear/day-night 等 47 个 `act_*` 列。 |
| `preprocess_actigraphy_pandas.py` | pandas streaming 版 actigraphy 聚合,逐 `id=*` 分区处理以避免全量读入 OOM,生成 `feat_v2__cpu__seed42.parquet`。 |
| `preprocess_actigraphy_spark.py` | Spark `groupBy(id).applyInPandas` 版 actigraphy 聚合,复用 pandas reducer 保证和 CPU reference 数值等价。 |

常用入口:

```bash
python -m src.data.splits
python -m src.data.feature_engineering
python -m src.data.preprocess_actigraphy_pandas
python -m src.data.preprocess_actigraphy_spark
```

## models/

| 文件 | 作用 |
|---|---|
| `base.py` | `BaseModel` 抽象接口,统一 `fit / predict / predict_proba / save / load / get_params`,让同一个 CV loop 驱动三套系统。 |
| `sklearn_baselines.py` | 单机 sklearn baseline:`LogisticRegression` 和 `MLPClassifier`。 |
| `spark_baselines.py` | Spark MLlib baseline:multinomial LR 和 MLP,内部负责 numpy 与 Spark DataFrame 转换。 |
| `torch_baselines.py` | PyTorch baseline:线性 LR 和两层 MLP,内部负责 tensor、device、class weight 和 early stopping。 |
| `__init__.py` | package 标记。 |

设计约束:

- 所有模型对外都使用 numpy array 输入/输出。
- Spark/PyTorch 的内部数据结构转换计入系统成本,这是 P1 训练阶段对比的一部分。
- LR 尽量对齐 class balancing;MLP 的 class weight 支持因系统能力不同而不同,结果报告中按系统差异处理。

## training/

| 文件 | 作用 |
|---|---|
| `cv.py` | 项目共享 5-fold CV runner。每个 fold 内只在训练折 fit imputer/scaler,随后训练模型、计算指标、记录训练耗时、RSS、推理延迟和模型大小。 |
| `__init__.py` | package 标记。 |

`run_cv(...)` 是 P1 模型阶段的核心公共协议。三系统 x 两算法都走这里,以保证 feature、fold、seed、预处理和指标计算一致。

## evaluation/

| 文件 | 作用 |
|---|---|
| `metrics.py` | 实现 Macro-F1、Quadratic Weighted Kappa、Balanced Accuracy、Log Loss 和 CV mean/std 汇总。 |
| `__init__.py` | package 标记。 |

指标约定来自 `src/config.py`:P1 主指标为 `macro_f1`,辅指标为 `qwk` 和 `balanced_accuracy`;P2 主指标为 `qwk`。

## experiments/

| 文件 | 作用 |
|---|---|
| `run_p1_systemwise.py` | P1 Table 2 入口。按 feature/cohort/system 运行 sklearn / Spark / PyTorch 的 LR/MLP 5-fold CV,输出 `reports/P1/p1_systemwise_*.csv`。 |
| `run_p1_feature_stage.py` | P1 Table 1 入口。比较 pandas streaming 与 Spark `applyInPandas` 构建 `feat_v2` 的耗时、RSS、hash 和数值等价性。 |
| `run_p1_spark_parallelism.py` | W3 A6 入口。扫描 Spark `local[4] / local[8] / local[20]`,比较特征阶段并行度、RSS 和等价性。 |
| `run_p1_ablation_a5_coverage.py` | W3 A5 入口。分析 actigraphy 覆盖率、fold 类别稀疏和 `v2/all - v1/all` 指标 delta。 |
| `run_p1_visualizations.py` | W3 可视化入口。读取报告 CSV,生成 Table 2 指标图、系统开销图、A5/A6 图、混淆矩阵和 feat_v2 lineage 图。 |
| `__init__.py` | package 标记。 |

常用入口:

```bash
python -m src.experiments.run_p1_feature_stage --mlflow
python -m src.experiments.run_p1_systemwise --feature v1 --mlflow
python -m src.experiments.run_p1_systemwise --feature v2 --mlflow
python -m src.experiments.run_p1_systemwise --feature v2 --cohort actigraphy --mlflow
python -m src.experiments.run_p1_ablation_a5_coverage
python -m src.experiments.run_p1_spark_parallelism --masters local[4],local[8],local[20] --mlflow
python -m src.experiments.run_p1_visualizations
```

## utils/

| 文件 | 作用 |
|---|---|
| `io.py` | CSV/Parquet 读写封装,自动创建输出目录。 |
| `logging.py` | 项目日志格式和 logger 获取工具。 |
| `reproducibility.py` | 全局随机种子、PyTorch device 选择等复现相关工具。 |
| `system_metrics.py` | RSS、GPU memory、模型大小、推理延迟和吞吐测量。 |
| `spark.py` | SparkSession 单例与环境修正:固定 Java 版本、Python worker、local IP、driver memory 等。 |
| `__init__.py` | package 标记。 |

## mlflow_utils/

| 文件 | 作用 |
|---|---|
| `tracking.py` | MLflow Tracking 工具:实验记录、参数/指标/artifact 日志、可视化图表上传。 |
| `registry.py` | MLflow Registry 工具:模型注册、别名管理、版本查询、模型加载。 |
| `model_card.py` | Model Card 生成:自动生成包含指标、特征、超参数的模型文档。 |
| `visualizations.py` | MLflow 可视化:混淆矩阵、ROC 曲线、学习曲线等图表生成。 |
| `__init__.py` | package 标记。 |

P2 MLflow 深度集成已完成,支持完整的实验追踪、模型注册、四别名体系（baseline/candidate/champion/archive）和自动文档生成。

## deployment/

| 文件 | 作用 |
|---|---|
| `fastapi_app.py` | FastAPI 推理服务主入口:5 个 API 端点（/health、/predict、/model_info 等）。 |
| `feature_engineering.py` | 部署用特征工程:与训练时特征处理保持一致的推理时特征准备。 |
| `model_loader.py` | 模型加载工具:从 MLflow Registry 按别名加载模型。 |
| `README.md` | FastAPI 服务文档:端点说明、使用示例、部署建议。 |
| `__init__.py` | package 标记。 |

P2 FastAPI 推理服务已完成,支持健康检查、模型信息查询、单样本/批量预测、模型热重载等功能。

## scripts/

这个目录目前主要是 Python package 占位;根目录已有 shell 与构建脚本在 `../scripts/`，包括：
- `register_baseline.py`:Baseline 模型批量注册脚本
- `test_docker.sh`:Docker 镜像构建和测试脚本
- 其他辅助工具脚本

## 当前数据流

```text
data/raw/train.csv
  -> src.data.splits                         -> data/splits/stratified_group_kfold_seed42.csv
  -> src.data.feature_engineering            -> data/processed/feat_v1__seed42.parquet
  -> src.data.preprocess_actigraphy_pandas   -> data/processed/feat_v2__cpu__seed42.parquet
  -> src.data.preprocess_actigraphy_spark    -> data/processed/feat_v2__spark__seed42.parquet

data/processed/feat_v1|feat_v2 + data/splits
  -> src.experiments.run_p1_systemwise       -> reports/P1/p1_systemwise_*.csv

reports/P1/*.csv
  -> src.experiments.run_p1_ablation_a5_coverage
  -> src.experiments.run_p1_spark_parallelism
  -> src.experiments.run_p1_visualizations   -> reports/P1/figures/
```

## 维护规则

- 新增可直接运行的实验脚本放在 `experiments/`,并在本 README 的入口表中登记。
- 新增可复用的数据处理逻辑放在 `data/`;一次性汇报脚本不要塞进 `data/`。
- 新增模型必须继承 `models.base.BaseModel`,否则不能接入共享 CV loop。
- P1 指标计算只通过 `evaluation.metrics` 统一实现,避免不同脚本各算一套。
- Spark 代码必须通过 `utils.spark.get_spark_session()` 获取 session,避免 Java/Python 版本和 driver memory 问题回归。
- 生成的表格、图、模型和缓存不要放进 `src/`;输出应进入 `../data/processed/`、`../reports/<阶段>/`、`../models/` 或 MLflow artifact。
