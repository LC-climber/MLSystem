# Kaggle 竞赛候选项目整理 v1

- 文档编号: `MLSYS-2026S-KAGGLE-CANDIDATES-v1`
- 创建日期: `2026-04-16`
- 目的: 为《机器学习系统》课程项目筛选适合当前硬件条件的 Kaggle 竞赛型题目
- 当前硬件前提:
  - 本地: `i5-14600K / 31 GiB RAM / RTX 5060 Ti`
  - 远程: `单卡 RTX 4090`
  - 深度学习环境约束: 本地优先 `PyTorch >= 2.7.x + cu128`

## 1. 筛选标准

本次筛选只保留同时满足以下条件的方向:

- 来自 Kaggle 竞赛，或与 Kaggle 竞赛直接对应
- 数据公开、容易获得，最好还能找到公开镜像或官方外部来源
- 在 `本地 CPU + 本地 5060 Ti + 远程单卡 4090` 的条件下可完成
- 题目不太“经典课设化”，尽量有一定新意
- 能服务于本课程两类作业:
  - 项目 1: 多系统算法对比
  - 项目 2: MLflow 全流程 MLOps 与模型发布

## 2. 难度星级说明

- `★☆☆☆☆`: 入门，数据和建模都较直观
- `★★☆☆☆`: 偏简单，适合作为稳妥备选
- `★★★☆☆`: 中等，需要完整实验设计
- `★★★★☆`: 偏难，需要较强特征工程或时序/多模态建模
- `★★★★★`: 高难，工程和建模复杂度都较高

## 3. 总表

