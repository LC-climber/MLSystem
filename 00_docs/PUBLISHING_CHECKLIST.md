# 发布清单 - P2-7 双渠道模型发布

**创建时间**: 2026-06-08  
**目标完成**: 2026-06-10  
**预计工作量**: 2-3 天

---

## 📋 总体清单

### Phase 1: 模型选定 ✅
- [x] P1 Baseline 确认: sklearn LR (QWK=0.3651)
- [ ] Optuna Champion 选定 (待运行完整优化)
- [ ] 性能对比分析
- [ ] 最终模型决策

### Phase 2: 文件准备 (0/7)
- [ ] 模型权重文件
- [ ] Model Card 生成
- [ ] 推理脚本整理
- [ ] 使用示例代码
- [ ] 可视化图表
- [ ] 依赖文件列表
- [ ] 许可证文件

### Phase 3: ModelScope 发布 (0/6)
- [ ] 注册 ModelScope 账号
- [ ] 创建模型仓库
- [ ] 准备文件结构
- [ ] 上传模型文件 (Git LFS)
- [ ] 配置仓库信息
- [ ] 测试在线推理

### Phase 4: HuggingFace Hub 发布 (0/6)
- [ ] 注册 HuggingFace 账号
- [ ] 创建模型仓库
- [ ] 准备 HF 格式文件
- [ ] 上传模型文件 (Git LFS)
- [ ] 配置 Model Card
- [ ] 测试模型加载

### Phase 5: 验证和文档 (0/5)
- [ ] 测试 ModelScope 推理
- [ ] 测试 HuggingFace 推理
- [ ] 更新项目 README
- [ ] 记录发布链接
- [ ] 撰写发布说明

---

## 📊 进度追踪

| 阶段 | 任务数 | 已完成 | 进度 |
|------|--------|--------|------|
| Phase 1: 模型选定 | 4 | 1 | 25% |
| Phase 2: 文件准备 | 7 | 0 | 0% |
| Phase 3: ModelScope | 6 | 0 | 0% |
| Phase 4: HuggingFace | 6 | 0 | 0% |
| Phase 5: 验证文档 | 5 | 0 | 0% |
| **总计** | **28** | **1** | **4%** |

---

## 🎯 详细任务

### Phase 1: 模型选定

#### 1.1 确认 Baseline ✅
- **状态**: 已完成
- **模型**: sklearn Logistic Regression
- **特征**: feat_v1 (100维)
- **性能**: QWK=0.3651

#### 1.2 Optuna Champion 选定
- **状态**: 待执行
- **依赖**: 完整 100-trial 优化
- **条件**: QWK > 0.4 (超过 baseline)
- **时间**: 后台运行 6-8 小时

#### 1.3 性能对比
- 对比 baseline vs champion
- 分析改进幅度
- 决策发布哪个模型

---

### Phase 2: 文件准备

#### 2.1 模型权重
- [ ] 导出 sklearn 模型: `model.pkl`
- [ ] 或导出 PyTorch 模型: `model.pt`
- [ ] 验证加载正常

#### 2.2 Model Card
- [ ] 使用 `src/mlflow_utils/artifacts.py` 生成
- [ ] 补充完整信息:
  - 模型描述
  - 训练数据
  - 性能指标
  - 使用限制
  - 伦理考虑

#### 2.3 推理脚本
- [ ] 整理 `src/deployment/inference.py`
- [ ] 添加使用说明
- [ ] 测试独立运行

#### 2.4 使用示例
- [ ] 创建 `example.py`
- [ ] 基础用法示例
- [ ] 批量推理示例

#### 2.5 可视化图表
- [ ] 混淆矩阵
- [ ] 特征重要性
- [ ] PR 曲线
- [ ] 训练曲线

#### 2.6 依赖文件
- [ ] 提取最小依赖
- [ ] 指定确切版本
- [ ] 测试安装

