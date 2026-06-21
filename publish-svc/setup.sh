#!/bin/bash

# 环境初始化脚本
echo "🔧 初始化发布系统后端服务环境..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python 版本: $python_version"

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv .venv
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source .venv/bin/activate

# 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装依赖包..."
pip install -r requirements.txt

# 生成密钥对
if [ ! -f "keys/private_key.pem" ] || [ ! -f "keys/public_key.pem" ]; then
    echo "🔐 生成 JWT 密钥对..."
    python generate_keys.py
else
    echo "✅ 密钥对已存在"
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads
mkdir -p logs

# 复制环境变量文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "📝 创建 .env 文件..."
    echo "⚠️  请编辑 .env 文件，配置数据库等信息"
else
    echo "✅ .env 文件已存在"
fi

echo ""
echo "🎉 环境初始化完成！"
echo ""
echo "📋 后续步骤："
echo "   1. 编辑 .env 文件，配置数据库连接等信息"
echo "   2. 初始化数据库：mysql -u root -p < init.sql"
echo "   3. 导入测试数据：mysql -u root -p < mock_user.sql"
echo "   4. 启动服务：bash start.sh 或 python main.py"
echo ""

