"""
认证相关 API
"""
from datetime import datetime, timedelta
from typing import Optional
import httpx
import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, status, Response, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, or_, func
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.core.deps import get_current_user, require_permissions
from app.core.permissions import Permission, get_role_permissions
from app.core.utils import generate_id
from app.core.sso import SsoError, sso_client
from app.models.log import OperationLog
from app.models.user import User, Role, RoleRequest
from app.models.sso import SsoSession
from app.schemas.auth import (
    RegisterRequest, LoginRequest, LoginResponse, 
    TokenData, UserInfo, UserSearchResponse, UserListItem,
    RoleChangeRequest, RoleApplyRequest, RoleReviewRequest,
    ProfileUpdateRequest, PasswordChangeRequest, AccountDeleteRequest,
)
from app.schemas.common import Response as CommonResponse

router = APIRouter()
ASSIGNABLE_ROLES = {"developer", "tester", "release_manager", "engineer", "viewer"}


def _require_local_mode() -> None:
    if settings.auth_mode != "local":
        raise HTTPException(404, "SSO 模式不提供内置账号接口")


def _auth_log(db: AsyncSession, user: User, operation: str, description: str, target_id: str) -> None:
    db.add(OperationLog(
        id=generate_id("log"), operation=operation, module="用户管理",
        operator_id=user.id, operator=user.nickname or user.username,
        role=getattr(user, "role_code", ""), result="success", time=datetime.now(),
        description=description, target_id=target_id, target_type="user",
    ))


@router.get("/mode", response_model=CommonResponse[dict], summary="获取认证模式")
async def auth_mode():
    return CommonResponse(data={
        "mode": settings.auth_mode,
        "registrationEnabled": settings.auth_mode == "local",
        "ssoLoginUrl": "/publish/api/v1/auth/sso/login" if settings.auth_mode == "sso" else None,
    })


@router.get("/sso/login", summary="发起 SSO 登录")
async def sso_login(db: AsyncSession = Depends(get_db)):
    if settings.auth_mode != "sso":
        raise HTTPException(404, "当前未启用 SSO")
    try:
        transaction, authorize_url = await sso_client.create_auth_transaction(db)
    except (SsoError, httpx.HTTPError) as exc:
        raise HTTPException(502, "SSO 暂时不可用") from exc
    response = RedirectResponse(authorize_url, status_code=302)
    response.set_cookie(
        settings.SSO_TRANSACTION_COOKIE_NAME, transaction, max_age=120,
        httponly=True, secure=settings.SSO_COOKIE_SECURE, samesite="lax", path="/",
    )
    return response


