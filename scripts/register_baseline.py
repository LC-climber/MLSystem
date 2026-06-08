"""
注册 P1 最佳模型为 baseline

从 P1 实验结果中选择最佳模型（按 QWK），注册到 MLflow Model Registry 并设置 baseline 别名。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
import logging

from src.mlflow_utils.registry import register_model, set_alias, init_registry
from src.config import MLFLOW_TRACKING_URI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_best_p1_model(
    report_paths: list,
    metric: str = "qwk_mean",
) -> tuple:
    """
    从 P1 报告中找到最佳模型

    Args:
        report_paths: 报告文件路径列表
        metric: 用于排序的指标

    Returns:
        (best_row, report_path) 元组
    """
    all_results = []

    for report_path in report_paths:
        if not Path(report_path).exists():
            logger.warning(f"Report not found: {report_path}")
            continue

        df = pd.read_csv(report_path)
        df['source_file'] = report_path
        all_results.append(df)

    if not all_results:
        raise FileNotFoundError("No valid P1 reports found")

    # 合并所有结果
    combined = pd.concat(all_results, ignore_index=True)

    # 按指标排序
    if metric not in combined.columns:
        logger.warning(f"Metric '{metric}' not found, trying alternative names...")
        # 尝试其他可能的列名
        possible_names = ['qwk', 'val_qwk', 'cv_qwk_mean']
        for alt_name in possible_names:
            if alt_name in combined.columns:
                metric = alt_name
                logger.info(f"Using metric: {metric}")
                break
        else:
            raise ValueError(f"Cannot find QWK metric in reports. Available columns: {combined.columns.tolist()}")

    # 找到最佳模型
    combined = combined.sort_values(metric, ascending=False)
    best_row = combined.iloc[0]

    logger.info(f"Best P1 model: {best_row['system']} {best_row['algo']} on {best_row['feature']}")
    logger.info(f"  {metric}: {best_row[metric]:.4f}")

    return best_row, combined


def register_baseline_from_reports(
    model_name: str = "piu-risk",
    dry_run: bool = False,
):
    """
    从 P1 报告中注册 baseline 模型

    Args:
        model_name: 模型注册名称
        dry_run: 如果为 True，只打印信息不实际注册
    """
    # P1 报告路径
    report_paths = [
        "reports/p1_systemwise_table2.csv",
        "reports/p1_systemwise_feat_v1.csv",
        "reports/p1_systemwise_feat_v2.csv",
    ]

    # 找到最佳模型
    logger.info("Searching for best P1 model...")
    best_row, all_results = find_best_p1_model(report_paths)

    # 提取信息
    system = best_row['system']
    algo = best_row['algo']
    feature = best_row['feature']
    qwk = best_row.get('qwk_mean', best_row.get('qwk', 0.0))

    logger.info("\n" + "="*60)
    logger.info("BASELINE MODEL SELECTION")
    logger.info("="*60)
    logger.info(f"System:   {system}")
    logger.info(f"Algorithm: {algo}")
    logger.info(f"Feature:   {feature}")
    logger.info(f"QWK:       {qwk:.4f}")
    logger.info("="*60 + "\n")

    if dry_run:
        logger.info("Dry run mode - not registering to MLflow")
        return

    # 从 MLflow 中查找对应的 run
    logger.info("Searching MLflow runs for matching experiment...")
    client = MlflowClient()

    # 尝试多个可能的 experiment 名称
    experiment_names = [
        "piu-p1-systemwise",
        f"piu-p1-systemwise-{feature}",
        "default",
    ]

    matching_run = None
    for exp_name in experiment_names:
        try:
            experiment = client.get_experiment_by_name(exp_name)
            if experiment is None:
                continue

            # 搜索匹配的 run
            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"params.system = '{system}' and params.algo = '{algo}' and params.feat_version = '{feature}'",
                max_results=1,
                order_by=["metrics.val_qwk DESC"]
            )

            if runs:
                matching_run = runs[0]
                logger.info(f"Found matching run in experiment '{exp_name}': {matching_run.info.run_id}")
                break

        except Exception as e:
            logger.debug(f"Could not search experiment '{exp_name}': {e}")
            continue

    if matching_run is None:
        logger.warning("Could not find matching MLflow run!")
        logger.warning("You may need to manually register the baseline model using:")
        logger.warning(f"  python -c \"from src.mlflow_utils.registry import register_model; register_model('<run_id>', '{model_name}', 'baseline')\"")
        return

    # 注册模型
    run_id = matching_run.info.run_id
    logger.info(f"Registering model from run {run_id}...")

    try:
        # 初始化 registry
        init_registry(model_name)

        # 注册模型
        model_version = register_model(
            run_id=run_id,
            model_name=model_name,
            alias="baseline",
            description=f"Baseline model: {system} {algo} on {feature} (QWK={qwk:.4f})",
            tags={
                "phase": "p1",
                "system": system,
                "algo": algo,
                "feature": feature,
                "qwk": str(qwk),
            }
        )

        logger.info(f"✓ Successfully registered baseline model (version {model_version.version})")
        logger.info(f"  Alias: baseline")
        logger.info(f"  Model URI: models:/{model_name}@baseline")

        # 保存 baseline 信息到配置
        baseline_info = {
            "model_name": model_name,
            "version": model_version.version,
            "run_id": run_id,
            "system": system,
            "algo": algo,
            "feature": feature,
            "qwk": float(qwk),
        }

        baseline_file = project_root / "models" / "baseline_info.json"
        baseline_file.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(baseline_file, 'w') as f:
            json.dump(baseline_info, f, indent=2)

        logger.info(f"✓ Saved baseline info to {baseline_file}")

    except Exception as e:
        logger.error(f"Failed to register baseline model: {e}")
        raise


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Register P1 best model as baseline")
    parser.add_argument(
        "--model-name",
        type=str,
        default="piu-risk",
        help="Model name in MLflow Registry"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selection without registering"
    )

    args = parser.parse_args()

    # 设置 MLflow tracking URI
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    # 注册 baseline
    register_baseline_from_reports(
        model_name=args.model_name,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
