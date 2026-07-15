"""Authentication and resource-scope checks for Exe/DevKit HTTP clients."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any, Iterable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.sso import sso_client


integration_bearer = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class IntegrationPrincipal:
    subject: str
    username: str
    token: str | None = None
    permissions: set[str] = field(default_factory=set)
    permission_grants: list[dict[str, Any]] = field(default_factory=list)
    auth_source: str = "local_api_key"

    @property
    def id(self) -> str:
        return self.subject

    @property
    def nickname(self) -> str:
        return self.username

    @property
    def role_code(self) -> str:
        return "service.account"


async def get_integration_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(integration_bearer),
) -> IntegrationPrincipal:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "缺少 Exe/DevKit Bearer 凭据", headers={"WWW-Authenticate": "Bearer"})

    token = credentials.credentials
    if settings.auth_mode == "local":
        expected = settings.integration_api_key
        if not expected:
            raise HTTPException(503, f"未配置环境变量 {settings.INTEGRATION_API_KEY_ENV}")
        if not secrets.compare_digest(token, expected):
            raise HTTPException(401, "Exe/DevKit API Key 无效", headers={"WWW-Authenticate": "Bearer"})
        return IntegrationPrincipal(subject="integration:local", username="local-integration")

    try:
        claims = await sso_client.verify_token(token, "access")
    except Exception as exc:
        raise HTTPException(401, "SSO Access Token 无效", headers={"WWW-Authenticate": "Bearer"}) from exc

    return IntegrationPrincipal(
        subject=str(claims["sub"]),
        username=str(claims.get("username") or claims.get("client_id") or claims["sub"]),
        token=token,
        permissions=set(claims.get("permissions") or []),
        permission_grants=list(claims.get("permission_grants") or []),
        auth_source="sso",
    )


def _grant_matches(
    grant: dict[str, Any],
    permission: str,
    resources: Iterable[tuple[str, str]],
) -> bool:
    if grant.get("permission") != permission:
        return False
    scope_type = str(grant.get("scopeType") or grant.get("scope_type") or "")
    scope_id = str(grant.get("scopeId") or grant.get("scope_id") or "")
    if scope_type == "tenant" and scope_id == "*":
        return True
    return (scope_type, scope_id) in set(resources)


def require_integration_permission(
    principal: IntegrationPrincipal,
    permission: str,
    resources: Iterable[tuple[str, str]] = (),
    *,
    check_scope: bool = True,
) -> None:
    if principal.auth_source == "local_api_key":
        return
    if permission not in principal.permissions:
        raise HTTPException(403, f"无操作权限: {permission}")
    if check_scope and not any(
        _grant_matches(grant, permission, resources) for grant in principal.permission_grants
    ):
        raise HTTPException(403, f"权限不包含当前设备范围: {permission}")


async def require_fresh_integration_permission(
    principal: IntegrationPrincipal,
    permission: str,
) -> None:
    """Online-check a publish permission; artifact submission intentionally ignores scope."""
    require_integration_permission(principal, permission, check_scope=False)
    if principal.auth_source != "sso" or not settings.SSO_INTROSPECT_HIGH_RISK:
        return
    try:
        result = await sso_client.introspect(principal.token or "")
    except Exception as exc:
        raise HTTPException(503, "SSO 权限在线校验失败") from exc
    if not result.get("active") or result.get("sub") != principal.subject:
        raise HTTPException(401, "SSO Token 已失效")
    if permission not in set(result.get("permissions") or []):
        raise HTTPException(403, f"SSO 权限已被撤销: {permission}")
