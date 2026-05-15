# 项目 2 优化版方案 — 基于 MLflow 的 PIU MLOps 实践与双渠道发布 v2

- 项目编号: `MLSYS-2026S-P2-MLOPS-PIU`
- 课程名称: `机器学习系统`
- 对应作业: `项目实践及演示汇报-2`
- 项目题目: `基于 MLflow 的青少年问题性互联网使用风险识别 MLOps 实践与模型发布`
- 数据来源: `Kaggle Child Mind Institute — Problematic Internet Use`
- 原版本: `00_docs/v1/plans/plan_p2_childmind_piu_v1.md`(2026-04-16)
- 文档版本: `v2`
- 日期: `2026-04-18`
- 团队成员: A / B / C(姓名待填)
- 指导教师: `待填写`

## 0. 相对 v1 的改动点

| # | v1 | v2 | 原因 |
|---|---|---|---|
| 1 | MLOps 深度只到 `MLflow + ModelScope` 两件事 | 扩展 6 件套: `MLflow + DVC/git-lfs + Dockerfile + FastAPI + Makefile + ModelScope/HF 双发布` | 答辩时 MLOps 完整度是一个关键加分项,v1 不够 |
| 2 | 发布只 ModelScope | **ModelScope 主 + HuggingFace Hub 镜像**,互为 fallback 并在报告中横向对比两家开发者体验 | MLOps 深度 + 国际可见度 + 降低国内网络风险 |
| 3 | 指标主未锁定 | 主 **QWK**(Kaggle 官方),辅 Macro-F1 / Log Loss | 对齐 Kaggle 官方标准,答辩有标尺 |
| 4 | 缺容器化、推理服务、CI | 加 Dockerfile(CPU 推理 / GPU 训练两镜像)+ FastAPI `/predict` + Makefile 驱动全流程 | "可发布"要名副其实 |
| 5 | 缺模型 card 模板 | 给出 `model_card.md` 模板,含许可、使用示例、局限 | ModelScope/HF Hub 都需要 |
| 6 | 实验矩阵只到名字 | 明确 baseline / enhanced / advanced 三层,且每层给 "触达条件" | 可按资源裁剪 |
| 7 | 超参搜索只提"调参" | Optuna 100-200 trials,定义 search space | 可复现 |
| 8 | 无推理服务 demo | FastAPI `/predict` + sample input + curl 示例 | 现场演示可用 |

## 1. 摘要

本项目基于 Kaggle `Child Mind Institute — Problematic Internet Use` 数据,构建一条**完整的 MLOps 工程闭环**:从原始数据下载到最终模型双渠道发布。项目以 `MLflow` 作为实验管理核心,引入 `DVC/git-lfs` 管数据版本、`Optuna` 做超参搜索、`Dockerfile` 做环境封装、`FastAPI` 做轻量推理服务、`Makefile` 串起数据→特征→训练→评估→注册→发布全链路。最终最佳模型在 `ModelScope` 发布为主仓库,同步到 `HuggingFace Hub` 作为镜像,以报告形式横向对比两家平台在模型发布工作流上的开发者体验。

**关键词**: `MLflow`、`MLOps`、`DVC`、`Docker`、`FastAPI`、`ModelScope`、`HuggingFace Hub`、`PIU`

## 1.1 本项目的"MLOps 完整度"自评

相比一般课程项目,本方案覆盖以下环节(v1 打勾✓项为改进):

- [x] 数据版本(DVC 或 git-lfs + hash)✓
- [x] 特征版本(feat_v1 / v2 / v3)
- [x] 代码版本(git + conventional commits + tags)✓
- [x] 环境版本(`requirements-pinned.txt` + `environment.yml`)✓
- [x] 实验追踪(MLflow Tracking)
- [x] Artifact 管理(MLflow Artifacts)
- [x] 模型注册(MLflow Model Registry,4 个别名)
- [x] 超参数优化(Optuna)
- [x] 容器化(Dockerfile × 2)✓
- [x] 推理服务(FastAPI)✓
- [x] 可复现实验入口(Makefile)✓
- [x] 双渠道发布(ModelScope + HF Hub)✓
- [ ] 持续集成(可选,时间富余时做 GitHub Actions 回归脚本)
- [ ] 在线监控(超出课程范围,不做)

## 2. 研究背景与意义