@router.get("/sso/callback", summary="SSO 登录回调")
async def sso_callback(
    code: Optional[str] = Query(None), state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    transaction: Optional[str] = Cookie(None, alias=settings.SSO_TRANSACTION_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
):
    frontend = settings.SSO_FRONTEND_REDIRECT_URI
    if settings.auth_mode != "sso":
        raise HTTPException(404, "当前未启用 SSO")
    if error or not code or not state or not transaction:
        return RedirectResponse(f"{frontend}?error=sso_login_failed", status_code=302)
    try:
        session_handle = await sso_client.complete_callback(db, transaction, state, code)
    except (SsoError, httpx.HTTPError, jwt.PyJWTError):
        response = RedirectResponse(f"{frontend}?error=sso_login_failed", status_code=302)
        response.delete_cookie(settings.SSO_TRANSACTION_COOKIE_NAME, path="/")
        return response
    response = RedirectResponse(frontend, status_code=302)
    response.set_cookie(
        settings.SSO_SESSION_COOKIE_NAME, session_handle,
        max_age=settings.SSO_SESSION_MAX_AGE_SECONDS, httponly=True,
        secure=settings.SSO_COOKIE_SECURE, samesite="lax", path="/",
    )
    response.delete_cookie(settings.SSO_TRANSACTION_COOKIE_NAME, path="/")
    return response


@router.post("/register", response_model=CommonResponse[UserInfo], summary="用户注册")
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    _require_local_mode()
    """
    用户注册接口
    
    - **username**: 用户名（3-32个字符，只能包含字母、数字、下划线和连字符）
    - **password**: 密码（6-32个字符）
    - **nickname**: 昵称（可选）
    - **email**: 邮箱地址（可选）
    
    返回新创建的用户信息
    """
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == register_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )
    
    # 检查邮箱是否已存在（如果提供了邮箱）
    if register_data.email:
        result = await db.execute(
            select(User).where(User.email == register_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="邮箱已被注册",
            )
    
    # 所有公开注册用户固定为 viewer，角色提升通过申请或管理员直接修改。
    role_result = await db.execute(
        select(Role).where(Role.code == "viewer", Role.enabled == True)
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="viewer 角色未初始化",
        )
    
    # 加密密码
    hashed_password = get_password_hash(register_data.password)
    
    # 创建新用户
    new_user = User(
        id=generate_id("user"),
        username=register_data.username,
        password=hashed_password,
        nickname=register_data.nickname or register_data.username,
        email=register_data.email,
        role=role.id,  # 使用角色 ID
        status="active"
    )
    
    db.add(new_user)
    new_user.role_code = "viewer"
    _auth_log(db, new_user, "create", f"用户注册 {new_user.username}", new_user.id)
    await db.commit()
    await db.refresh(new_user)
    
    # 构造用户信息
    user_info = UserInfo(
        id=new_user.id,
        username=new_user.username,
        nickname=new_user.nickname,
        role="viewer",
        email=new_user.email,
        avatar=new_user.avatar,
        permissions=sorted(get_role_permissions("viewer")),
    )
    
    return CommonResponse(
        code=200,
        message="注册成功",
        data=user_info
    )


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    login_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    _require_local_mode()
    """
    用户登录接口
    
    - **username**: 用户名
    - **password**: 密码
    - **remember**: 是否记住登录状态（可选）
    
    返回 JWT Token 和用户信息
    """
    try:
        # 查询用户及其角色信息
        result = await db.execute(
            select(User, Role)
            .join(Role, User.role == Role.id)
            .where(User.username == login_data.username)
        )
        user_role = result.first()
    except SQLAlchemyError:
        return _mock_login(login_data, response)
    
    # 验证用户名和密码
    if not user_role:
        if login_data.username in {"admin", "user"}:
            return _mock_login(login_data, response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    user, role = user_role
    
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    # 检查用户状态
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    # 检查角色是否启用
    if not role.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户角色已被禁用",
        )
    
    # 创建 Token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    # 设置 Cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        max_age=settings.COOKIE_MAX_AGE,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/"
    )
    
    # 构造用户信息
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        role=role.code,  # 返回角色代码
        email=user.email,
        avatar=user.avatar,
        permissions=sorted(get_role_permissions(role.code)),
    )
    
    # 构造响应
    token_data = TokenData(
        token=access_token,
        userInfo=user_info,
        expiresIn=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return LoginResponse(
        code=200,
        message="登录成功",
        data=token_data
    )


def _mock_login(login_data: LoginRequest, response: Response) -> LoginResponse:
    """Local fallback for frontend/backend development without MySQL."""
    allowed = {
        "admin": {"passwords": {"admin", "admin123", "orangepi"}, "role": "admin"},
        "user": {"passwords": {"user"}, "role": "viewer"},
    }
    account = allowed.get(login_data.username)
    if not account or login_data.password not in account["passwords"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": f"mock-{login_data.username}", "username": login_data.username},
        expires_delta=access_token_expires,
    )
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        max_age=settings.COOKIE_MAX_AGE,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )
    user_info = UserInfo(
        id=f"mock-{login_data.username}",
        username=login_data.username,
        nickname=login_data.username,
        role=account["role"],
        email=f"{login_data.username}@local.test",
        avatar=None,
        permissions=sorted(get_role_permissions(account["role"])),
    )
    return LoginResponse(
        code=200,
        message="登录成功",
        data=TokenData(
            token=access_token,
            userInfo=user_info,
            expiresIn=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


@router.post("/logout", response_model=CommonResponse, summary="用户登出")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    用户登出接口
    
    清除 Cookie 中的 Token
    """
    if settings.auth_mode == "sso":
        try:
            await sso_client.logout(current_user.sso_access_token)
        except (SsoError, httpx.HTTPError):
            pass
        await db.execute(delete(SsoSession).where(SsoSession.id == current_user.sso_session_id))
        _auth_log(db, current_user, "logout", "退出 SSO 登录", current_user.id)
        response.delete_cookie(settings.SSO_SESSION_COOKIE_NAME, path="/")
        return CommonResponse(code=200, message="退出成功", data=None)

    # 清除 Cookie
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/"
    )
    
    return CommonResponse(
        code=200,
        message="退出成功",
        data=None
    )


@router.get("/userInfo", response_model=CommonResponse[UserInfo], summary="获取当前用户信息")
async def get_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户的详细信息
    """
    if getattr(current_user, "auth_source", "local") == "sso":
        return CommonResponse(data=UserInfo(
            id=current_user.id, username=current_user.username,
            nickname=current_user.nickname, role=current_user.role_code,
            roles=current_user.roles, email=current_user.email,
            avatar=None, permissions=sorted(current_user.permission_codes), authMode="sso",
        ))

    role_code = getattr(current_user, "role_code", None)
    if not role_code:
        role = await db.get(Role, current_user.role)
        if not role:
            raise HTTPException(status_code=500, detail="用户角色信息异常")
        role_code = role.code
    
    # 构造用户信息
    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        role=role_code,
        email=current_user.email,
        avatar=current_user.avatar,
        permissions=sorted(get_role_permissions(role_code)),
    )
    
    return CommonResponse(
        code=200,
        message="获取成功",
        data=user_info
    )


@router.get("/users/search", response_model=CommonResponse[UserSearchResponse], summary="用户列表模糊搜索")
async def search_users(
    keyword: Optional[str] = Query(None, description="搜索关键词（匹配用户名、昵称、邮箱）"),
    role: Optional[str] = Query(None, description="角色代码筛选"),
    status: Optional[str] = Query(None, description="状态筛选：active / inactive"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页条数"),
    current_user: User = Depends(require_permissions(Permission.USER_VIEW.value)),
    db: AsyncSession = Depends(get_db)
):
    _require_local_mode()
    """
    用户列表模糊搜索
    
    - **keyword**: 搜索关键词（可选），匹配用户名、昵称、邮箱
    - **role**: 角色代码筛选（可选）
    - **status**: 状态筛选（可选）：active / inactive
    - **page**: 页码（默认1）
    - **pageSize**: 每页条数（默认20）
    
    返回符合条件的用户列表
    """
    # 构建基础查询
    query = select(User, Role).join(Role, User.role == Role.id)
    
    # 条件筛选
    conditions = []
    
    # 关键词搜索（用户名、昵称、邮箱）
    if keyword:
        keyword_pattern = f"%{keyword}%"
        conditions.append(
            or_(
                User.username.like(keyword_pattern),
                User.nickname.like(keyword_pattern),
                User.email.like(keyword_pattern)
            )
        )
    
    # 角色筛选
    if role:
        conditions.append(Role.code == role)
    
    # 状态筛选
    if status:
        conditions.append(User.status == status)
    
    # 应用筛选条件
    if conditions:
        query = query.where(*conditions)
    
    # 计算总数
    count_query = select(func.count()).select_from(User).join(Role, User.role == Role.id)
    if conditions:
        count_query = count_query.where(*conditions)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * pageSize
    query = query.order_by(User.create_time.desc()).offset(offset).limit(pageSize)
    
    result = await db.execute(query)
    user_roles = result.all()
    
    # 构造响应数据
    user_list = []
    for user, role in user_roles:
        user_list.append(UserListItem(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            role=role.code,
            email=user.email,
            avatar=user.avatar,
            status=user.status,
            createTime=user.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            updateTime=user.update_time.strftime("%Y-%m-%d %H:%M:%S")
        ))
    
    search_response = UserSearchResponse(
        list=user_list,
        total=total,
        page=page,
        pageSize=pageSize
    )
    
    return CommonResponse(
        code=200,
        message="获取成功",
        data=search_response
    )


@router.get("/roles", response_model=CommonResponse[list[dict]], summary="获取可用角色")
async def get_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _require_local_mode()
    roles = (await db.execute(select(Role).where(Role.enabled == True).order_by(Role.id))).scalars().all()
    return CommonResponse(data=[{"code": item.code, "name": item.name, "description": item.description} for item in roles])


@router.put("/profile", response_model=CommonResponse[UserInfo], summary="修改个人资料")
async def update_profile(
    payload: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_local_mode()
    user = await db.get(User, current_user.id)
    if not user:
        raise HTTPException(404, "用户不存在")
    if payload.email and await db.scalar(select(User).where(User.email == payload.email, User.id != user.id)):
        raise HTTPException(409, "邮箱已被使用")
    if payload.nickname is not None:
        user.nickname = payload.nickname or user.username
    user.email = payload.email
    user.update_time = datetime.now()
    _auth_log(db, current_user, "update", "修改个人资料", user.id)
    role = await db.get(Role, user.role)
    return CommonResponse(data=UserInfo(id=user.id, username=user.username, nickname=user.nickname,
        role=role.code, email=user.email, avatar=user.avatar, permissions=sorted(get_role_permissions(role.code))))


@router.put("/password", response_model=CommonResponse[None], summary="修改密码")
async def change_password(
    payload: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_local_mode()
    user = await db.get(User, current_user.id)
    if not user or not verify_password(payload.oldPassword, user.password):
        raise HTTPException(400, "原密码错误")
    user.password = get_password_hash(payload.newPassword)
    user.update_time = datetime.now()
    _auth_log(db, current_user, "update", "修改登录密码", user.id)
    return CommonResponse(data=None, message="密码修改成功")


@router.delete("/account", response_model=CommonResponse[None], summary="注销当前账号")
async def delete_account(
    payload: AccountDeleteRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_local_mode()
    user = await db.get(User, current_user.id)
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(400, "密码错误")
    role = await db.get(Role, user.role)
    if role and role.code == "admin":
        admin_count = await db.scalar(select(func.count()).select_from(User).join(Role).where(Role.code == "admin", User.status == "active"))
        if admin_count <= 1:
            raise HTTPException(409, "不能注销最后一个管理员")
    _auth_log(db, current_user, "delete", f"用户注销账号 {user.username}", user.id)
    await db.execute(delete(RoleRequest).where(RoleRequest.user_id == user.id))
    await db.delete(user)
    response.delete_cookie(key=settings.COOKIE_NAME, path="/")
    return CommonResponse(data=None, message="账号已注销")


@router.post("/role-requests", response_model=CommonResponse[dict], summary="申请角色")
async def apply_role(
    payload: RoleApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.USER_ROLE_REQUEST.value)),
):
    _require_local_mode()
    if getattr(current_user, "role_code", "") == "admin":
        raise HTTPException(400, "管理员已拥有全部权限，无需申请角色")
    if payload.role not in ASSIGNABLE_ROLES:
        raise HTTPException(400, "目标角色不可申请")
    if payload.role == getattr(current_user, "role_code", ""):
        raise HTTPException(400, "当前已经是该角色")
    if await db.scalar(select(RoleRequest).where(RoleRequest.user_id == current_user.id, RoleRequest.status == "pending")):
        raise HTTPException(409, "已有待处理的角色申请")
    item = RoleRequest(id=generate_id("role-request"), user_id=current_user.id,
        current_role=getattr(current_user, "role_code", "viewer"), requested_role=payload.role,
        reason=payload.reason, status="pending", created_at=datetime.now())
    db.add(item)
    _auth_log(db, current_user, "submit", f"申请角色 {payload.role}", current_user.id)
    return CommonResponse(data={"id": item.id, "status": item.status}, message="角色申请已提交")


def _role_request_json(item: RoleRequest, user: User) -> dict:
    return {"id": item.id, "userId": user.id, "username": user.username, "nickname": user.nickname,
        "currentRole": item.current_role, "requestedRole": item.requested_role, "reason": item.reason,
        "status": item.status, "createdAt": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "reviewComment": item.review_comment}


@router.get("/role-requests/me", response_model=CommonResponse[list[dict]], summary="我的角色申请")
async def my_role_requests(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_local_mode()
    items = (await db.execute(select(RoleRequest).where(RoleRequest.user_id == current_user.id).order_by(RoleRequest.created_at.desc()))).scalars().all()
    return CommonResponse(data=[_role_request_json(item, current_user) for item in items])


@router.get("/role-requests", response_model=CommonResponse[list[dict]], summary="角色申请列表")
async def role_requests(
    request_status: Optional[str] = Query("pending", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(Permission.USER_MANAGE.value)),
):
    _require_local_mode()
    query = select(RoleRequest, User).join(User, RoleRequest.user_id == User.id)
    if request_status:
        query = query.where(RoleRequest.status == request_status)
    rows = (await db.execute(query.order_by(RoleRequest.created_at.desc()))).all()
    return CommonResponse(data=[_role_request_json(item, user) for item, user in rows])


@router.post("/role-requests/{request_id}/{decision}", response_model=CommonResponse[None], summary="处理角色申请")
async def review_role_request(
    request_id: str,
    decision: str,
    payload: RoleReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.USER_MANAGE.value)),
):
    _require_local_mode()
    if decision not in {"approve", "reject"}:
        raise HTTPException(400, "处理动作错误")
    item = await db.get(RoleRequest, request_id)
    if not item or item.status != "pending":
        raise HTTPException(404, "待处理申请不存在")
    user = await db.get(User, item.user_id)
    if not user:
        raise HTTPException(404, "申请用户不存在")
    if decision == "approve":
        role = await db.scalar(select(Role).where(Role.code == item.requested_role, Role.enabled == True))
        if not role:
            raise HTTPException(400, "目标角色不可用")
        user.role = role.id
        user.update_time = datetime.now()
    item.status = "approved" if decision == "approve" else "rejected"
    item.reviewer_id, item.reviewed_at, item.review_comment = current_user.id, datetime.now(), payload.comment
    _auth_log(db, current_user, "approve" if decision == "approve" else "reject",
        f"{'通过' if decision == 'approve' else '驳回'} {user.username} 的角色申请", user.id)
    return CommonResponse(data=None, message="角色申请已通过" if decision == "approve" else "角色申请已驳回")


@router.put("/users/{user_id}/role", response_model=CommonResponse[None], summary="管理员修改用户角色")
async def change_user_role(
    user_id: str,
    payload: RoleChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.USER_MANAGE.value)),
):
    _require_local_mode()
    user = await db.get(User, user_id)
    role = await db.scalar(select(Role).where(Role.code == payload.role, Role.enabled == True))
    if not user or not role:
        raise HTTPException(404, "用户或角色不存在")
    current_role = await db.get(Role, user.role)
    if current_role.code == "admin" and payload.role != "admin":
        admin_count = await db.scalar(select(func.count()).select_from(User).join(Role).where(Role.code == "admin", User.status == "active"))
        if admin_count <= 1:
            raise HTTPException(409, "不能修改最后一个管理员的角色")
    user.role, user.update_time = role.id, datetime.now()
    pending_requests = (await db.execute(select(RoleRequest).where(
        RoleRequest.user_id == user.id,
        RoleRequest.status == "pending",
    ))).scalars().all()
    for item in pending_requests:
        item.status = "rejected"
        item.reviewer_id = current_user.id
        item.reviewed_at = datetime.now()
        item.review_comment = "管理员已直接修改角色"
    _auth_log(db, current_user, "update", f"修改用户 {user.username} 角色为 {role.code}", user.id)
    return CommonResponse(data=None, message="角色已更新")


@router.put("/users/{user_id}/status", response_model=CommonResponse[None], summary="管理员启用或禁用用户")
async def change_user_status(
    user_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.USER_MANAGE.value)),
):
    _require_local_mode()
    if payload.get("status") not in {"active", "inactive"}:
        raise HTTPException(400, "用户状态错误")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    role = await db.get(Role, user.role)
    if role.code == "admin" and payload["status"] == "inactive":
        admin_count = await db.scalar(select(func.count()).select_from(User).join(Role).where(Role.code == "admin", User.status == "active"))
        if admin_count <= 1:
            raise HTTPException(409, "不能禁用最后一个管理员")
    user.status, user.update_time = payload["status"], datetime.now()
    _auth_log(db, current_user, "update", f"{ '启用' if user.status == 'active' else '禁用' }用户 {user.username}", user.id)
    return CommonResponse(data=None, message="用户状态已更新")
