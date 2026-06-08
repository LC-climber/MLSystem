# 下一步立即行动清单

**更新时间**: 2026-06-08
**当前阶段**: P2 阶段 1 完成，准备启动阶段 2

---

## 🎯 推荐执行路径：方案 2（快速推进）

### ✅ Step 1: 环境确认

```bash
# 激活环境
conda activate openpi_311

# 确认 MLflow 运行
curl http://localhost:5000/health
# 如未运行，执行: bash scripts/start_mlflow.sh &
```

### ⏳ Step 2: Optuna 小规模测试（10 trials）

```bash
# 创建日志目录
mkdir -p logs

# 运行 10 trials 测试（3-fold CV，约 30-60 分钟）
python -m src.experiments.run_p2_optuna \
  --feature v2 \
  --trials 10 \
  --study-name test-optuna \
  --folds 3
```

**预期结果**: 10 个 trials 完成，产生 best trial

### ⏳ Step 3: 查看结果并注册 baseline

```bash
# 查看 Optuna 结果
python -c "
import optuna
study = optuna.load_study('test-optuna', storage='sqlite:///optuna.db')
print(f'Best trial: {study.best_trial.number}')
print(f'Best QWK: {study.best_value:.4f}')
print(f'Best params: {study.best_trial.params}')
"

# 从 MLflow UI 找到 best trial 对应的 run_id
# 访问 http://localhost:5000 → piu-p2-mlops experiment
# 按 val_qwk_mean 排序，复制最佳 run 的 ID

# 注册为 baseline
python -c "
from src.mlflow_utils.registry import register_model
register_model(
    run_id='<best_run_id>',  # 替换为实际 run_id
    model_name='piu-risk',
    alias='baseline',
    description='Initial baseline from 10-trial Optuna test',
    tags={'phase': 'p2', 'source': 'optuna_test'}
)
"

# 验证
python -c "
from src.mlflow_utils.registry import get_model_by_alias
model = get_model_by_alias('piu-risk', 'baseline')
print('✓ Baseline model loaded successfully')
"
```

### ⏳ Step 4: 启动完整 Optuna 优化（100 trials）

```bash
# 后台运行（预计 4-6 小时）
nohup python -m src.experiments.run_p2_optuna \
  --feature v2 \
  --trials 100 \
  --study-name piu-mlp-v2 \
  --folds 5 \
  > logs/optuna_v2_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# 记录进程 ID
echo $! > logs/optuna_pid.txt

# 监控进度
tail -f logs/optuna_v2_*.log

# 或者使用 Optuna Dashboard
# pip install optuna-dashboard
# optuna-dashboard sqlite:///optuna.db --port 8080
```

### ⏳ Step 5: 选定 champion（Optuna 完成后）

```bash
# 查看最终结果
python -c "
import optuna
study = optuna.load_study('piu-mlp-v2', storage='sqlite:///optuna.db')
print(f'Completed trials: {len(study.trials)}')
print(f'Best trial: {study.best_trial.number}')
print(f'Best QWK: {study.best_value:.4f}')
print(f'Best params:')
for key, value in study.best_trial.params.items():
    print(f'  {key}: {value}')
"

# 从 MLflow 找到 best trial 的 run_id，注册为 champion
python -c "
from src.mlflow_utils.registry import register_model
register_model(
    run_id='<best_run_id>',
    model_name='piu-risk',
    alias='champion',
    description='Best model from 100-trial Optuna optimization',
    tags={'phase': 'p2', 'source': 'optuna_full', 'trials': '100'}
)
"
```

---

## 📅 时间预算

| 步骤 | 预计时间 | 可并行 |
|------|----------|--------|
| Step 1: 环境确认 | 5 分钟 | - |
| Step 2: 10 trials 测试 | 30-60 分钟 | - |
| Step 3: 注册 baseline | 10 分钟 | - |
| Step 4: 100 trials 完整优化 | 4-6 小时 | ✅ 后台运行 |
| Step 5: 选定 champion | 15 分钟 | - |

**今天可完成**: Step 1-3 + 启动 Step 4
**明天查看**: Step 4 结果 + Step 5

---

## 🔄 进度追踪

- [ ] Step 1: 环境确认 ✅
- [ ] Step 2: 10 trials 测试完成
- [ ] Step 3: baseline 注册成功
- [ ] Step 4: 100 trials 启动（后台）
- [ ] Step 5: champion 选定

---

## 🆘 故障排查

### 问题 1: Optuna 报错 "cannot import module"
```bash
# 确认当前目录
pwd  # 应该在 /home/er/桌面/MLsystem

# 确认环境
which python  # 应该在 openpi_311 环境

# 确认模块可导入
python -c "from src.experiments.run_p2_optuna import main; print('✓ Import OK')"
```

### 问题 2: GPU OOM
```bash
# 减少 batch size 或使用 CPU
# 修改 run_p2_optuna.py 中 device 参数为 "cpu"
```

### 问题 3: MLflow 连接失败
```bash
# 检查 MLflow server
curl http://localhost:5000/health

# 重启
pkill -f "mlflow server"
bash scripts/start_mlflow.sh &
```

---

**当前状态**: P2 阶段 1 完成，工具包就绪
**下一里程碑**: 完成 Optuna 优化，选定 champion 模型
