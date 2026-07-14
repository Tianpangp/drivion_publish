"""
应用配置
"""
import os
import tomllib
from typing import Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


CONFIG_PATH = Path(
    os.getenv("PUBLISH_CONFIG_FILE", Path(__file__).resolve().parents[3] / "config.toml")
).expanduser()


def _load_toml() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("rb") as config_file:
        return tomllib.load(config_file)


TOML_CONFIG = _load_toml()


def _config(*path: str, default: Any = None) -> Any:
    value: Any = TOML_CONFIG
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "发布系统后端服务"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = _config("server", "debug", default=True)
    
    # 服务器配置
    HOST: str = _config("server", "host", default="0.0.0.0")
    PORT: int = _config("server", "port", default=8001)
    
    # 数据库配置
    # DB_TYPE: mysql / sqlite / postgresql
    DB_TYPE: str = _config("database", "type", default="sqlite")
    DB_HOST: str = _config("database", "host", default="localhost")
    DB_PORT: int = _config("database", "port", default=3306)
    DB_USER: str = _config("database", "username", default="root")
    DB_PASSWORD: str = _config("database", "password", default="")
    DB_NAME: str = _config("database", "name", default="publish_system")
    DB_CHARSET: str = _config("database", "charset", default="utf8mb4")
    SQLITE_PATH: str = _config("database", "sqlite_path", default="./data/publish.db")
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
    CORS_ORIGINS: str | List[str] = _config(
        "server", "cors_origins", default=["http://localhost:3000", "http://localhost:5173"]
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 1073741824  # 1GB
    LOCAL_STORAGE_DIR: str = _config("storage", "local_dir", default="./uploads/objects")
    # OBJECT_STORAGE_PROVIDER: local / minio / s3
    OBJECT_STORAGE_PROVIDER: str = _config("storage", "provider", default="local")
    
    # MinIO 配置
    MINIO_ENDPOINT: str = str(_config("storage", "endpoint", default="http://192.168.3.68:9000")).removeprefix("http://").removeprefix("https://")
    MINIO_ACCESS_KEY: str = _config("storage", "access_key", default="minioadmin")
    MINIO_SECRET_KEY: str = _config("storage", "secret_key", default="minioadmin")
    MINIO_BUCKET: str = _config("storage", "bucket", default="publish-system")
    MINIO_SECURE: bool = _config("storage", "secure", default=False)

    # S3 兼容对象存储配置（MinIO 也可复用这组配置）
    S3_ENDPOINT_URL: str = _config("storage", "endpoint", default="")
    S3_ACCESS_KEY_ID: str = _config("storage", "access_key", default="")
    S3_SECRET_ACCESS_KEY: str = _config("storage", "secret_key", default="")
    S3_BUCKET: str = _config("storage", "bucket", default="publish-system")
    S3_REGION: str = _config("storage", "region", default="us-east-1")
    S3_SECURE: bool = _config("storage", "secure", default=True)

    # 认证配置
    AUTH_MODE: str = _config("auth", "mode", default="local")
    SSO_ISSUER: str = _config("auth", "sso", "issuer", default="http://localhost:8002")
    SSO_CLIENT_ID: str = _config("auth", "sso", "client_id", default="release")
    SSO_CLIENT_SECRET: str = ""
    SSO_CLIENT_SECRET_ENV: str = _config("auth", "sso", "client_secret_env", default="RELEASE_OIDC_CLIENT_SECRET")
    SSO_SCOPE: str = _config("auth", "sso", "scope", default="openid profile")
    SSO_REDIRECT_URI: str = _config("auth", "sso", "redirect_uri", default="http://localhost:8001/publish/api/v1/auth/sso/callback")
    SSO_FRONTEND_REDIRECT_URI: str = _config("auth", "sso", "frontend_redirect_uri", default="http://localhost:5173/auth/callback")
    SSO_SESSION_SECRET: str = ""
    SSO_SESSION_SECRET_ENV: str = _config("auth", "sso", "session_secret_env", default="PUBLISH_SSO_SESSION_SECRET")
    SSO_SESSION_COOKIE_NAME: str = _config("auth", "sso", "session_cookie_name", default="publish_sso_session")
    SSO_TRANSACTION_COOKIE_NAME: str = _config("auth", "sso", "transaction_cookie_name", default="publish_sso_transaction")
    SSO_COOKIE_SECURE: bool = _config("auth", "sso", "cookie_secure", default=False)
    SSO_SESSION_MAX_AGE_SECONDS: int = _config("auth", "sso", "session_max_age_seconds", default=604800)
    SSO_REFRESH_BEFORE_EXPIRY_SECONDS: int = _config("auth", "sso", "refresh_before_expiry_seconds", default=60)
    SSO_HTTP_TIMEOUT_SECONDS: int = _config("auth", "sso", "http_timeout_seconds", default=10)
    SSO_INTROSPECT_HIGH_RISK: bool = _config("auth", "sso", "introspect_high_risk", default=True)
    
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
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def auth_mode(self) -> str:
        mode = self.AUTH_MODE.lower()
        if mode not in {"local", "sso"}:
            raise ValueError("AUTH_MODE 只支持 local 或 sso")
        return mode

    @property
    def sso_client_secret(self) -> str:
        return self.SSO_CLIENT_SECRET or os.getenv(self.SSO_CLIENT_SECRET_ENV, "")

    @property
    def sso_session_secret(self) -> str:
        return self.SSO_SESSION_SECRET or os.getenv(self.SSO_SESSION_SECRET_ENV, "")
    
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
