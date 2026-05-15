# 中国科学院大学研究生课程项目计划书

- 项目编号: `MLSYS-2026S-P2-MLOPS-CHILDMIND`
- 课程名称: `机器学习系统`
- 对应作业: `项目实践及演示汇报-2`
- 项目题目: `基于 MLflow 的问题性互联网使用风险识别 MLOps 实践与模型发布`
- 数据来源: `Kaggle Child Mind Institute — Problematic Internet Use`
- 文档版本: `v1`
- 日期: `2026-04-16`
- 团队成员: `待填写`
- 指导教师: `待填写`

## 摘要

本项目拟围绕青少年问题性互联网使用风险识别任务，构建一套完整的 `MLOps` 开发管理流程。项目将基于 Kaggle `Child Mind Institute — Problematic Internet Use` 数据，围绕数据清洗、缺失值建模、特征工程、模型选择、超参数优化、实验评价、模型注册与模型发布等环节展开，使用 `MLflow` 作为核心实验管理平台。项目计划在传统机器学习模型与轻量多模态深度模型之间建立分层 baseline，既保留课程项目的可控工作量，又体现工程规范、可追溯性和模型演进能力。最终项目将输出一套带版本管理的数据处理流程、实验记录与 best model 注册结果，并将最优模型整理为可发布到 `ModelScope` 的模型仓库。

关键词: `MLflow`、`MLOps`、`多模态健康数据`、`Child Mind Institute`、`ModelScope`

## 1. 研究背景与意义

课程项目 2 强调的不是单次建模成绩，而是完整的机器学习工程闭环。`Child Mind` 任务的优势在于它天然包含如下 MLOps 场景:

- 数据源异构，必须明确数据版本与特征版本。
- 缺失值、异常值和标签分布需要被显式记录。
- 传统模型与深度模型之间存在清晰的演化路径。
- 结果具有较强社会价值和应用解释空间。

因此，该任务非常适合作为一条从数据到发布的 MLOps 全流程示范。

## 2. 项目目标

本项目拟实现以下目标:

1. 使用 `MLflow Tracking` 记录所有实验运行。
2. 定义数据版本、特征版本和标签映射版本。
3. 建立至少三层模型体系:
   - 传统 baseline
   - 轻量深度模型
   - 融合模型
4. 完成超参数优化与模型评估。
5. 将最优模型注册并整理发布到 `ModelScope`。

## 3. 研究内容

### 3.1 数据工程

- 原始数据结构梳理
- 缺失值分布分析
- 特征字段分层
- 数据清洗规则固化
- 数据切分协议固化

### 3.2 特征工程

- 数值特征标准化
- 类别特征编码
- 时间序列统计特征抽取
- 多源特征融合
- 特征重要性分析

### 3.3 模型层次

- Level 1:
  - `Logistic Regression`
  - `CatBoost / XGBoost`
- Level 2:
  - `MLP`
  - `TabTransformer` 或轻量融合网络
- Level 3:
  - 传感分支编码器 + 表格分支编码器 + late fusion

## 4. 技术路线

技术路线拟采用如下分层结构:

1. 数据层:
  - 原始样本清洗
  - schema 统一
  - 数据快照版本化
2. 特征层:
  - 构建 `v1-basic`、`v2-biosensing`、`v3-fusion`
3. 模型层:
  - baseline 到 fusion model 逐步升级
4. MLOps 层:
  - `MLflow Tracking`
  - `MLflow Artifacts`
  - `MLflow Model Registry`
5. 发布层:
  - 导出最佳模型
  - 编写 model card
  - 发布至 `ModelScope`

## 5. MLflow 设计方案

### 5.1 Tracking 规范

每个 run 统一记录:

- 数据版本
- 特征版本
- 标签版本
- 训练脚本版本
- 模型名称
- 超参数
- 主指标与辅指标
- 运行设备信息

### 5.2 Artifact 规范

统一保存以下 artifact:

- 数据字典
- 缺失值统计图
- 特征分布图
- 混淆矩阵
- ROC 或 Kappa 曲线相关图
- 模型权重
- 推理脚本

### 5.3 Registry 规范

建议在 `MLflow Model Registry` 中维护以下别名:

- `baseline`
- `candidate`
- `champion`
- `demo`

## 6. 实验设计

### 6.1 数据版本设计

- `data_v1`
  - 清洗后的表格数据
