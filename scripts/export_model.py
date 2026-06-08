#!/usr/bin/env python3
"""
模型导出工具

将 MLflow 中的模型导出为可发布格式。
"""

import sys
import mlflow
import joblib
from pathlib import Path
import json
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import MLFLOW_TRACKING_URI


def export_model(model_name="piu-risk", alias="champion", output_dir="exported_models"):
    """
    导出模型

    Args:
        model_name: 模型名称
        alias: 模型别名
        output_dir: 输出目录
    """
    print(f"导出模型: {model_name} (别名: {alias})")

    # 设置 MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = mlflow.MlflowClient()

    # 创建输出目录
    output_path = Path(output_dir) / f"{model_name}-{alias}"
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"输出目录: {output_path}")

    try:
        # 获取模型
        model_uri = f"models:/{model_name}@{alias}"
        print(f"加载模型: {model_uri}")

        # 下载模型
        model_path = mlflow.artifacts.download_artifacts(model_uri)
        print(f"模型路径: {model_path}")

        # 复制模型文件
        for item in Path(model_path).iterdir():
            if item.is_file():
                shutil.copy2(item, output_path / item.name)
                print(f"  ✓ 复制: {item.name}")

        # 获取模型元数据
        model_version = client.get_model_version_by_alias(model_name, alias)

        metadata = {
            "model_name": model_name,
            "version": model_version.version,
            "alias": alias,
            "run_id": model_version.run_id,
            "description": model_version.description,
            "tags": model_version.tags,
        }

        # 保存元数据
        metadata_file = output_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"  ✓ 保存元数据: metadata.json")

        # 创建 README
        readme_content = f"""# {model_name} Model ({alias})

## 模型信息

- **版本**: {model_version.version}
- **别名**: {alias}
- **Run ID**: {model_version.run_id}

## 文件说明

- `model.pkl` / `pytorch_model.bin`: 模型权重
- `metadata.json`: 模型元数据
- `MLmodel`: MLflow 模型定义
- `requirements.txt`: 依赖清单

## 使用方法

### Python

```python
import mlflow

# 加载模型
model = mlflow.pyfunc.load_model(".")

# 预测
predictions = model.predict(X)
```

### 部署

参考项目主文档中的部署指南。

## 更多信息

- 项目仓库: https://github.com/LC-climber/MLSystem
- 文档: 项目 00_docs/ 目录
"""

        readme_file = output_path / "README.md"
        readme_file.write_text(readme_content)
        print(f"  ✓ 生成 README: README.md")

        print(f"\n✓ 导出完成！")
        print(f"输出位置: {output_path.absolute()}")

        return str(output_path.absolute())

    except Exception as e:
        print(f"\n✗ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 25 + "模型导出工具" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝\n")

    # 默认导出 champion 模型
    result = export_model(
        model_name="piu-risk",
        alias="champion",
        output_dir="exported_models"
    )

    if result:
        print(f"\n成功导出模型到: {result}")
        return 0
    else:
        print("\n导出失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
