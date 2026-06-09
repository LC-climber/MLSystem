# 项目文档导航

**项目**: MLsystem - PIU Risk Classification  
**版本**: v1.0.0  
**最后更新**: 2026-06-08

---

## 📚 快速导航

### 🚀 快速开始
- [README.md](README.md) - 项目主页
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - 使用示例
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 部署指南

### 📊 项目状态
- [PROJECT_STATUS_REPORT_20260608.md](PROJECT_STATUS_REPORT_20260608.md) - 最新状态
- [00_docs/PROGRESS.md](00_docs/PROGRESS.md) - 进度快照
- [COMPLETION_GUIDE.md](COMPLETION_GUIDE.md) - 完成指南

### 📝 开发文档
- [API_REFERENCE.md](API_REFERENCE.md) - API 参考
- [00_docs/P2_IMPLEMENTATION_PLAN.md](00_docs/P2_IMPLEMENTATION_PLAN.md) - 实施计划
- [00_docs/MODEL_PUBLISHING_GUIDE.md](00_docs/MODEL_PUBLISHING_GUIDE.md) - 发布指南

### 🧪 测试文档
- [TEST_REPORT.md](TEST_REPORT.md) - 测试报告
- [00_docs/TEST_EXECUTION_PLAN.md](00_docs/TEST_EXECUTION_PLAN.md) - 测试计划
- [tests/test_e2e_api.py](tests/test_e2e_api.py) - E2E 测试

### 🚢 发布文档
- [PUBLISHING_READINESS.md](PUBLISHING_READINESS.md) - 发布准备
- [00_docs/CHAMPION_SELECTION_GUIDE.md](00_docs/CHAMPION_SELECTION_GUIDE.md) - Champion 选定
- [00_docs/PUBLISHING_CHECKLIST.md](00_docs/PUBLISHING_CHECKLIST.md) - 发布清单

### 📖 报告文档
- [FINAL_REPORT_OUTLINE.md](FINAL_REPORT_OUTLINE.md) - 最终报告
- [DAILY_SUMMARY_20260608.md](DAILY_SUMMARY_20260608.md) - 每日总结
- [FINAL_WORK_SUMMARY_20260608.md](FINAL_WORK_SUMMARY_20260608.md) - 工作总结

---

## 📂 目录结构

```
MLsystem/
├── 📄 README.md                    # 项目主页
├── 📄 COMPLETION_GUIDE.md         # 完成指南
├── 📄 API_REFERENCE.md            # API 参考
├── 📄 USAGE_EXAMPLES.md           # 使用示例
├── 📄 DEPLOYMENT_GUIDE.md         # 部署指南
├── 📄 TEST_REPORT.md              # 测试报告
├── 📄 PUBLISHING_READINESS.md     # 发布准备
├── 📄 FINAL_REPORT_OUTLINE.md     # 最终报告
│
├── 📁 00_docs/                    # 文档目录
│   ├── PROGRESS.md               # 进度快照
│   ├── PROJECT_LOG.md            # 项目日志
│   ├── NEXT_STEPS.md             # 下一步
│   ├── P2_IMPLEMENTATION_PLAN.md # 实施计划
│   ├── MODEL_PUBLISHING_GUIDE.md # 发布指南
│   ├── CHAMPION_SELECTION_GUIDE.md
│   ├── PUBLISHING_CHECKLIST.md
│   └── TEST_EXECUTION_PLAN.md
│
├── 📁 src/                        # 源代码
│   ├── mlflow_utils/             # MLflow 工具
│   ├── deployment/               # 部署代码
│   ├── experiments/              # 实验脚本
│   ├── models/                   # 模型定义
│   └── data/                     # 数据处理
│
├── 📁 tests/                      # 测试代码
│   └── test_e2e_api.py           # E2E 测试
│
├── 📁 scripts/                    # 工具脚本
│   ├── verify_system.py          # 系统验证
│   ├── quick_check.py            # 快速检查
│   ├── export_model.py           # 模型导出
│   └── register_baseline.py      # Baseline 注册
│
├── 📁 docker/                     # Docker 配置
│   ├── Dockerfile.infer          # 推理镜像
│   ├── Dockerfile.train          # 训练镜像
│   ├── docker-compose.yml        # 编排配置
│   └── test_docker.sh            # Docker 测试
│
└── 📁 SESSION*_SUMMARY.md         # 会话记录
```

