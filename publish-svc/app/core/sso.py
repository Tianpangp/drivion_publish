"""Drivion SSO OIDC BFF 客户端。"""
from __future__ import annotations

import base64
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.sso import SsoAuthTransaction, SsoSession


class SsoError(RuntimeError):
    pass


class SsoClient:
    def __init__(self) -> None:
        self._discovery: dict[str, Any] | None = None
        self._jwks: dict[str, Any] | None = None
        self._cache_until = 0.0

    def validate_config(self) -> None:
        if settings.auth_mode != "sso":
            return
        missing = []
        if not settings.sso_client_secret:
            missing.append(settings.SSO_CLIENT_SECRET_ENV)
        if not settings.sso_session_secret:
            missing.append(settings.SSO_SESSION_SECRET_ENV)
        if missing:
            raise RuntimeError(f"SSO 模式缺少环境变量: {', '.join(missing)}")

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def _fernet(self) -> Fernet:
        secret = settings.sso_session_secret
        if not secret:
            raise SsoError("SSO 会话加密密钥未配置")
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
        return Fernet(key)

    def encrypt(self, value: str) -> str:
        return self._fernet().encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet().decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise SsoError("SSO 会话数据无法解密") from exc

    async def _metadata(self, force: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
        now = time.monotonic()
        if not force and self._discovery and self._jwks and now < self._cache_until:
            return self._discovery, self._jwks
        issuer = settings.SSO_ISSUER.rstrip("/")
        async with httpx.AsyncClient(timeout=settings.SSO_HTTP_TIMEOUT_SECONDS) as client:
            discovery_response = await client.get(f"{issuer}/.well-known/openid-configuration")
            discovery_response.raise_for_status()
            discovery = discovery_response.json()
            if discovery.get("issuer", "").rstrip("/") != issuer:
                raise SsoError("SSO Discovery issuer 与配置不一致")
            jwks_response = await client.get(discovery["jwks_uri"])
            jwks_response.raise_for_status()
        self._discovery, self._jwks = discovery, jwks_response.json()
        self._cache_until = now + 300
        return self._discovery, self._jwks

    async def verify_token(
        self, token: str, token_use: str, *, nonce: str | None = None
    ) -> dict[str, Any]:
        discovery, jwks = await self._metadata()
        header = jwt.get_unverified_header(token)
        key_data = next((item for item in jwks.get("keys", []) if item.get("kid") == header.get("kid")), None)
        if not key_data:
            discovery, jwks = await self._metadata(force=True)
            key_data = next((item for item in jwks.get("keys", []) if item.get("kid") == header.get("kid")), None)
        if not key_data:
            raise SsoError("SSO Token 使用了未知签名密钥")
        claims = jwt.decode(
            token,
            jwt.PyJWK.from_dict(key_data).key,
            algorithms=[key_data.get("alg", "RS256")],
            audience=settings.SSO_CLIENT_ID,
            issuer=discovery["issuer"],
            options={"require": ["exp", "iat", "iss", "aud", "sub", "token_use"]},
            leeway=10,
        )
        if claims.get("token_use") != token_use:
            raise SsoError("SSO Token 类型错误")
        if nonce is not None and claims.get("nonce") != nonce:
            raise SsoError("SSO ID Token nonce 校验失败")
        return claims

    async def create_auth_transaction(self, db: AsyncSession) -> tuple[str, str]:
        self.validate_config()
        raw_handle = secrets.token_urlsafe(48)
        state = secrets.token_urlsafe(48)
        nonce = secrets.token_urlsafe(48)
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        now = datetime.utcnow()
        await db.execute(delete(SsoAuthTransaction).where(SsoAuthTransaction.expires_at < now))
        db.add(SsoAuthTransaction(
            id=self._digest(raw_handle), state=state, nonce=nonce,
            code_verifier=self.encrypt(verifier), created_at=now,
            expires_at=now + timedelta(seconds=120),
        ))
        discovery, _ = await self._metadata()
        query = urlencode({
            "response_type": "code",
            "client_id": settings.SSO_CLIENT_ID,
            "redirect_uri": settings.SSO_REDIRECT_URI,
            "scope": settings.SSO_SCOPE,
            "state": state,
            "nonce": nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })
        return raw_handle, f"{discovery['authorization_endpoint']}?{query}"

    async def _token_request(self, data: dict[str, str]) -> dict[str, Any]:
        discovery, _ = await self._metadata()
        async with httpx.AsyncClient(timeout=settings.SSO_HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                discovery["token_endpoint"], data=data,
                auth=httpx.BasicAuth(settings.SSO_CLIENT_ID, settings.sso_client_secret),
            )
        if response.is_error:
            error = response.json().get("error", "token_request_failed")
            raise SsoError(f"SSO Token 请求失败: {error}")
        return response.json()

    async def complete_callback(
        self, db: AsyncSession, raw_transaction: str, state: str, code: str
    ) -> str:
        transaction = await db.get(SsoAuthTransaction, self._digest(raw_transaction))
        if not transaction or transaction.expires_at < datetime.utcnow() or not secrets.compare_digest(transaction.state, state):
            raise SsoError("SSO 登录状态无效或已过期")
        verifier = self.decrypt(transaction.code_verifier)
        nonce = transaction.nonce
        await db.delete(transaction)
        await db.commit()
        tokens = await self._token_request({
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.SSO_CLIENT_ID,
            "redirect_uri": settings.SSO_REDIRECT_URI,
            "code_verifier": verifier,
        })
        await self.verify_token(tokens["id_token"], "id", nonce=nonce)
        access_claims = await self.verify_token(tokens["access_token"], "access")
        userinfo = await self.userinfo(tokens["access_token"])
        raw_session = secrets.token_urlsafe(48)
        now = datetime.utcnow()
        db.add(SsoSession(
            id=self._digest(raw_session), subject=userinfo["sub"],
            username=userinfo.get("preferred_username") or access_claims.get("username") or userinfo["sub"],
            nickname=userinfo.get("name"), email=userinfo.get("email"),
            roles=userinfo.get("roles", []), permissions=userinfo.get("permissions", []),
            permission_grants=userinfo.get("permission_grants", []),
            access_token=self.encrypt(tokens["access_token"]),
            refresh_token=self.encrypt(tokens["refresh_token"]),
            access_expires_at=datetime.utcfromtimestamp(access_claims["exp"]),
            created_at=now, updated_at=now,
        ))
        return raw_session

    async def userinfo(self, access_token: str) -> dict[str, Any]:
        discovery, _ = await self._metadata()
        async with httpx.AsyncClient(timeout=settings.SSO_HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(
                discovery["userinfo_endpoint"], headers={"Authorization": f"Bearer {access_token}"}
            )
        if response.is_error:
            raise SsoError("无法从 SSO 获取用户信息")
        return response.json()

    async def load_session(self, db: AsyncSession, raw_session: str) -> SsoSession:
        query = select(SsoSession).where(SsoSession.id == self._digest(raw_session)).with_for_update()
        session = (await db.execute(query)).scalar_one_or_none()
        if not session:
            raise HTTPException(401, "SSO 会话不存在或已过期")
        if session.created_at + timedelta(seconds=settings.SSO_SESSION_MAX_AGE_SECONDS) <= datetime.utcnow():
            await db.delete(session)
            await db.commit()
            raise HTTPException(401, "SSO 会话已过期")
        refresh_at = datetime.utcnow() + timedelta(seconds=settings.SSO_REFRESH_BEFORE_EXPIRY_SECONDS)
        if session.access_expires_at <= refresh_at:
            try:
                tokens = await self._token_request({
                    "grant_type": "refresh_token", "client_id": settings.SSO_CLIENT_ID,
                    "refresh_token": self.decrypt(session.refresh_token),
                })
                claims = await self.verify_token(tokens["access_token"], "access")
                userinfo = await self.userinfo(tokens["access_token"])
            except Exception as exc:
                await db.delete(session)
                await db.commit()
                raise HTTPException(401, "SSO 会话刷新失败，请重新登录") from exc
            session.access_token = self.encrypt(tokens["access_token"])
            session.refresh_token = self.encrypt(tokens["refresh_token"])
            session.access_expires_at = datetime.utcfromtimestamp(claims["exp"])
            session.roles = userinfo.get("roles", [])
            session.permissions = userinfo.get("permissions", [])
            session.permission_grants = userinfo.get("permission_grants", [])
            session.nickname, session.email = userinfo.get("name"), userinfo.get("email")
            session.updated_at = datetime.utcnow()
            await db.flush()
        return session

    async def introspect(self, access_token: str) -> dict[str, Any]:
        discovery, _ = await self._metadata()
        async with httpx.AsyncClient(timeout=settings.SSO_HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                discovery["introspection_endpoint"], data={"token": access_token},
                auth=httpx.BasicAuth(settings.SSO_CLIENT_ID, settings.sso_client_secret),
            )
        if response.is_error:
            raise SsoError("SSO Token 在线校验失败")
        return response.json()

    async def logout(self, access_token: str) -> None:
        endpoint = f"{settings.SSO_ISSUER.rstrip('/')}/api/auth/logout"
        async with httpx.AsyncClient(timeout=settings.SSO_HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                endpoint, json={"revokeAll": False},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.is_error and response.status_code != 401:
            raise SsoError("SSO 登出请求失败")


sso_client = SsoClient()
