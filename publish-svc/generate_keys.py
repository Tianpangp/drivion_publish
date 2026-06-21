#!/usr/bin/env python3
"""
生成 JWT RS256 密钥对

运行此脚本生成私钥和公钥文件
"""
import os
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_rsa_keys(key_size: int = 2048, keys_dir: str = "./keys"):
    """
    生成 RSA 密钥对
    
    Args:
        key_size: 密钥长度（位），默认 2048
        keys_dir: 密钥文件存储目录
    """
    # 创建密钥目录
    keys_path = Path(keys_dir)
    keys_path.mkdir(exist_ok=True)
    
    # 生成私钥
    print(f"🔐 正在生成 {key_size} 位 RSA 密钥对...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    
    # 序列化私钥
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # 保存私钥
    private_key_path = keys_path / "private_key.pem"
    with open(private_key_path, "wb") as f:
        f.write(private_pem)
    print(f"✅ 私钥已保存至: {private_key_path}")
    
    # 生成公钥
    public_key = private_key.public_key()
    
    # 序列化公钥
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # 保存公钥
    public_key_path = keys_path / "public_key.pem"
    with open(public_key_path, "wb") as f:
        f.write(public_pem)
    print(f"✅ 公钥已保存至: {public_key_path}")
    
    # 设置文件权限（仅所有者可读写）
    os.chmod(private_key_path, 0o600)
    os.chmod(public_key_path, 0o644)
    
    print("\n🎉 密钥对生成完成!")
    print(f"\n⚠️  请妥善保管私钥文件: {private_key_path}")
    print("   不要将私钥提交到版本控制系统！")


if __name__ == "__main__":
    generate_rsa_keys()