---

## 🎯 按任务查找

### 我想部署系统
1. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 完整部署指南
2. [docker/docker-compose.yml](docker/docker-compose.yml) - 配置文件
3. [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - 使用示例

### 我想运行测试
1. [TEST_REPORT.md](TEST_REPORT.md) - 测试报告
2. [tests/test_e2e_api.py](tests/test_e2e_api.py) - E2E 测试
3. [docker/test_docker.sh](docker/test_docker.sh) - Docker 测试

### 我想发布模型
1. [PUBLISHING_READINESS.md](PUBLISHING_READINESS.md) - 发布准备
2. [00_docs/MODEL_PUBLISHING_GUIDE.md](00_docs/MODEL_PUBLISHING_GUIDE.md) - 发布指南
3. [scripts/export_model.py](scripts/export_model.py) - 导出工具

### 我想了解 API
1. [API_REFERENCE.md](API_REFERENCE.md) - API 参考
2. [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - 使用示例
3. [src/deployment/fastapi_app.py](src/deployment/fastapi_app.py) - API 实现

### 我想查看进度
1. [PROJECT_STATUS_REPORT_20260608.md](PROJECT_STATUS_REPORT_20260608.md) - 项目状态
2. [00_docs/PROGRESS.md](00_docs/PROGRESS.md) - 进度快照
3. [COMPLETION_GUIDE.md](COMPLETION_GUIDE.md) - 完成指南

---

## 📋 会话记录

**15 次会话完整记录**:
- [SESSION1-3_SUMMARY.md](SESSION1-3_SUMMARY.md) - 基础设施搭建
- [SESSION4_SUMMARY.md](SESSION4_SUMMARY.md) - Optuna 测试
- [SESSION5-6_SUMMARY.md](SESSION5-6_SUMMARY.md) - FastAPI + Docker
- [SESSION7_SUMMARY.md](SESSION7_SUMMARY.md) - 特征工程（50%里程碑）
- [SESSION8_SUMMARY.md](SESSION8_SUMMARY.md) - 模型发布准备
- [SESSION9_SUMMARY.md](SESSION9_SUMMARY.md) - E2E测试（57%）
- [SESSION10_SUMMARY.md](SESSION10_SUMMARY.md) - Baseline（60%里程碑）
- [SESSION11_SUMMARY.md](SESSION11_SUMMARY.md) - 系统验证（63%）
- [SESSION12_SUMMARY.md](SESSION12_SUMMARY.md) - 验证分析（65%）
- [SESSION13_SUMMARY.md](SESSION13_SUMMARY.md) - 工具完善（70%里程碑）
- [SESSION14_SUMMARY.md](SESSION14_SUMMARY.md) - 导出工具
- [SESSION15_SUMMARY.md](SESSION15_SUMMARY.md) - 文档完善（78%）

---

## 🔍 关键文件

### 配置文件
- `src/config.py` - 项目配置
- `docker/docker-compose.yml` - Docker 编排
- `.dockerignore` - Docker 忽略

### 核心代码
- `src/mlflow_utils/tracking.py` - MLflow 追踪
- `src/mlflow_utils/registry.py` - 模型注册
- `src/deployment/fastapi_app.py` - API 服务
- `src/deployment/inference.py` - 特征工程

### 测试代码
- `tests/test_e2e_api.py` - E2E 测试
- `docker/test_docker.sh` - Docker 测试
- `scripts/verify_system.py` - 系统验证
- `scripts/quick_check.py` - 快速检查

---

## 📈 项目指标

- **代码行数**: 4,250+
- **文档行数**: 8,550+
- **测试覆盖**: E2E + Docker
- **项目健康度**: 5.0/5.0
- **完成进度**: 78%

---

## 🆘 获取帮助

### 遇到问题？
1. 查看 [TEST_REPORT.md](TEST_REPORT.md) 的故障排查部分
2. 查看 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) 的常见问题
3. 查看项目 [Issues](https://github.com/LC-climber/MLSystem/issues)

### 联系方式
- GitHub: https://github.com/LC-climber/MLSystem
- 文档: 项目 00_docs/ 目录

---

**版本**: 1.0.0  
**最后更新**: 2026-06-08 21:10