| 题目 | 任务类型 | 新颖度 | 难度 | 硬件适配 | 数据获取 | 对课程适配度 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Child Mind Institute — Problematic Internet Use` | 多模态分类 | 高 | `★★★★☆` | 很好 | 容易 | 很强 | `优先推荐` |
| `NFL Big Data Bowl 2026 / 2025` | 时空轨迹预测/分析 | 很高 | `★★★★☆` | 很好 | 容易 | 很强 | `优先推荐` |
| `HMS - Harmful Brain Activity Classification` | EEG 分类 | 很高 | `★★★★★` | 好 | 较容易 | 强 | `强推荐` |
| `BirdCLEF 2024` | 音频多标签分类 | 很高 | `★★★★☆` | 好 | 较容易 | 强 | `推荐` |
| `Google Research - Identify Contrails to Reduce Global Warming` | 遥感分割 | 很高 | `★★★★★` | 可做 | 较容易 | 中强 | `进阶推荐` |
| `G2Net Detecting Continuous Gravitational Waves` | 科学信号检测 | 很高 | `★★★★☆` | 可做 | 容易 | 中强 | `进阶推荐` |
| `Cassava Leaf Disease Classification` | 图像分类 | 中等 | `★★☆☆☆` | 很好 | 很容易 | 中等 | `稳妥备选` |

## 4. 逐项分析

### 4.1 Child Mind Institute — Problematic Internet Use

- Kaggle 竞赛: `Child Mind Institute — Problematic Internet Use`
- 任务概述:
  - 预测青少年问题性互联网使用的严重程度
  - 数据包含 `biosensing data + tabular data`
- 数据开放性:
  - Kaggle 竞赛数据公开可下载
  - 背后对应 `Child Mind Institute` 的 `Healthy Brain Network` 开放科学项目
- 依据:
  - Child Mind Institute 官方说明 `Healthy Brain Network` 面向 `5-21` 岁参与者，且明确表示会将去标识化数据共享给全球科研社区
  - 一篇基于该 Kaggle 竞赛的数据分析论文提到: Kaggle 子集约有 `3960` 条样本、`82` 个表格属性，并包含 biosensing 数据
- 难度评级: `★★★★☆`
- 适配当前硬件:
  - 本地 CPU: 很适合做表格特征、baseline 和 Spark 对比
  - 本地 `5060 Ti`: 适合做轻量 MLP、时序编码器、多模态融合调试
  - 远程 `4090`: 适合做正式训练、超参搜索、MLflow 实验
- 适合作业方式:
  - 项目 1:
    - 非常适合
    - 可将时序/穿戴设备数据先切窗聚合为统计特征，再在 `sklearn / Spark / PyTorch` 上比较 `Logistic Regression`、`MLP`
  - 项目 2:
    - 非常适合
    - 可以完整做数据清洗、缺失值处理、特征工程、多模态模型、实验追踪和发布
- 风险:
  - 真实任务涉及缺失值、不平衡和多模态融合，实验设计要比普通表格题更严谨
- 结论:
  - 这是当前最适合你们课程要求的 Kaggle 方向之一
  - 如果想保持“同一主题串联两项作业”，它是最强候选

### 4.2 NFL Big Data Bowl 2026 / 2025

- Kaggle 竞赛: `NFL Big Data Bowl`
- 任务概述:
  - 基于 `Next Gen Stats` 球员追踪数据做运动分析或运动轨迹预测
- 数据开放性:
  - Kaggle 持续承办该系列竞赛
  - NFL Football Operations 官方页面公开介绍竞赛背景、任务和年份数据范围
- 依据:
  - NFL 官方说明 `2026` 年题目首次要求根据传球前数据预测空中传球后的球员移动轨迹
  - 官方明确说明 `2023` 和 `2024` 赛季数据可用于建模，并以 `2025` 赛季特定周次结果做评估
- 难度评级: `★★★★☆`
- 适配当前硬件:
  - 本地 CPU: 很适合做数据清洗、轨迹特征统计、baseline
  - 本地 `5060 Ti`: 适合做轻量 LSTM/Transformer 或图模型原型
  - 远程 `4090`: 适合做正式时空序列模型训练
- 适合作业方式:
  - 项目 1:
    - 很适合
    - 适合比较 `传统特征 + 分类/回归模型` 与 `序列模型`
    - 也适合讨论 Spark 是否真的有收益
  - 项目 2:
    - 适合
    - 但最终发布到 ModelScope 的“通用模型仓库表达”不如图像/音频/医疗信号任务自然
- 风险:
  - 需要较多业务理解，轨迹特征定义要花时间
- 结论:
  - 如果你想做一个“不撞题而且很有展示性”的项目，这是最有意思的候选之一

### 4.3 HMS - Harmful Brain Activity Classification

- Kaggle 竞赛: `HMS - Harmful Brain Activity Classification`
- 任务概述:
  - 基于 ICU 场景的 EEG 数据识别癫痫发作等有害脑活动
- 数据开放性:
  - Kaggle 提供竞赛数据
  - 有公开的 `Brain-Spectrograms` 镜像数据集，许可为 `CC0`
- 依据:
  - 公开研究论文写明该 Kaggle 数据集来自 `1950` 名患者，包含 `106,800` 个 EEG 片段，分为 `6` 类模式
  - Kaggle 上公开镜像说明可直接使用 `spectrogram_id` 与竞赛 `train.csv` 对齐
- 难度评级: `★★★★★`
- 适配当前硬件:
  - 本地 CPU: 不适合做完整深度训练，但可做数据检查和小样本预处理
  - 本地 `5060 Ti`: 适合小规模 spectrogram 模型调试
  - 远程 `4090`: 适合正式训练
- 适合作业方式:
  - 项目 1:
    - 一般
    - 不太适合拿来做 `单机 / Spark / 深度学习系统` 的同算法横向对比
  - 项目 2:
    - 非常适合
    - 非常适合做 `MLflow + 医疗信号深度模型 + 模型注册`
- 风险:
  - 医疗信号预处理复杂
  - 任务本身偏难
- 结论:
  - 如果项目 2 想做得更强、更“研究味”，这是高质量候选

### 4.4 BirdCLEF 2024

- Kaggle 竞赛: `BirdCLEF 2024`
- 任务概述:
  - 从鸟类音频中识别物种
- 数据开放性:
  - LifeCLEF 官方明确说明 `BirdCLEF 2024` 在 Kaggle 上举行
  - 有公开的 mel 频谱镜像数据，例如约 `193,000` 张 `224x224` 频谱图版本
- 依据:
  - LifeCLEF 官方说明这项任务服务于被动声学监测和生物多样性保护
  - Rist 对该 Kaggle 竞赛的说明提到任务使用印度西高止山脉录制的鸟类音频，类别数为 `182`
- 难度评级: `★★★★☆`
- 适配当前硬件:
  - 本地 CPU: 可以做音频转 mel 预处理，但耗时
  - 本地 `5060 Ti`: 适合小规模 CNN 调试
  - 远程 `4090`: 适合正式训练
- 适合作业方式:
  - 项目 1:
    - 中等
    - 若先把音频统一变为 mel 图，可做跨系统对比，但工程量大于表格/时序
  - 项目 2:
    - 很适合
    - 音频转图像后可做 MLflow 完整实验，并且演示效果很好
- 风险:
  - 类别多、标签噪声高、音频预处理成本高
- 结论:
  - 如果你想做“有趣又能演示”的项目 2，这是很强的备选

### 4.5 Google Research - Identify Contrails to Reduce Global Warming

- Kaggle 竞赛: `Google Research - Identify Contrails to Reduce Global Warming`
- 任务概述:
  - 从卫星图像中分割飞行尾迹云
- 数据开放性:
  - Kaggle 竞赛数据公开可获取
  - 相关公开研究文章的数据可用性说明直接指向 Kaggle 竞赛页面
- 依据:
  - 公开报道和论文都指出这是一个 `semantic segmentation` 任务，目标是帮助减少尾迹云带来的气候影响
- 难度评级: `★★★★★`
- 适配当前硬件:
  - 本地 CPU: 不适合正式训练
  - 本地 `5060 Ti`: 适合 patch-based 调试
  - 远程 `4090`: 可做正式训练，但要控制分辨率、batch size 和增强策略
- 适合作业方式:
  - 项目 1:
    - 一般
    - 不太适合做三类系统上的“相同算法”对比
  - 项目 2:
    - 很适合
    - 适合做完整深度学习 MLOps
- 风险:
  - 分割任务工程复杂度高
  - 对实验管理要求高
- 结论:
  - 题目非常新颖，但更适合把项目 2 做成进阶版

### 4.6 G2Net Detecting Continuous Gravitational Waves

- Kaggle 竞赛: `G2Net Detecting Continuous Gravitational Waves`
- 任务概述:
  - 识别样本中是否存在模拟的连续引力波信号
- 数据开放性:
  - G2Net 官方新闻页面公开说明该 Kaggle 竞赛面向所有人免费开放
  - 官方还明确说明获奖方案需要公开源码
- 依据:
  - 官方说明该任务面向尚未被观测到的连续引力波信号检测
  - 这是典型的“科学信号检测”任务，方向很少见
- 难度评级: `★★★★☆`
- 适配当前硬件:
  - 本地 CPU: 适合数据探索与传统特征尝试
  - 本地 `5060 Ti`: 适合 2D CNN / 频谱模型调试
  - 远程 `4090`: 可做正式训练
- 适合作业方式:
  - 项目 1:
    - 中等
    - 可做“频谱特征 + 传统模型”与“深度模型”的比较
  - 项目 2:
    - 适合
    - 可作为一条足够新颖的 MLflow 题目
- 风险:
  - 领域背景较硬核
  - 汇报时需要额外讲清楚物理意义
- 结论:
  - 如果团队想要“少见且有科研感”的题目，这是非常强的冷门候选

### 4.7 Cassava Leaf Disease Classification

- Kaggle 竞赛: `Cassava Leaf Disease Classification`
- 任务概述:
  - 识别 `5` 类木薯叶片病害
- 数据开放性:
  - Kaggle 上有公开镜像数据集，描述清晰，许可为 `CC0`
- 依据:
  - 公开数据页明确给出五个类别目录，适合直接作为图像分类任务使用
- 难度评级: `★★☆☆☆`
- 适配当前硬件:
  - 本地 CPU: 可做小规模 baseline
  - 本地 `5060 Ti`: 很轻松
  - 远程 `4090`: 完全够用
- 适合作业方式:
  - 项目 1:
    - 一般
    - 图像任务不太适合 Spark 对比
  - 项目 2:
    - 适合
    - 很容易跑通 MLOps 全流程和发布
- 风险:
  - 题目完成度高，但不够新
- 结论:
  - 非常适合做“保底方案”，但不建议作为第一选择

## 5. 结合课程要求的推荐排序

### 5.1 最适合做两项作业主线统一的题目

1. `Child Mind Institute — Problematic Internet Use`
2. `NFL Big Data Bowl`
3. `G2Net Detecting Continuous Gravitational Waves`

这三类任务的共同点是:

- 更像“机器学习系统”而不是普通图像分类课设
- 既可以做传统机器学习，也能扩展到深度学习
- 更容易解释“单机、分布式、深度学习系统”之间的差异

### 5.2 最适合做项目 2 的题目

1. `HMS - Harmful Brain Activity Classification`
2. `BirdCLEF 2024`
3. `Google Contrails`

这三类任务的共同点是:

- 深度学习味道更浓
- 非常适合用 `MLflow` 跟踪实验
- 更容易做出好看的演示和模型发布材料

### 5.3 最稳妥但不够惊喜的备选

1. `Cassava Leaf Disease Classification`

它的优点是:

- 数据容易拿
- GPU 压力小
- 很容易做出完整结果

它的缺点是:

- 和课程“机器学习系统”的契合度一般
- 新意不够强

## 6. 对当前课程项目的具体建议

基于课程要求和你当前硬件，我建议优先考虑以下三套组合。

### 方案 A: 最平衡

- 项目 1: `Child Mind Institute — Problematic Internet Use`
- 项目 2: `Child Mind Institute — Problematic Internet Use`

优势:

- 两项作业完全共用同一主题，叙事最完整
- 项目 1 可做 `sklearn / Spark / PyTorch`
- 项目 2 可做 `MLflow + 多模态融合 + 最优模型发布`

风险:

- 需要更认真处理缺失值、不平衡和多模态问题

### 方案 B: 展示性更强

- 项目 1: `NFL Big Data Bowl`
- 项目 2: `BirdCLEF 2024` 或 `HMS`

优势:

- 一个偏系统分析，一个偏深度模型展示
- 中期和最终汇报更有看点

风险:

- 两项作业主题不完全统一

### 方案 C: 研究味更强

- 项目 1: `Child Mind Institute` 或 `G2Net`
- 项目 2: `HMS` 或 `Contrails`

优势:

- 题目新颖度高
- 容易做出“不是普通课程作业”的感觉

风险:

- 工作量和不确定性都更高

## 7. 我的当前推荐

如果只从“课程适配度 + 新颖性 + 硬件可做性 + 数据容易获得”四个维度综合排序，我当前推荐如下:

1. `Child Mind Institute — Problematic Internet Use`
2. `NFL Big Data Bowl`
3. `HMS - Harmful Brain Activity Classification`
4. `BirdCLEF 2024`
5. `Google Contrails`
6. `G2Net`
7. `Cassava`

其中最推荐你优先认真考虑的，是前 `3` 个。

## 8. 资料来源

### Kaggle / 数据镜像

- Child Mind Institute 竞赛镜像: https://www.kaggle.com/datasets/akirahoimancheng/child-mind-institute-problematic-internet-use
- HMS spectrogram 镜像: https://www.kaggle.com/datasets/cdeotte/brain-spectrograms
- Cassava 镜像: https://www.kaggle.com/datasets/nirmalsankalana/cassava-leaf-disease-classification
- BirdCLEF 2024 mel 频谱镜像: https://www.kaggle.com/datasets/nathaniellybrand/birdclef-2024-mel-spectrograms

### 官方组织方 / 官方项目页

- Child Mind Institute Healthy Brain Network: https://childmind.org/our-research/center-for-the-developing-brain/healthy-brain-network/
- NFL Big Data Bowl: https://operations.nfl.com/gameday/analytics/big-data-bowl
- BirdCLEF 2024 官方页: https://www.imageclef.org/node/316
- G2Net 官方竞赛说明: https://www.g2net.eu/news/detecting-continuous-gravitational-wave-signals-a-kaggle-competition

### 论文与公开说明

- PIU Kaggle 数据说明论文: https://www.sciencedirect.com/science/article/pii/S2214782925000648
- HMS 数据说明论文: https://pmc.ncbi.nlm.nih.gov/articles/PMC12715239/
- Google Contrails 数据可用性论文: https://pmc.ncbi.nlm.nih.gov/articles/PMC10914276/
- Google Contrails 竞赛公开说明: https://www.rist.co.jp/202308295444/
- HMS 竞赛公开说明: https://www.rist.co.jp/202404176540/
- BirdCLEF 2024 竞赛公开说明: https://www.rist.co.jp/202406146827/

## 9. 说明

- Kaggle 部分竞赛页面在搜索抓取时会出现 `anti-forgery token` 问题，因此本整理中部分事实使用了组织方官网、公开论文和 Kaggle 公共镜像页进行交叉确认。
- 难度星级与“硬件适配”属于基于任务类型、数据组织方式和当前资源条件作出的工程判断，不是官方评级。
