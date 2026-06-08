#!/usr/bin/env python3
"""
快速验证脚本 - 检查所有核心组件

在正式测试前快速验证系统各组件的可用性。
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_imports():
    """检查所有核心模块能否导入"""
    print("━" * 70)
    print("检查 1: 核心模块导入")
    print("━" * 70)

    modules = [
        ("src.config", "配置模块"),
        ("src.models.sklearn_baselines", "sklearn 模型"),
        ("src.models.configurable_torch_mlp", "PyTorch 模型"),
        ("src.mlflow_utils.tracking", "MLflow tracking"),
        ("src.mlflow_utils.registry", "MLflow registry"),
        ("src.mlflow_utils.artifacts", "MLflow artifacts"),
        ("src.deployment.inference", "特征工程"),
        ("src.deployment.schemas", "API schemas"),
    ]

    success = 0
    for module, name in modules:
        try:
            __import__(module)
            print(f"✓ {name:30s} - OK")
            success += 1
        except Exception as e:
            print(f"✗ {name:30s} - FAILED: {e}")

    print(f"\n导入成功: {success}/{len(modules)}\n")
    return success == len(modules)


def check_data_files():
    """检查数据文件是否存在"""
    print("━" * 70)
    print("检查 2: 数据文件")
    print("━" * 70)

    files = [
        "data/processed/feat_v1.parquet",
        "data/processed/feat_v2.parquet",
        "data/splits/stratified_group_kfold_seed42.csv",
    ]

    success = 0
    for filepath in files:
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size / (1024 * 1024)  # MB
            print(f"✓ {filepath:50s} ({size:.1f} MB)")
            success += 1
        else:
            print(f"✗ {filepath:50s} - NOT FOUND")

    print(f"\n文件存在: {success}/{len(files)}\n")
    return success == len(files)


def check_mlflow():
    """检查 MLflow 配置"""
    print("━" * 70)
    print("检查 3: MLflow 配置")
    print("━" * 70)

    try:
        import mlflow
        from src.config import MLFLOW_TRACKING_URI

        print(f"✓ MLflow 版本: {mlflow.__version__}")
        print(f"✓ Tracking URI: {MLFLOW_TRACKING_URI}")

        # 检查能否连接
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        client = mlflow.MlflowClient()

        # 尝试列出实验
        experiments = client.search_experiments()
        print(f"✓ MLflow 连接成功")
        print(f"✓ 实验数量: {len(experiments)}")

        return True
    except Exception as e:
        print(f"✗ MLflow 配置失败: {e}")
        return False


def check_model_files():
    """检查模型文件"""
    print("━" * 70)
    print("检查 4: 模型和脚本")
    print("━" * 70)

    files = [
        "scripts/register_baseline.py",
        "src/experiments/run_p2_optuna.py",
        "src/deployment/fastapi_app.py",
        "tests/test_e2e_api.py",
        "docker/test_docker.sh",
    ]

    success = 0
    for filepath in files:
        path = Path(filepath)
        if path.exists():
            print(f"✓ {filepath:50s}")
            success += 1
        else:
            print(f"✗ {filepath:50s} - NOT FOUND")

    print(f"\n脚本存在: {success}/{len(files)}\n")
    return success == len(files)


def check_docker_files():
    """检查 Docker 配置"""
    print("━" * 70)
    print("检查 5: Docker 配置")
    print("━" * 70)

    files = [
        "docker/Dockerfile.infer",
        "docker/Dockerfile.train",
        "docker/docker-compose.yml",
        "docker/requirements-infer.txt",
        "docker/requirements-train.txt",
        ".dockerignore",
    ]

    success = 0
    for filepath in files:
        path = Path(filepath)
        if path.exists():
            print(f"✓ {filepath:50s}")
            success += 1
        else:
            print(f"✗ {filepath:50s} - NOT FOUND")

    print(f"\nDocker 文件: {success}/{len(files)}\n")
    return success == len(files)


def check_documentation():
    """检查文档完整性"""
    print("━" * 70)
    print("检查 6: 文档完整性")
    print("━" * 70)

    docs = [
        "README.md",
        "PROJECT_STATUS_REPORT_20260608.md",
        "DAILY_SUMMARY_20260608.md",
        "00_docs/PROGRESS.md",
        "00_docs/PROJECT_LOG.md",
        "00_docs/NEXT_STEPS.md",
        "00_docs/MODEL_PUBLISHING_GUIDE.md",
        "00_docs/CHAMPION_SELECTION_GUIDE.md",
    ]

    success = 0
    total_lines = 0
    for filepath in docs:
        path = Path(filepath)
        if path.exists():
            lines = len(path.read_text().splitlines())
            total_lines += lines
            print(f"✓ {filepath:50s} ({lines:4d} 行)")
            success += 1
        else:
            print(f"✗ {filepath:50s} - NOT FOUND")

    print(f"\n文档存在: {success}/{len(docs)}")
    print(f"总行数: {total_lines:,} 行\n")
    return success == len(docs)


def main():
    """主验证流程"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "系统验证 - 快速检查" + " " * 27 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    results = {
        "核心模块导入": check_imports(),
        "数据文件": check_data_files(),
        "MLflow 配置": check_mlflow(),
        "模型和脚本": check_model_files(),
        "Docker 配置": check_docker_files(),
        "文档完整性": check_documentation(),
    }

    # 总结
    print("━" * 70)
    print("验证总结")
    print("━" * 70)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status:8s} {name}")

    print()
    print(f"总计: {passed}/{total} 通过 ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n✓ 所有检查通过！系统就绪。")
        return 0
    else:
        print(f"\n✗ {total - passed} 项检查失败，请修复后重试。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