项目 2 的考察核心不是"模型谁更高",而是"一个机器学习工程师在真实项目里怎么把'模型'变成'可交付产品'"。PIU 任务的多模态、缺失、不平衡特性,让 MLOps 的每一个环节都有展示空间:

- 数据异构 → 需要 **数据版本**(DVC)锁定每次实验的输入分布
- actigraphy 覆盖不均 → 需要 **特征版本** 显式标注"有/无 biosensing"
- 缺失值策略敏感 → 需要 **实验追踪** 记录每种 imputer 的结果
- 模型多层次 → 需要 **Registry 别名体系** 管理 baseline/candidate/champion/demo
- 结果需复现与移交 → 需要 **Docker + FastAPI** 提供"可下载即可运行"的最小发布

## 3. 项目目标

1. 建立数据版本 + 特征版本 + 模型版本 + 代码版本四级版本矩阵
2. 使用 `MLflow` 完整追踪至少 **40 次 runs**(baseline × 5 + 中等 × 15 + 融合 × 20)
3. 实现 `Optuna` 在至少 1 个关键模型上做 **100 次** 超参搜索
4. 输出 `champion` 模型,QWK ≥ baseline + 0.05
5. 交付 Dockerfile(CPU 推理镜像 / GPU 训练镜像)
6. 交付 FastAPI `/predict` 服务 + sample input + curl demo
7. 在 **ModelScope 主 + HuggingFace Hub 镜像** 两处完成发布,含完整 model_card

## 4. 研究内容

### 4.1 数据工程

- 原始数据: `data/raw/`,DVC track 或 git-lfs
- 清洗后数据: `data/interim/`(缺失标记、类型转换)
- 特征矩阵: `data/processed/feat_v{1,2,3}.parquet`
- 所有数据版本打 MLflow tag: `data_version=raw@<hash>`,`feat_version=v2`

### 4.2 特征工程

- 数值: z-score 或 robust scaler
- 类别: one-hot 或 target encoding(train 上 fit,valid/test 上 transform)
- 时序: actigraphy 滑窗(30s 窗口,50% overlap)→ 统计(mean/std/p25/p50/p75/energy)→ 日内/夜间聚合
- 融合(v3): v2 统计 + actigraphy 窗口级 1D CNN 特征 embedding (dim=64)

### 4.3 模型层次(三层实验矩阵)

#### Level 1 — Baseline(全员必做)

- `Logistic Regression` (feat_v1)
- `MLP` (feat_v1)
- `CatBoost` / `LightGBM`(feat_v1)
- 主要目的: 建立 QWK/Macro-F1 下限

#### Level 2 — Enhanced(主力产出层)

- `MLP` (feat_v2)
- `1D CNN on actigraphy 窗口`(单分支)
- `TabTransformer` 或 `FT-Transformer`(feat_v2,可选)

#### Level 3 — Advanced(若时间/VRAM 允许)

- `Late-fusion 双分支`: (tabular branch MLP) ⊕ (actigraphy branch 1D CNN) → concat → MLP head
- `Light Transformer`(feat_v2,4 layer × 8 head,≤10M 参数)

### 4.4 超参数优化

- 工具: `Optuna` 3.x
- 对象: Level 2 最佳 2 个模型 + Level 3 融合模型
- 搜索空间示例(MLP on feat_v2):
  - `hidden_dim_1 ∈ [64, 128, 256, 512]`
  - `hidden_dim_2 ∈ [32, 64, 128, 256]`
  - `dropout ∈ [0.0, 0.1, 0.2, 0.3, 0.5]`
  - `lr ∈ log_uniform(1e-4, 1e-2)`
  - `weight_decay ∈ log_uniform(1e-6, 1e-3)`
  - `batch_size ∈ [64, 128, 256, 512]`
- Trials: 100(融合模型可做 50,受 VRAM 与时间限制)
- Pruner: `MedianPruner`
- 所有 trials 记录到 MLflow

## 5. 技术路线