- `data_v2`
  - 增加传感统计特征
- `data_v3`
  - 完整融合版数据

### 6.2 特征版本设计

- `feat_v1_basic`
  - 基础数值与类别特征
- `feat_v2_imputed`
  - 完整缺失值处理版
- `feat_v3_fusion`
  - 传感特征融合版

### 6.3 模型实验矩阵

- baseline 组:
  - `Logistic Regression`
  - `CatBoost`
- neural 组:
  - `MLP`
  - `TabTransformer`
- fusion 组:
  - 双分支融合网络

### 6.4 指标体系

主指标:

- `Quadratic Weighted Kappa`
- `Macro-F1`

辅指标:

- 训练时间
- 推理时间
- 参数量
- 模型大小
- 稳定性指标

## 7. 发布到 ModelScope 的方案

### 7.1 发布内容

- 最优模型权重
- 推理代码
- README
- 数据输入格式说明
- 示例输入输出
- 模型 card

### 7.2 发布形式

优先采用“课程验收友好型”发布方案:

- 不强行部署在线服务
- 重点保证模型可下载、可加载、可复现、可演示

## 8. 多场景实施方案

### 8.1 方案 A: 标准多模态方案

适用条件:

- 远程 `4090` 可稳定使用
- 团队有足够精力处理融合模型

实施内容:

- 完整做 `basic -> imputed -> fusion`
- 完成 `CatBoost + MLP + 融合模型`
- 完成 Model Registry 与 ModelScope 发布

### 8.2 方案 B: 中等复杂度方案

适用条件:

- 时间有限
- 需要保证计划可落地

实施内容:

- 重点做表格数据 + 传感统计特征
- 模型以 `CatBoost`、`MLP` 为主
- 融合模型只做一版演示

### 8.3 方案 C: 保底发布方案

适用条件:

- 融合模型效果不稳定
- 发布时间紧

实施内容:

- 选用 `CatBoost` 或 `MLP` 最佳版本作为最终发布模型
- 强调 MLOps 全流程完整性而非模型复杂度

## 9. 资源条件与环境配置

- 本地 `5060 Ti`
  - 负责调试与演示
- 远程 `4090`
  - 负责正式训练和超参搜索
- 推荐软件环境:
  - `torch 2.7.x + cu128`
  - `mlflow`
  - `optuna`
  - `pandas`
  - `scikit-learn`
  - `catboost`

## 10. 可行性与难点分析

可行性来源:

- 数据公开易得
- 任务适合从传统模型逐步过渡到深度模型
- `MLflow` 对课程展示友好

关键难点:

- 多模态数据清洗复杂
- 缺失值处理策略可能影响最终结论
- 若要做高质量融合模型，需要控制实验规模

## 11. 进度安排

- `2026-04-16` 至 `2026-04-25`
  - 数据版本与特征版本规范确定
- `2026-04-26` 至 `2026-05-10`
  - 完成 baseline 与 MLflow 接入
- `2026-05-11` 至 `2026-05-25`
  - 完成神经网络实验与超参数优化
- `2026-05-26` 至 `2026-06-10`
  - 完成 best model 注册
- `2026-06-11` 至 `2026-06-25`
  - 完成 ModelScope 发布材料与最终报告

## 12. 预期成果

- 一套标准化数据处理脚本
- 一套 MLflow 实验跟踪体系
- 一个注册到 Registry 的最优模型
- 一个发布到 ModelScope 的课程项目模型仓库
- 一份 MLOps 实践报告

## 13. 风险与应对

- 风险 1:
  - 融合模型训练收益有限
  - 应对: 发布时采用更稳的 `CatBoost` 或 `MLP`
- 风险 2:
  - ModelScope 仓库封装耗时
  - 应对: 先完成最小可用发布版本
- 风险 3:
  - 远程 GPU 资源紧张
  - 应对: 本地 `5060 Ti` 负责调试，远程只跑正式实验

## 14. 参考资料

- Child Mind Institute Healthy Brain Network: https://childmind.org/our-research/center-for-the-developing-brain/healthy-brain-network/
- Kaggle 数据镜像: https://www.kaggle.com/datasets/akirahoimancheng/child-mind-institute-problematic-internet-use
- 任务相关论文: https://www.sciencedirect.com/science/article/pii/S2214782925000648
- MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
- ModelScope 官方仓库: https://github.com/modelscope/modelscope
