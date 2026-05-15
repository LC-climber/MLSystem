# 中国科学院大学研究生课程项目计划书

- 项目编号: `MLSYS-2026S-P2-MLOPS-HMSHBAC`
- 课程名称: `机器学习系统`
- 对应作业: `项目实践及演示汇报-2`
- 项目题目: `基于 MLflow 的 EEG 有害脑活动识别 MLOps 实践与模型发布`
- 数据来源: `HMS - Harmful Brain Activity Classification`
- 文档版本: `v1`
- 日期: `2026-04-16`
- 团队成员: `待填写`
- 指导教师: `待填写`

## 摘要

本项目拟基于 `HMS - Harmful Brain Activity Classification` 竞赛数据，构建一个面向医疗信号识别的 MLOps 实践流程。项目将围绕 EEG 片段及其频谱表示，完成数据预处理、频谱生成或对齐、特征工程、模型设计、超参数优化、实验管理、误差分析、模型注册与模型发布。与课程项目 1 不同，本项目将保留 HMS 任务的深度学习本质，重点研究 `spectrogram-based CNN`、`hybrid CNN-RNN` 和轻量 `Transformer` 等模型在 `MLflow` 管理下的实验组织与演进过程。最终输出包括完整实验追踪、最优模型注册结果、医疗任务导向的 model card 和面向课程展示的可复现实验仓库。

关键词: `HMS`、`EEG`、`MLflow`、`医疗信号`、`ModelScope`

## 1. 研究背景与意义

EEG 有害脑活动识别是兼具医学价值和技术挑战性的任务。公开资料显示，HMS 竞赛数据来自 `1950` 名患者，包含 `106,800` 个 EEG 片段，标签覆盖 `6` 类脑活动模式。该任务的特点包括:

- 信号维度高
- 标签噪声与类别不平衡问题明显
- 频谱建模和误差分析都需要严谨记录

因此，该任务非常适合作为课程项目 2 的“高质量 MLOps 实践”候选题。

## 2. 项目目标

1. 建立 EEG 数据与 spectrogram 数据的一致化处理流程。
2. 使用 `MLflow` 跟踪所有训练、验证和调参过程。
3. 比较至少三类模型:
   - `CNN`
   - `CNN-RNN`
   - 轻量 `Transformer`
4. 完成误差分析、模型注册和模型发布。

## 3. 研究内容

### 3.1 数据工程

- EEG 片段与 spectrogram 对齐
- 标签清洗与类别统计
- 数据切分协议
- 缓存与存储格式优化

### 3.2 模型工程

- `CNN baseline`
- `CNN + BiGRU / BiLSTM`
- 轻量 `ViT` 或时频 Transformer

### 3.3 MLOps 工程

- Tracking
- Artifact 管理
- Model Registry
- 发布说明文档

## 4. 技术路线

1. 准备数据索引表与标签映射。
2. 统一 spectrogram 输入格式。
3. 训练 baseline CNN。
4. 使用 `MLflow` 记录超参数、指标和 artifact。
5. 进行模型增强与调优。
6. 选择最优模型注册为 `champion`。
7. 输出 `ModelScope` 发布材料。

## 5. MLflow 设计

### 5.1 Tracking 内容

- 数据版本
- 频谱生成版本
- 模型结构版本
- 损失函数
- 优化器与学习率
- batch size
- 训练轮数
- 设备信息
- 主指标

### 5.2 Artifact 内容

- 训练曲线
- 混淆矩阵
- PR 或 ROC 图
- 典型错误样本可视化
- 最优权重文件
- 推理脚本

### 5.3 Registry 规则

- `baseline-cnn`
- `best-cnn`
- `best-hybrid`
- `champion`
- `demo`

## 6. 实验设计

### 6.1 模型矩阵

- baseline:
  - 2D `CNN`
- enhanced:
  - `CNN + BiLSTM`
- advanced:
  - 轻量 `Transformer`

### 6.2 指标体系

主指标:

- `Macro-F1`
- `Log Loss`

辅指标:

- 参数量
- 训练时长
- 推理吞吐
- 模型大小

### 6.3 误差分析

重点分析:

- 易混淆类别
- 频谱质量对结果的影响
- 类别不平衡导致的偏差

## 7. 发布到 ModelScope 的方案

建议将发布内容控制在课程验收友好的范围内:

- 频谱输入说明
- 模型权重与推理脚本
- 示例文件
- README 与限制说明

## 8. 多场景实施方案

### 8.1 方案 A: 标准深度学习方案

- `CNN`
- `CNN + BiLSTM`
- `Transformer` 选做

### 8.2 方案 B: 稳妥课程方案

- 只保留 `CNN` 与 `CNN + BiLSTM`
- 重点做好 `MLflow + Registry + 发布`

### 8.3 方案 C: 资源受限保底方案

- 使用公开 spectrogram 镜像
- 仅训练 `CNN baseline`
- 将更多精力投入实验管理与发布规范

## 9. 资源条件与环境配置

- 本地 `5060 Ti`
  - 调试和可视化
- 远程 `4090`
  - 正式训练
- 推荐环境:
  - `torch 2.7.x + cu128`
  - `mlflow`
  - `albumentations`
  - `timm`
  - `optuna`

## 10. 可行性与难点

可行性:

- 数据公开
- 远程 `4090` 足以支撑轻量频谱模型
- `MLflow` 能清晰展示实验演进

难点:

- 医疗信号任务存在标签噪声
- 若做复杂 Transformer，课程时间压力较大

## 11. 进度安排

- `2026-04-16` 至 `2026-04-25`
  - 数据整理与 baseline 搭建
- `2026-04-26` 至 `2026-05-10`
  - `CNN` 训练与 MLflow 接入
- `2026-05-11` 至 `2026-05-25`
  - `CNN + BiLSTM` 与调参
- `2026-05-26` 至 `2026-06-10`
  - 注册与误差分析
- `2026-06-11` 至 `2026-06-25`
  - 发布与最终报告

## 12. 预期成果

- EEG 任务 MLOps 实验体系
- 最优频谱模型
- 注册与发布材料
- 中期与最终汇报文档

## 13. 风险与应对

- 风险 1:
  - 模型较难稳定复现
  - 应对: 先锁定数据版本和训练随机种子
- 风险 2:
  - 发布说明不够清楚
  - 应对: 提前编写标准化 model card

## 14. 参考资料

- HMS 数据说明论文: https://pmc.ncbi.nlm.nih.gov/articles/PMC12715239/
- spectrogram 镜像: https://www.kaggle.com/datasets/cdeotte/brain-spectrograms
- 公开竞赛说明: https://www.rist.co.jp/202404176540/
- MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
- ModelScope 官方仓库: https://github.com/modelscope/modelscope
