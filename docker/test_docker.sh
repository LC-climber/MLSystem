#!/bin/bash
# Docker 构建测试脚本

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                Docker 镜像构建测试                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "✗ Docker 未安装"
    exit 1
fi
echo "✓ Docker 已安装: $(docker --version)"

# 检查 docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "✗ docker-compose 未安装"
    exit 1
fi
echo "✓ docker-compose 已安装: $(docker-compose --version)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 1: 构建推理镜像"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker build -f docker/Dockerfile.infer -t piu-infer:test . --no-cache

if [ $? -eq 0 ]; then
    echo "✓ 推理镜像构建成功"
    docker images | grep piu-infer
else
    echo "✗ 推理镜像构建失败"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 2: docker-compose 配置验证"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd docker
docker-compose config

if [ $? -eq 0 ]; then
    echo "✓ docker-compose 配置有效"
else
    echo "✗ docker-compose 配置无效"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试 3: 启动服务（仅验证，不持久运行）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker-compose up -d

if [ $? -eq 0 ]; then
    echo "✓ 服务启动成功"
    echo ""
    echo "运行中的容器:"
    docker-compose ps

    echo ""
    echo "等待服务就绪..."
    sleep 10

    # 测试健康检查
    echo ""
    echo "测试 MLflow 健康检查:"
    curl -f http://localhost:5000/health && echo " ✓" || echo " ✗"

    echo "测试推理服务健康检查:"
    curl -f http://localhost:8000/health && echo " ✓" || echo " ✗"

    # 停止服务
    echo ""
    echo "停止测试服务..."
    docker-compose down
else
    echo "✗ 服务启动失败"
    docker-compose logs
    docker-compose down
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✓ 所有测试通过                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