```
[Kaggle 数据] --DVC/git-lfs--> [data/raw]
      ↓ preprocess (Makefile: make data)
[data/interim, data/processed/feat_v*] --MLflow tag--> data_version, feat_version
      ↓ train (Makefile: make train MODEL=...)
[Optuna trials] --record--> [MLflow runs]
      ↓ select
[MLflow Model Registry]
      ├── baseline    (best Level 1)
      ├── candidate   (Level 2/3 候选)
      ├── champion    (Optuna 扫完后最佳,带 metadata)
      └── demo        (答辩现场演示用,轻量化)
      ↓ docker build
[image: piu-train-gpu:v1]  [image: piu-infer-cpu:v1]
      ↓ deploy
[FastAPI /predict] -- uvicorn 启动 --> http://localhost:8000/predict
      ↓ publish
[ModelScope 主仓] + [HuggingFace Hub 镜像] --+ model_card.md + sample_input + README
```

## 6. MLflow 设计

### 6.1 Tracking Server

- `mlflow server --backend-store-uri sqlite:///mlruns.db --default-artifact-root ./mlruns_artifacts --host 0.0.0.0 --port 5000`
- 本地启动,组员 SSH tunnel 访问

### 6.2 每个 run 必记字段

- params: `model_name / feat_version / data_version / seed / optimizer / lr / bs / epochs / class_weight_policy / imputer`
- metrics: `val_qwk / val_macro_f1 / val_logloss / train_time_s / n_params / model_size_mb / val_rss_peak_gb`
- tags: `owner / phase (baseline|enhanced|advanced) / is_final_candidate / git_sha / device (cpu|5060ti|4090)`

### 6.3 Artifacts

- `confusion_matrix.png`
- `pr_curve.png`
- `training_curve.png`
- `feature_importance.png`(若模型支持)
- `model/`(MLflow pyfunc flavor)
- `inference.py`(最小推理脚本)
- `input_example.json`

### 6.4 Registry 别名

| 别名 | 含义 | 变更频率 |
|---|---|---|
| `baseline` | 项目最早 tabular MLP 的最佳 | 锁定,不再变 |
| `candidate` | 当前训练阶段最新最佳 | 每次 Optuna 完成后更新 |
| `champion` | 正式发布用最佳 | W7 确定后冻结 |
| `demo` | 现场演示用的轻量版(model size <10MB) | W8 确定 |

## 7. 容器化

### 7.1 两镜像策略

- `piu-infer-cpu:v1`(答辩演示、发布仓库推荐)
  - base: `python:3.11-slim`
  - 装 torch CPU wheel + mlflow(本项目推理不吃 GPU 也足够快)
  - copy FastAPI app + champion weights
  - 镜像大小目标 <1.5 GB
- `piu-train-gpu:v1`(训练/复现用)
  - base: `nvcr.io/nvidia/pytorch:25.03-py3` 或自建 `nvidia/cuda:12.8.1-cudnn9-runtime-ubuntu22.04`
  - 装 torch 2.11+cu128 + mlflow + optuna + pyspark
  - 通过 `docker run --gpus all` 训练

### 7.2 Dockerfile 规约

- 使用多阶段构建(只拷 artifact,不带 src 中间件)
- 层顺序: 依赖层在前,代码层在后,提高 cache 命中率
- 不 hardcode 密钥(ModelScope/HF token 走 env var)

## 8. 推理服务 FastAPI

### 8.1 接口设计

```
POST /predict
Content-Type: application/json

{
  "tabular": {"age": 12, "bmi": 18.5, "iat_q1": 3, ...},
  "actigraphy_stats": {"day_mean": 0.12, "night_mean": 0.05, ...}  // 可选
}

200 OK
{
  "model_version": "champion",
  "sii_prediction": 1,
  "sii_label": "mild_impairment",
  "confidence": 0.62,
  "probas": [0.05, 0.62, 0.28, 0.05]
}
```

### 8.2 启动

