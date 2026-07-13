"""
应用配置
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "发布系统后端服务"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    # DB_TYPE: mysql / sqlite / postgresql
    DB_TYPE: str = "sqlite"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "publish_system"
    DB_CHARSET: str = "utf8mb4"
    SQLITE_PATH: str = "./data/publish.db"
    DATABASE_URL: str = ""
    
    # JWT 配置（RS256）
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY_PATH: str = "./keys/private_key.pem"
    JWT_PUBLIC_KEY_PATH: str = "./keys/public_key.pem"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Cookie 配置
    COOKIE_NAME: str = "token"
    COOKIE_MAX_AGE: int = 7200
    COOKIE_SECURE: bool = False
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"
    
    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 1073741824  # 1GB
    LOCAL_STORAGE_DIR: str = "./uploads/objects"
    # OBJECT_STORAGE_PROVIDER: local / minio / s3
    OBJECT_STORAGE_PROVIDER: str = "local"
    
    # MinIO 配置
    MINIO_ENDPOINT: str = "192.168.3.68:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "publish-system"
    MINIO_SECURE: bool = False  # 是否使用 HTTPS

    # S3 兼容对象存储配置（MinIO 也可复用这组配置）
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = "publish-system"
    S3_REGION: str = "us-east-1"
    S3_SECURE: bool = True
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def database_url(self) -> str:
        """数据库连接URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        db_type = self.DB_TYPE.lower()
        if db_type == "sqlite":
            sqlite_path = Path(self.SQLITE_PATH)
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{sqlite_path}"
        if db_type in {"postgres", "postgresql"}:
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """CORS允许的源列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def jwt_private_key(self) -> str:
        """读取JWT私钥"""
        self._ensure_jwt_keys()
        key_path = Path(self.JWT_PRIVATE_KEY_PATH)
        return key_path.read_text()
    
    @property
    def jwt_public_key(self) -> str:
        """读取JWT公钥"""
        self._ensure_jwt_keys()
        key_path = Path(self.JWT_PUBLIC_KEY_PATH)
        return key_path.read_text()

    def _ensure_jwt_keys(self) -> None:
        """首次本地启动时自动生成 JWT RSA 密钥对。"""
        private_path = Path(self.JWT_PRIVATE_KEY_PATH)
        public_path = Path(self.JWT_PUBLIC_KEY_PATH)
        if private_path.exists() and public_path.exists():
            return

        private_path.parent.mkdir(parents=True, exist_ok=True)
        public_path.parent.mkdir(parents=True, exist_ok=True)
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_path.write_bytes(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        public_path.write_bytes(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )


# 创建全局配置实例
settings = Settings()
