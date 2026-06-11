#!/usr/bin/env python3
"""导出 P2 报告文件（从 Optuna DB 和 MLflow）"""
import sqlite3
import pandas as pd
from pathlib import Path
import json

# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent
OPTUNA_DB = PROJECT_ROOT / "src" / "optuna.db"
REPORTS_P2 = PROJECT_ROOT / "reports" / "P2"
MLRUNS_DIR = PROJECT_ROOT / "mlruns"

REPORTS_P2.mkdir(parents=True, exist_ok=True)

print("📊 开始导出 P2 报告...")

# 1. 导出 Optuna trials
if OPTUNA_DB.exists():
    print(f"\n1️⃣ 导出 Optuna trials from {OPTUNA_DB}")
    conn = sqlite3.connect(OPTUNA_DB)

    # 获取所有 trials
    trials_df = pd.read_sql_query("""
        SELECT t.trial_id, t.number, t.state,
               t.datetime_start, t.datetime_complete,
               tv.value
        FROM trials t
        LEFT JOIN trial_values tv ON t.trial_id = tv.trial_id
        ORDER BY t.number
    """, conn)

    # 获取 trial 参数
    params_df = pd.read_sql_query("""
        SELECT trial_id, param_name, param_value
        FROM trial_params
    """, conn)

    conn.close()

    # 合并参数到 trials
    if len(params_df) > 0:
        params_pivot = params_df.pivot(index='trial_id', columns='param_name', values='param_value')
        trials_full = trials_df.merge(params_pivot, left_on='trial_id', right_index=True, how='left')
    else:
        trials_full = trials_df

    # 保存完整 trials
    output_file = REPORTS_P2 / "p2_optuna_trials.csv"
    trials_full.to_csv(output_file, index=False)
    print(f"   ✅ 保存 {len(trials_full)} 个 trials -> {output_file.name}")

    # 生成最佳 trial 报告
    if len(trials_full) > 0:
        best_trials = trials_full[trials_full['state'] == 'COMPLETE'].nlargest(5, 'value')
        best_md = REPORTS_P2 / "p2_optuna_best_trials.md"

        with open(best_md, 'w') as f:
            f.write("# P2 Optuna 最佳 Trials\n\n")
            f.write(f"**总 Trials**: {len(trials_full)}\n")
            f.write(f"**完成**: {len(trials_full[trials_full['state']=='COMPLETE'])}\n")
            f.write(f"**最佳 QWK**: {trials_full['value'].max():.4f}\n\n")
            f.write("## Top 5 Trials\n\n")
            f.write(best_trials.to_markdown(index=False))

        print(f"   ✅ 保存最佳 trials 报告 -> {best_md.name}")
else:
    print(f"\n⚠️  未找到 Optuna DB: {OPTUNA_DB}")

# 2. 导出 MLflow 实验摘要
mlflow_meta = MLRUNS_DIR / ".trash"
if MLRUNS_DIR.exists():
    print(f"\n2️⃣ 扫描 MLflow runs from {MLRUNS_DIR}")

    runs = []
    for exp_dir in MLRUNS_DIR.iterdir():
        if exp_dir.is_dir() and not exp_dir.name.startswith('.'):
            for run_dir in exp_dir.iterdir():
                if run_dir.is_dir() and not run_dir.name.startswith('.'):
                    meta_file = run_dir / "meta.yaml"
                    if meta_file.exists():
                        runs.append({
                            'experiment': exp_dir.name,
                            'run_id': run_dir.name[:8],
                            'path': str(run_dir.relative_to(PROJECT_ROOT))
                        })

    if runs:
        mlflow_df = pd.DataFrame(runs)
        output_file = REPORTS_P2 / "p2_mlflow_runs_summary.csv"
        mlflow_df.to_csv(output_file, index=False)
        print(f"   ✅ 保存 {len(runs)} 个 MLflow runs -> {output_file.name}")
else:
    print(f"\n⚠️  未找到 MLflow 目录: {MLRUNS_DIR}")

# 3. 生成 P2 总结报告
summary_md = REPORTS_P2 / "p2_summary_report.md"
with open(summary_md, 'w') as f:
    f.write("# P2 MLOps 实践总结报告\n\n")
    f.write("**生成时间**: 2026-06-11\n\n")
    f.write("## 数据来源\n\n")

    if OPTUNA_DB.exists():
        f.write(f"- ✅ Optuna DB: `{OPTUNA_DB.relative_to(PROJECT_ROOT)}`\n")
        f.write(f"  - Trials 数量: {len(trials_full)}\n")
        f.write(f"  - 最佳 QWK: {trials_full['value'].max():.4f}\n")
    else:
        f.write(f"- ❌ Optuna DB 未找到\n")

    if MLRUNS_DIR.exists():
        f.write(f"- ✅ MLflow: `{MLRUNS_DIR.relative_to(PROJECT_ROOT)}`\n")
        f.write(f"  - Runs 数量: {len(runs)}\n")
    else:
        f.write(f"- ❌ MLflow 目录未找到\n")

    f.write("\n## 已完成的 P2 组件\n\n")
    f.write("- ✅ MLflow 深度集成（tracking, registry, model_card, visualizations）\n")
    f.write("- ✅ Optuna 超参数优化框架\n")
    f.write("- ✅ FastAPI 推理服务（5个端点）\n")
    f.write("- ✅ Docker 容器化部署（推理+训练镜像）\n")
    f.write("- ✅ 模型发布指南（双渠道）\n")

    f.write("\n## 生成的报告文件\n\n")
    f.write("- `p2_optuna_trials.csv` - 完整的 Optuna trials 数据\n")
    f.write("- `p2_optuna_best_trials.md` - Top 5 最佳 trials\n")
    f.write("- `p2_mlflow_runs_summary.csv` - MLflow runs 摘要\n")
    f.write("- `p2_summary_report.md` - 本报告\n")

    f.write("\n## 查看方式\n\n")
    f.write("```bash\n")
    f.write("# 启动 MLflow UI\n")
    f.write("mlflow ui\n\n")
    f.write("# 查看 Optuna 数据库\n")
    f.write("sqlite3 src/optuna.db\n")
    f.write("```\n")

print(f"   ✅ 保存总结报告 -> {summary_md.name}")

print(f"\n✅ 完成！报告文件位于: {REPORTS_P2.relative_to(PROJECT_ROOT)}/")
print(f"\n生成的文件:")
for f in sorted(REPORTS_P2.glob("p2_*")):
    print(f"   - {f.name}")