```
docker run -p 8000:8000 piu-infer-cpu:v1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 8.3 演示用例

- 现场答辩 curl 调用 → 返回结果
- Python 客户端示例(放 README)

## 9. 双渠道发布

### 9.1 ModelScope(主仓)

仓库名建议: `Child-Mind-PIU-Risk-Identifier`
- 必交文件:
  - `configuration.json`(custom pipeline 描述)
  - `pytorch_model.bin`(或 `model.safetensors`)
  - `preprocessor_config.json`(tabular imputer/scaler 参数)
  - `README.md`(model_card)
  - `inference.py`(最小推理)
  - `sample_input.json` / `sample_output.json`
- custom pipeline 类: `PiuRiskIdentifier(Pipeline)`,实现 `preprocess / forward / postprocess`

### 9.2 HuggingFace Hub(镜像)

仓库名: `<user>/piu-risk-identifier`
- 优势: 国际可见度高、`transformers` 生态通用、支持 `inference API` 测试
- 文件结构: 同 ModelScope,但 `configuration.json` 改为 `config.json`(HF 风格)
- 发布: `huggingface-cli login` → `huggingface-cli upload`

### 9.3 两家平台对比(写入最终报告)

| 维度 | ModelScope | HuggingFace Hub |
|---|---|---|
| 国内访问稳定性 | 优 | 一般(HTTPS 偶发) |
| 国际可见度 | 中 | 优 |
| 自定义 Pipeline 模板 | `Pipeline` 抽象 | `transformers` 的 `AutoModel` + `AutoTokenizer` |
| CLI 成熟度 | modelscope CLI | huggingface_hub CLI |
| 非文本/非图像任务 | 需 custom pipeline | 需 custom pipeline |
| LFS 支持 | 有 | 有 |
| 私有仓 | 支持 | 支持 |

把"两家发布各自踩的坑"也写进报告,本身就是 MLOps 工程经验的展示。

### 9.4 model_card.md 模板(附录)

```markdown
---
license: cc-by-4.0
task: classification
tags: [healthcare, behavioral-health, adolescent, multi-modal]
metrics:
  - quadratic-weighted-kappa
datasets:
  - child-mind-institute/problematic-internet-use
---

# Child Mind PIU Risk Identifier v1.0

## 模型简介
本模型基于 Kaggle Child Mind Institute 竞赛数据训练,用于预测青少年问题性互联网使用(PIU)的严重程度指数(SII,4 级有序)。

## 输入
- tabular: 26 个健康与问卷特征(见 `preprocessor_config.json`)
- actigraphy_stats: 可选,12 个 actigraphy 滑窗聚合特征

## 输出
- SII 类别(0-3)
- 类别概率

## 训练数据
- 来源: Kaggle CMI-PIU 训练集
- 切分: StratifiedGroupKFold(K=5, group=participant_id, seed=42)
- 训练规模: ~2400 参与者

## 评估
- 5-fold CV QWK: 0.XX ± 0.YY(填写)
- Macro-F1: 0.XX ± 0.YY

## 局限与风险
- 训练数据仅来自 HBN 项目人群,泛化到其他地区需重训
- 不应用于临床诊断;仅供研究

## 使用
见 `inference.py` 与 `sample_input.json`。

