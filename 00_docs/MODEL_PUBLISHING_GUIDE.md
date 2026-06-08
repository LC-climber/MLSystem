# 模型发布指南

## 概述

本项目采用**双渠道发布策略**：
1. **ModelScope** (魔搭社区) - 主要发布渠道
2. **HuggingFace Hub** - 国际镜像

---

## 发布准备清单

### 1. 模型文件准备

#### 需要发布的文件
- [ ] 最佳模型权重 (`model.pkl` / `model.pt`)
- [ ] 特征工程脚本 (`inference.py`)
- [ ] Model Card (`MODEL_CARD.md`)
- [ ] 推理示例 (`example.py`)
- [ ] 依赖文件 (`requirements.txt`)
- [ ] 许可证 (`LICENSE`)

#### 模型元数据
- 模型名称: `piu-risk-classifier`
- 任务类型: 多分类 (4类)
- 框架: PyTorch / scikit-learn
- 输入: 表格数据 (可选 actigraphy)
- 输出: PIU 风险等级 (None/Mild/Moderate/Severe)

### 2. Model Card 内容

#### 必需章节
- [ ] 模型描述
- [ ] 预期用途和使用限制
- [ ] 训练数据
- [ ] 训练过程
- [ ] 评估结果
- [ ] 伦理考虑
- [ ] 引用信息

### 3. 代码示例

#### 推理示例代码
```python
# 基础用法
from piu_risk import PiuRiskClassifier

model = PiuRiskClassifier.from_pretrained("piu-risk-classifier")
prediction = model.predict({
    "age": 12.5,
    "sex": 1,
    "bmi": 18.5,
    "cgas_score": 75.0
})
print(f"Risk level: {prediction['label']}")
print(f"Confidence: {prediction['confidence']:.2%}")
```

---

## ModelScope 发布流程

### 1. 注册账号
访问: https://modelscope.cn

### 2. 创建模型仓库
- 仓库名称: `piu-risk-classifier`
- 可见性: 公开
- 任务类型: 多分类
- 框架: PyTorch

### 3. 准备文件结构
```
piu-risk-classifier/
├── README.md                 # Model Card
├── model.pkl                 # 模型权重
├── inference.py              # 推理脚本
├── example.py                # 使用示例
├── requirements.txt          # 依赖
├── LICENSE                   # 许可证
└── assets/
    ├── confusion_matrix.png
    └── feature_importance.png
```

### 4. 上传模型
```bash
# 使用 Git LFS
git lfs install
git clone https://www.modelscope.cn/<username>/piu-risk-classifier.git
cd piu-risk-classifier

# 添加大文件到 LFS
git lfs track "*.pkl"
git lfs track "*.pt"

# 添加文件
git add .
git commit -m "Initial model release v1.0.0"
git tag v1.0.0
git push origin main --tags
```

### 5. 填写模型信息
- 模型简介
- 任务描述
- 使用限制
- 训练数据说明
- 性能指标

---

## HuggingFace Hub 发布流程

### 1. 注册账号
访问: https://huggingface.co

### 2. 创建模型仓库
```bash
# 安装 huggingface_hub
pip install huggingface_hub

# 登录
huggingface-cli login

# 创建仓库
huggingface-cli repo create piu-risk-classifier --type model
```

### 3. 准备文件结构
```
piu-risk-classifier/
├── README.md                 # Model Card (HF format)
├── config.json               # 模型配置
├── pytorch_model.bin         # PyTorch 权重
├── inference.py              # 推理脚本
├── requirements.txt
└── LICENSE
```

### 4. 上传模型
```bash
git clone https://huggingface.co/<username>/piu-risk-classifier
cd piu-risk-classifier

# 使用 Git LFS
git lfs install
git lfs track "*.bin"
git lfs track "*.pkl"

# 添加文件
git add .
git commit -m "Initial release v1.0.0"
git tag v1.0.0
git push origin main --tags
```

### 5. 配置模型卡片
- Tags: `tabular`, `classification`, `mental-health`
- Datasets: `PIU-Dataset`
- Metrics: `cohen-kappa`, `f1-score`
- Languages: `zh`, `en`

---

## Model Card 模板

```markdown
---
language: 
- zh
- en
tags:
- tabular-classification
- mental-health
- piu
- adolescent
license: mit
metrics:
- cohen-kappa
- f1-score
- balanced-accuracy
---

# PIU Risk Classifier

## 模型描述

本模型用于评估青少年的网络成瘾（PIU）风险等级。基于多模态数据（表格数据和活动记录）训练。

## 预期用途

**主要用途**:
- 辅助临床医生进行 PIU 风险筛查
- 研究用途：分析 PIU 相关因素

**不适用场景**:
- 不应作为诊断的唯一依据
- 不适用于成人群体
- 不应用于非医疗决策

## 模型性能

| 指标 | 值 |
|------|-----|
| Cohen's Kappa | 0.365 |
| Macro F1 | 0.362 |
| Balanced Accuracy | 0.404 |

## 训练数据

- 数据集: ABCD Study PIU Dataset
- 样本数: 2,736 (有标签)
- 特征: 100维 (v1) / 145维 (v2)
- 类别分布: None (58%), Mild (27%), Moderate (14%), Severe (1%)

## 使用方法

\`\`\`python
from piu_risk import PiuRiskClassifier

model = PiuRiskClassifier.from_pretrained("piu-risk-classifier")
result = model.predict({
    "age": 12.5,
    "sex": 1,
    "bmi": 18.5
})
\`\`\`

## 限制和偏差

- 模型训练数据来自美国青少年
- 对少数类别（Severe）识别能力有限
- 需要专业人员解读结果

## 引用

\`\`\`bibtex
@software{piu_risk_classifier,
  author = {Your Name},
  title = {PIU Risk Classifier},
  year = {2026},
  url = {https://modelscope.cn/models/piu-risk-classifier}
}
\`\`\`
```

---

## 发布检查清单

### 发布前
- [ ] 选定最佳模型（QWK 最高）
- [ ] 生成 Model Card
- [ ] 准备示例代码
- [ ] 测试推理脚本
- [ ] 准备可视化图表
- [ ] 编写使用文档

### ModelScope
- [ ] 创建仓库
- [ ] 上传模型文件
- [ ] 配置仓库信息
- [ ] 测试在线推理
- [ ] 发布版本 tag

### HuggingFace Hub
- [ ] 创建仓库
- [ ] 上传模型文件
- [ ] 配置 Model Card
- [ ] 测试加载
- [ ] 发布版本 tag

### 发布后
- [ ] 更新项目 README
- [ ] 记录发布链接
- [ ] 准备演示 demo
- [ ] 撰写发布说明

---

## 常见问题

### Q: 如何选择发布哪个模型？
A: 选择 Champion 别名的模型（QWK 最高且经过验证）

### Q: 模型文件太大怎么办？
A: 使用 Git LFS，或考虑模型压缩/量化

### Q: 如何更新已发布的模型？
A: 创建新的 tag (v1.0.1, v1.1.0) 并推送

### Q: 两个平台都要发布吗？
A: 建议都发布，ModelScope 面向国内，HF 面向国际

---

## 参考资源

- [ModelScope 文档](https://modelscope.cn/docs)
- [HuggingFace Hub 文档](https://huggingface.co/docs/hub)
- [Model Card 指南](https://huggingface.co/docs/hub/model-cards)
- [Git LFS 教程](https://git-lfs.github.com/)
