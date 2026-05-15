# 《机器学习系统》课程项目计划书包 v1

- 文档编号: `MLSYS-2026S-PLAN-PORTFOLIO-v1`
- 课程名称: `机器学习系统`
- 文档用途: `项目立项 / 4.17 项目计划提交 / 中期汇报前方案评审`
- 创建日期: `2026-04-16`
- 计划书范围:
  - 项目实践及演示汇报-1: `多系统算法对比`
  - 项目实践及演示汇报-2: `MLops 实践`

## 1. 编制说明

本计划书包面向中国科学院大学研究生课程项目场景编制，结构上参考国科大研究生开题/中期类材料的常见要求，统一保留以下要素:

- 项目基本信息
- 摘要与关键词
- 选题背景与意义
- 国内外或竞赛背景
- 研究目标与研究内容
- 技术路线与实验设计
- 资源条件与可行性分析
- 进度安排
- 风险分析与备选方案
- 预期成果
- 参考资料

这种组织方式主要依据以下公开信息:

- 国科大研究生学位论文撰写规范强调材料应包含封面、摘要、正文、参考文献等规范部分，并遵循 `GB/T 7713.1` 与 `GB/T 7714`。
- 国科大开题报告管理说明强调开题材料应覆盖 `背景意义`、`国内外研究动态及发展趋势`、`主要研究内容`、`技术路线及研究方法`、`预期成果`、`时间安排`。
- 人工智能学院开题/中期通知显示，校内汇报通常要求 `10 分钟报告 + 5 分钟问答`，且书面材料需便于盲审和现场答辩裁剪。

基于以上要求，本计划书包不是简单题目清单，而是按“可提交、可汇报、可迭代”的标准编制。

## 2. 当前硬件与环境前提

- 本地:
  - CPU: `Intel Core i5-14600K`
  - 内存: `31 GiB`
  - GPU: `RTX 5060 Ti`
  - 建议深度学习环境: `PyTorch 2.7.x + cu128`
- 远程:
  - GPU: `单卡 RTX 4090`
- 本地环境管理:
  - `conda 25.7.0`
  - 建议环境名:
    - `mlsys_cpu`
    - `mlsys_gpu_local`
    - `mlsys_gpu_remote`

## 3. 文档清单

### 3.1 Child Mind Institute — Problematic Internet Use

- 项目 1 计划书:
  - [plan_p1_childmind_piu_v1.md](/home/er/桌面/MLsystem/00_docs/v1/plans/plan_p1_childmind_piu_v1.md)
- 项目 2 计划书:
  - [plan_p2_childmind_piu_v1.md](/home/er/桌面/MLsystem/00_docs/v1/plans/plan_p2_childmind_piu_v1.md)

### 3.2 NFL Big Data Bowl

- 项目 1 计划书:
  - [plan_p1_nfl_bdb_v1.md](/home/er/桌面/MLsystem/00_docs/v1/plans/plan_p1_nfl_bdb_v1.md)
- 项目 2 计划书:
  - [plan_p2_nfl_bdb_v1.md](/home/er/桌面/MLsystem/00_docs/v1/plans/plan_p2_nfl_bdb_v1.md)

### 3.3 HMS - Harmful Brain Activity Classification

- 项目 1 计划书:
  - [plan_p1_hms_hbac_v1.md](/home/er/桌面/MLsystem/00_docs/v1/plans/plan_p1_hms_hbac_v1.md)
- 项目 2 计划书:
  - [plan_p2_hms_hbac_v1.md](/home/er/桌面/MLsystem/00_docs/v1/plans/plan_p2_hms_hbac_v1.md)

## 4. 使用建议

### 4.1 如果希望两项作业共用一条主线

优先选择:

1. `Child Mind Institute — Problematic Internet Use`

原因:

- 两项作业之间的任务连续性最好
- 既能做系统对比，也能做 MLflow 全流程
- 对当前硬件较友好

### 4.2 如果更重视“机器学习系统”味道

优先组合:

1. 项目 1 选 `Child Mind` 或 `NFL Big Data Bowl`
2. 项目 2 选 `HMS`

原因:

- 项目 1 更强调单机、分布式和深度学习系统的比较
- 项目 2 更强调深度模型、实验管理和模型发布

### 4.3 如果希望项目更有“新颖度 + 展示性”

优先选择:

1. `NFL Big Data Bowl`
2. `HMS`

原因:

- 轨迹预测和 EEG 分类都不属于传统课设题
- 中期和最终汇报表现力较强

## 5. 当前推荐结论

综合课程要求、硬件条件、数据可得性、工程风险和汇报质量，推荐顺序如下:

1. `Child Mind` 同时覆盖项目 1 和项目 2
2. `Child Mind` 做项目 1，`HMS` 做项目 2
3. `NFL Big Data Bowl` 做项目 1，`HMS` 做项目 2

## 6. 参考来源

- 国科大研究生学位论文撰写规范与模板: https://scce.ucas.ac.cn/index.php/en/jxpy/pygl/3333-2022-08-23-12-59-15
- 国科大研究生学位论文撰写指导意见: https://eece.ucas.ac.cn/index.php/zh-cn/2014-06-13-06-47-02/2014-06-13-06-48-14/1535-2018-10-22-02-11-12
- 国科大开题/中期要求说明: https://onestop.ucas.ac.cn/home/info/16edeb59-0332-4c3d-9f11-99b73c6a0ed0
- 国科大人工智能学院开题/中期通知: https://aipt.ucas.ac.cn/index.php/zh-cn/lunwentongzhi/6335-2026