## 许可
数据: 遵从 HBN 数据使用协议
代码: CC-BY-4.0
```

## 10. 实验设计

### 10.1 数据版本设计

- `data_v1`: 原始 Kaggle 下载,md5 记录
- `data_v2`: `v1` + 合并 actigraphy → 主 dataframe
- `data_v3`: `v2` + 增强(随机 mask、轻微扰动,仅训练集)

### 10.2 特征版本设计

同 P1 的 `feat_v1/v2/v3`(此处复用)

### 10.3 训练设计

- 每个 Level 的模型跑 5-fold CV(seed 固定)
- 每个 fold 的 best epoch model 保存为 artifact
- 5-fold 结果聚合(均值 ± std)作为该实验的代表指标

### 10.4 指标体系

- 主指标: `QWK`
- 辅指标: `Macro-F1`、`Log Loss`
- 系统辅: 训练耗时 / 推理吞吐 / 参数量 / 模型大小 / 推理延迟
- 校准指标: ECE(Expected Calibration Error,只对 champion 做)

### 10.5 误差分析

- 对 champion model 做:
  - 混淆矩阵(5-fold 平均)
  - 按年龄段、性别分层性能
  - 失败案例采样(取 20 个预测错最严重的,列在报告附录)
  - 特征重要性(SHAP,仅对 CatBoost)

## 11. 资源条件

- 本地 `mlsys_cpu`: 数据处理 + baseline
- 本地 `mlsys_gpu_local`(5060 Ti): 开发调试、MLflow server host、本地 FastAPI 测试
- 远程 `mlsys_gpu_remote`(4090): Optuna 主力,融合模型训练,Level 3 实验

大致分配(W5-W8):

- 4090 约 40 小时(Optuna 100 trials × 20 分钟 + 融合模型训练 × 10 小时)
- 5060 Ti 约 20 小时(调试 + 小批实验)

## 12. 多场景实施方案

### 12.1 方案 A — 标准多模态 + 双发布(推荐)

DoD:
- Level 1+2+3 全部完成
- Optuna 100 trials
- 双发布完成
- FastAPI + Docker

### 12.2 方案 B — Level 2 为主 + 单发布

触发: 远程 4090 可用时间不足 20 小时

DoD:
- Level 1+2 完成,Level 3 选 1 个做最佳 effort
- Optuna 50 trials
- 只发布到 ModelScope,HF 仅文字说明
- Docker + FastAPI 保留

### 12.3 方案 C — 稳健发布为主

触发: 数据/资源严重受限

DoD:
- Level 1 完成
- 以 CatBoost 或 MLP 最佳版本作 champion
- 强调 MLOps 闭环完整性(Docker + FastAPI + 双发布都做)
- QWK 可能不如 A,但"可发布性"是满分

## 13. 进度安排

| 周 | 成员 A | 成员 B | 成员 C |
|---|---|---|---|
| W5 | 配合 C 接入 MLflow 记录 P1 的 baseline | PyTorch baseline + 1D CNN 迁入 MLflow | MLflow server + DVC + Registry 规约文档 |
| W6 | feat_v3 融合特征构建 | Optuna 100 trials(MLP/1D CNN)+ Level 3 融合模型 | Optuna artifact 管理 / Registry 打标 |
| W7 | 最终报告 P2 数据/特征章节 | champion 训练定稿 | Dockerfile × 2 + ModelScope 主仓 + HF 镜像 |
| W8 | 误差分析 + SHAP 可视化 | 轻量化 demo 模型 | FastAPI + curl demo + 端到端验证 |
| W9 | 最终报告定稿 | 答辩演示支持 | 答辩 PPT MLOps 章节定稿 |

## 14. 预期成果

- MLflow 数据库(`mlruns.db`)含 ≥40 runs
- Registry 4 个别名齐备
- `Dockerfile.infer` + `Dockerfile.train`
- `docker-compose.yml`(可选,本地 demo 用)
- FastAPI app(`app/main.py`)
- `Makefile`(`make data|features|train|eval|register|release|serve`)
- ModelScope 仓库 URL
- HuggingFace Hub 仓库 URL
- 书面报告 P2 部分(含两家平台开发者体验对比章节)
- 最终答辩 PPT MLOps 部分

## 15. 风险与应对(P2 专属)

| # | 风险 | 应对 |
|---|---|---|
| P2-R1 | Optuna 100 trials 超出 4090 窗口 | 降级至 50 trials + 早停(MedianPruner) |
| P2-R2 | ModelScope custom pipeline 未走通 | 先发 HF Hub(更熟的 API),ModelScope 延后 1 周 |
| P2-R3 | champion QWK 较 baseline 提升 <0.03 | 增加 actigraphy 覆盖的子集实验;或用 ensemble(top-3 融合)作为 champion |
| P2-R4 | FastAPI `/predict` 在 Docker 内起不来 | 先本地 python 运行,再 docker 化;容器健康检查加 `/health` endpoint |
| P2-R5 | model_card 写不到位被 hub 拒 | 用 HF Hub 的 `CC-BY-4.0` / ModelScope "Apache-2.0" 已有模板参考 |

## 16. 参考资料

- Kaggle PIU: https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use
- MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
- MLflow pyfunc flavor: https://mlflow.org/docs/latest/models.html#python-function-python-function
- Optuna: https://optuna.readthedocs.io/en/stable/
- DVC: https://dvc.org/doc
- ModelScope 快速开始: https://www.modelscope.cn/docs
- ModelScope custom pipeline: https://modelscope.cn/docs/
- HuggingFace Hub 上传: https://huggingface.co/docs/hub/repositories-getting-started
- FastAPI: https://fastapi.tiangolo.com/
- Docker 多阶段构建: https://docs.docker.com/build/building/multi-stage/

## 17. 修订记录

- `v2 | 2026-04-18`: 大幅扩展 MLOps 深度从 "MLflow+ModelScope" 到 6 件套;锁 QWK 主指标;加 Optuna / Dockerfile / FastAPI / model_card 模板 / 双渠道发布;给每方案 done 标准;新增两家平台对比章节。
