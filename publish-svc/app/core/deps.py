"""
依赖注入
"""
from typing import Optional, Set
from fastapi import Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.core.config import settings
from app.core.permissions import get_role_permissions, has_permission
from app.core.sso import sso_client
from app.core.sso_permissions import map_sso_permissions
from app.models.user import User, Role

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token_cookie: Optional[str] = Cookie(None, alias=settings.COOKIE_NAME),
    sso_session_cookie: Optional[str] = Cookie(None, alias=settings.SSO_SESSION_COOKIE_NAME),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    支持从 Authorization 头或 Cookie 中获取 Token
    """
    if settings.auth_mode == "sso":
        if not sso_session_cookie:
            raise HTTPException(status_code=401, detail="未登录 SSO")
        session = await sso_client.load_session(db, sso_session_cookie)
        roles = list(session.roles or [])
        external_permissions = list(session.permissions or [])
        user = User(
            id=session.subject, username=session.username, password="",
            nickname=session.nickname or session.username, email=session.email,
            role=0, status="active",
        )
        user.role_code = roles[0] if roles else "platform.user"
        user.roles = roles
        user.auth_source = "sso"
        user.external_permissions = external_permissions
        user.permission_grants = list(session.permission_grants or [])
        user.permission_codes = map_sso_permissions(external_permissions, roles)
        user.sso_access_token = sso_client.decrypt(session.access_token)
        user.sso_session_id = session.id
        return user

    # 优先从 Cookie 获取 token
    token = token_cookie
    
    # 如果 Cookie 中没有，则从 Authorization 头获取
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证或认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 解码 token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户ID
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效",
        )
    
    # 查询用户及其角色信息
    try:
        result = await db.execute(
            select(User, Role)
            .join(Role, User.role == Role.id)
            .where(User.id == user_id, User.status == "active")
        )
        user_role = result.first()
    except Exception:
        user_role = None
    
    if not user_role:
        if user_id in {"mock-admin", "mock-user"}:
            role_code = "admin" if user_id == "mock-admin" else "viewer"
            user = User(
                id=user_id,
                username="admin" if user_id == "mock-admin" else "user",
                password="",
                nickname="admin" if user_id == "mock-admin" else "user",
                email=f"{user_id}@local.test",
                role=1 if role_code == "admin" else 6,
                status="active",
            )
            user.role_code = role_code
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    
    user, role = user_role
    
    # 将角色代码附加到用户对象上(用于权限检查)
    user.role_code = role.code
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    """
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    return current_user


async def get_user_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Set[str]:
    """
    获取用户权限列表
    从 permissions.py 的硬编码配置中获取角色权限
    """
    if hasattr(current_user, "permission_codes"):
        return set(current_user.permission_codes)

    # 从硬编码配置中获取角色权限
    if hasattr(current_user, 'role_code'):
        return get_role_permissions(current_user.role_code)
    
    # 如果没有 role_code 属性,查询角色信息
    result = await db.execute(
        select(Role).where(Role.id == current_user.role)
    )
    role = result.scalar_one_or_none()
    
    if role:
        current_user.role_code = role.code
        return get_role_permissions(role.code)
    
    return set()


def require_permissions(*required_permissions: str):
    """
    权限检查装饰器
    
    Args:
        *required_permissions: 需要的权限代码列表
    
    使用说明:
        from app.core.permissions import Permission
        
        @router.post("/facilities/factory")
        async def create_factory(
            user = Depends(require_permissions(Permission.FACILITY_FACTORY_CREATE.value))
        ):
            pass
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # 获取用户角色代码
        role_code = getattr(current_user, 'role_code', None)
        
        if not role_code:
            # 如果没有 role_code,查询角色信息
            result = await db.execute(
                select(Role).where(Role.id == current_user.role)
            )
            role = result.scalar_one_or_none()
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="用户角色信息异常",
                )
            
            role_code = role.code
            current_user.role_code = role_code
        
        if hasattr(current_user, "permission_codes"):
            missing = [item for item in required_permissions if item not in current_user.permission_codes]
            if missing:
                raise HTTPException(status_code=403, detail=f"无操作权限: {missing[0]}")
            return current_user

        # 管理员拥有所有权限(硬编码检查)
        if role_code == "admin":
            return current_user
        
        # 检查是否拥有所需权限(使用硬编码的权限配置)
        for permission in required_permissions:
            if not has_permission(role_code, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"无操作权限: {permission}",
                )
        
        return current_user
    
    return permission_checker


def user_has_permission(user: User, permission: str) -> bool:
    if hasattr(user, "permission_codes"):
        return permission in user.permission_codes
    return has_permission(getattr(user, "role_code", ""), permission)


async def require_fresh_sso_permission(user: User, permission: str) -> None:
    """高风险操作在线确认账号和权限；发布系统明确忽略 Scope。"""
    if getattr(user, "auth_source", "local") != "sso":
        return
    if permission not in set(getattr(user, "external_permissions", [])):
        raise HTTPException(status_code=403, detail=f"无操作权限: {permission}")
    if not settings.SSO_INTROSPECT_HIGH_RISK:
        return
    try:
        result = await sso_client.introspect(user.sso_access_token)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="SSO 权限在线校验失败") from exc
    if not result.get("active") or result.get("sub") != user.id:
        raise HTTPException(status_code=401, detail="SSO Token 已失效")
    if result.get("client_id") != settings.SSO_CLIENT_ID:
        raise HTTPException(status_code=401, detail="SSO Token 客户端不匹配")
    if permission not in set(result.get("permissions", [])):
        raise HTTPException(status_code=403, detail=f"SSO 权限已被撤销: {permission}")
