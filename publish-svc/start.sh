#!/bin/bash

# 启动脚本
echo "🚀 启动发布系统后端服务..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 setup.sh"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查密钥文件
if [ ! -f "keys/private_key.pem" ] || [ ! -f "keys/public_key.pem" ]; then
    echo "⚠️  密钥文件不存在，正在生成..."
    python generate_keys.py
fi

# 启动服务
echo "✅ 启动服务..."
python main.py

