#!/usr/bin/env python3
"""
快速验证脚本 - 简化版

检查项目核心组件的可用性，快速评估项目状态。
"""

import sys
from pathlib import Path

def check_critical_files():
    """检查关键文件"""
    print("检查关键文件...")

    critical_files = {
        "配置": [
            "src/config.py",
            "docker/docker-compose.yml",
            ".dockerignore",
        ],
        "核心代码": [
            "src/mlflow_utils/tracking.py",
            "src/mlflow_utils/registry.py",
            "src/deployment/fastapi_app.py",
            "src/deployment/inference.py",
        ],
        "测试": [
            "tests/test_e2e_api.py",
            "docker/test_docker.sh",
            "scripts/verify_system.py",
        ],
        "文档": [
            "README.md",
            "COMPLETION_GUIDE.md",
            "00_docs/PROGRESS.md",
        ]
    }

    total = 0
    passed = 0

    for category, files in critical_files.items():
        print(f"\n{category}:")
        for filepath in files:
            path = Path(filepath)
            if path.exists():
                print(f"  ✓ {filepath}")
                passed += 1
            else:
                print(f"  ✗ {filepath} - NOT FOUND")
            total += 1

    print(f"\n总计: {passed}/{total} 存在 ({passed/total*100:.0f}%)")
    return passed == total

def check_project_structure():
    """检查项目结构"""
    print("\n检查项目结构...")

    dirs = [
        "src/mlflow_utils",
        "src/deployment",
        "src/experiments",
        "docker",
        "tests",
        "scripts",
        "00_docs",
    ]

    passed = 0
    for d in dirs:
        if Path(d).exists():
            print(f"  ✓ {d}/")
            passed += 1
        else:
            print(f"  ✗ {d}/ - NOT FOUND")

    print(f"\n目录存在: {passed}/{len(dirs)}")
    return passed == len(dirs)

def main():
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "快速项目验证" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝\n")

    results = {
        "关键文件": check_critical_files(),
        "项目结构": check_project_structure(),
    }

    print("\n" + "━" * 70)
    print("验证总结")
    print("━" * 70)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status:8s} {name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n✓ 项目状态良好，可以继续推进！")
        return 0
    else:
        print(f"\n⚠ {total - passed} 项检查失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