#### 2.7 许可证
- [ ] 选择合适的开源许可证 (建议: MIT)
- [ ] 创建 LICENSE 文件

---

### Phase 3: ModelScope 发布

#### 3.1 账号和仓库
- [ ] 注册: https://modelscope.cn
- [ ] 创建仓库: `piu-risk-classifier`
- [ ] 设置可见性: 公开

#### 3.2 文件结构
```
piu-risk-classifier/
├── README.md
├── model.pkl
├── inference.py
├── example.py
├── requirements.txt
├── LICENSE
└── assets/
    └── *.png
```

#### 3.3 Git LFS 设置
```bash
git lfs track "*.pkl"
git lfs track "*.pt"
```

#### 3.4 上传
```bash
git add .
git commit -m "Initial release v1.0.0"
git tag v1.0.0
git push origin main --tags
```

#### 3.5 配置信息
- 任务类型: 多分类
- 框架: PyTorch / scikit-learn
- 标签: mental-health, classification

#### 3.6 测试
- 在线推理测试
- 下载测试
- 示例代码验证

---

### Phase 4: HuggingFace Hub 发布

#### 4.1 账号设置
```bash
pip install huggingface_hub
huggingface-cli login
```

#### 4.2 创建仓库
```bash
huggingface-cli repo create piu-risk-classifier --type model
```

#### 4.3 HF 格式文件
- `config.json` (如果是 PyTorch)
- `pytorch_model.bin` / `model.pkl`
- `README.md` (HF 格式)

#### 4.4 上传
```bash
git clone https://huggingface.co/<username>/piu-risk-classifier
cd piu-risk-classifier
git lfs install
git lfs track "*.bin" "*.pkl"
git add .
git commit -m "Initial release v1.0.0"
git push
```

#### 4.5 Model Card 配置
```yaml
---
language: 
- zh
- en
tags:
- tabular-classification
- mental-health
license: mit
---
```

#### 4.6 测试
```python
from transformers import pipeline
# 或自定义加载方法
```

---

### Phase 5: 验证和文档

#### 5.1 ModelScope 测试
- [ ] 在线推理功能
- [ ] 模型下载
- [ ] API 调用

#### 5.2 HuggingFace 测试
- [ ] 使用 `from_pretrained` 加载
- [ ] 推理测试
- [ ] 文档可读性

#### 5.3 更新项目文档
- [ ] 在 README.md 添加发布链接
- [ ] 更新 PROGRESS.md
- [ ] 记录在 PROJECT_LOG.md

#### 5.4 发布说明
```markdown
## 模型发布

**ModelScope**: https://modelscope.cn/models/xxx/piu-risk-classifier
**HuggingFace**: https://huggingface.co/xxx/piu-risk-classifier

**版本**: v1.0.0
**发布日期**: 2026-06-10
**模型性能**: QWK=0.3651
```

#### 5.5 Demo 准备
- Gradio / Streamlit demo (可选)
- 在线演示链接

---

## ⚠️ 注意事项

### 数据隐私
- ✅ 不上传任何原始数据
- ✅ 不上传个人身份信息
- ✅ 仅上传聚合的模型文件

### 伦理考虑
- ⚠️ 明确标注使用限制
- ⚠️ 说明不应作为唯一诊断依据
- ⚠️ 注明目标人群（青少年）

### 技术要求
- 模型文件 < 2GB (Git LFS 限制)
- README 完整且易读
- 示例代码可直接运行

---

## 📅 时间线

| 日期 | 任务 |
|------|------|
| 2026-06-08 | ✅ 创建发布清单 |
| 2026-06-09 | Phase 2: 文件准备 |
| 2026-06-10 AM | Phase 3: ModelScope 发布 |
| 2026-06-10 PM | Phase 4: HuggingFace 发布 |
| 2026-06-10 EOD | Phase 5: 验证和文档 |

---

**创建者**: Claude Opus 4.8  
**最后更新**: 2026-06-08 19:10  
**预计完成**: 2026-06-10
