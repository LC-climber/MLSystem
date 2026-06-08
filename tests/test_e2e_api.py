"""
端到端测试脚本 - FastAPI 推理服务

测试完整的推理流程：
1. 服务启动验证
2. 健康检查
3. 模型信息获取
4. 推理测试（v1 和 v2）
5. 错误处理
"""

import requests
import json
import time
import sys

# 配置
BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_health_check():
    """测试健康检查端点"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("测试 1: 健康检查")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json()
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 服务状态: {data.get('status')}")
        print(f"✓ 模型已加载: {data.get('model_loaded')}")

        assert data.get('status') == 'healthy', "服务状态异常"
        assert data.get('model_loaded') == True, "模型未加载"

        print("✓ 健康检查通过")
        return True

    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        return False


def test_model_info():
    """测试模型信息端点"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("测试 2: 模型信息")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        response = requests.get(f"{BASE_URL}/model_info", timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json()
        print(f"✓ 模型名称: {data.get('model_name')}")
        print(f"✓ 模型版本: {data.get('model_version')}")
        print(f"✓ 模型别名: {data.get('model_alias')}")
        print(f"✓ 特征版本: {data.get('feature_version')}")
        print(f"✓ 特征数量: {data.get('n_features')}")

        print("✓ 模型信息获取成功")
        return True

    except Exception as e:
        print(f"✗ 模型信息获取失败: {e}")
        return False


def test_prediction_v1():
    """测试 v1 预测"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("测试 3: v1 预测")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 示例输入
    payload = {
        "age": 12.5,
        "sex": 1,
        "bmi": 18.5,
        "height": 150.0,
        "weight": 45.0,
        "cgas_score": 75.0
    }

    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        print(f"✓ 预测类别: {data.get('prediction')}")
        print(f"✓ 预测标签: {data.get('prediction_label')}")
        print(f"✓ 置信度: {data.get('confidence'):.2%}")
        print(f"✓ 概率分布: {[f'{p:.3f}' for p in data.get('probabilities', [])]}")

        # 验证输出格式
        assert 'prediction' in data, "缺少 prediction 字段"
        assert 'prediction_label' in data, "缺少 prediction_label 字段"
        assert 'confidence' in data, "缺少 confidence 字段"
        assert 0 <= data['prediction'] <= 3, "预测类别超出范围"
        assert 0 <= data['confidence'] <= 1, "置信度超出范围"

        print("✓ v1 预测成功")
        return True

    except Exception as e:
        print(f"✗ v1 预测失败: {e}")
        return False


def test_prediction_v2():
    """测试 v2 预测（含 actigraphy）"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("测试 4: v2 预测（含 actigraphy）")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 示例输入（含 actigraphy）
    payload = {
        "age": 13.0,
        "sex": 0,
        "bmi": 19.2,
        "cgas_score": 68.0,
        "actigraphy_features": {
            "act_mean_enmo": 35.2,
            "act_std_enmo": 12.5,
            "act_night_enmo_mean": 5.2,
            "act_day_enmo_mean": 45.8
        }
    }

    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        print(f"✓ 预测类别: {data.get('prediction')}")
        print(f"✓ 预测标签: {data.get('prediction_label')}")
        print(f"✓ 置信度: {data.get('confidence'):.2%}")

        print("✓ v2 预测成功")
        return True

    except Exception as e:
        print(f"✗ v2 预测失败: {e}")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("测试 5: 错误处理")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 测试无效输入
    invalid_payload = {
        "age": -1,  # 无效年龄
        "sex": 2    # 无效性别
    }

    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=invalid_payload,
            timeout=TIMEOUT
        )

        # 应该返回错误
        if response.status_code >= 400:
            print(f"✓ 正确返回错误状态码: {response.status_code}")
            print("✓ 错误处理正常")
            return True
        else:
            print(f"✗ 应该返回错误但返回了: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        return False


def test_performance():
    """测试性能"""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("测试 6: 性能测试")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    payload = {
        "age": 12.5,
        "sex": 1,
        "bmi": 18.5,
        "cgas_score": 75.0
    }

    n_requests = 10
    times = []

    try:
        for i in range(n_requests):
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/predict",
                json=payload,
                timeout=TIMEOUT
            )
            elapsed = time.time() - start
            times.append(elapsed)

            if i == 0:
                print(f"✓ 首次请求: {elapsed*1000:.1f}ms")

        avg_time = sum(times[1:]) / len(times[1:])  # 排除首次
        print(f"✓ 平均响应时间: {avg_time*1000:.1f}ms ({n_requests-1}次)")
        print(f"✓ 最快: {min(times[1:])*1000:.1f}ms")
        print(f"✓ 最慢: {max(times[1:])*1000:.1f}ms")

        if avg_time < 1.0:  # 小于1秒
            print("✓ 性能测试通过")
            return True
        else:
            print(f"⚠ 响应时间较慢: {avg_time:.2f}s")
            return True  # 仍然算通过，只是警告

    except Exception as e:
        print(f"✗ 性能测试失败: {e}")
        return False


def wait_for_service(max_wait=60):
    """等待服务启动"""
    print(f"\n等待服务启动（最多 {max_wait} 秒）...")

    for i in range(max_wait):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"✓ 服务已启动（耗时 {i+1} 秒）")
                return True
        except:
            pass

        time.sleep(1)

    print(f"✗ 服务未在 {max_wait} 秒内启动")
    return False


def main():
    """主测试流程"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║              FastAPI 端到端测试                                ║")
    print("╚════════════════════════════════════════════════════════════════╝")

    # 等待服务启动
    if not wait_for_service():
        print("\n✗ 无法连接到服务，请确保服务已启动:")
        print("  cd docker && docker-compose up -d")
        print("  或")
        print("  uvicorn src.deployment.fastapi_app:app --reload")
        sys.exit(1)

    # 运行测试
    results = []

    results.append(("健康检查", test_health_check()))
    results.append(("模型信息", test_model_info()))
    results.append(("v1 预测", test_prediction_v1()))
    results.append(("v2 预测", test_prediction_v2()))
    results.append(("错误处理", test_error_handling()))
    results.append(("性能测试", test_performance()))

    # 总结
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║                      测试总结                                  ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status:8s} {name}")

    print()
    print(f"总计: {passed}/{total} 通过 ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n✓ 所有测试通过！")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} 个测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
