"""
认证相关 schemas
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=32, description="用户名，3-32个字符")
    password: str = Field(..., min_length=6, max_length=32, description="密码，6-32个字符")
    nickname: Optional[str] = Field(None, max_length=64, description="昵称")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    remember: Optional[bool] = Field(False, description="是否记住登录状态")


class UserInfo(BaseModel):
    """用户信息"""
    id: str
    username: str
    nickname: Optional[str] = None
    role: str  # 角色代码（如：admin, developer等）
    email: Optional[str] = None
    avatar: Optional[str] = None
    permissions: List[str] = []
    roles: List[str] = []
    authMode: str = "local"
    
    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    """用户列表项"""
    id: str
    username: str
    nickname: Optional[str] = None
    role: str  # 角色代码
    email: Optional[str] = None
    avatar: Optional[str] = None
    status: str  # active / inactive
    createTime: str
    updateTime: str
    
    class Config:
        from_attributes = True


class UserSearchResponse(BaseModel):
    """用户搜索响应数据"""
    list: List[UserListItem]
    total: int
    page: int
    pageSize: int


class TokenData(BaseModel):
    """Token数据"""
    token: str
    userInfo: UserInfo
    expiresIn: int  # Token过期时间（秒）


class LoginResponse(BaseModel):
    """登录响应"""
    code: int = 200
    message: str = "登录成功"
    data: TokenData


class RoleChangeRequest(BaseModel):
    role: str


class RoleApplyRequest(BaseModel):
    role: str
    reason: Optional[str] = Field(None, max_length=500)


class RoleReviewRequest(BaseModel):
    comment: Optional[str] = Field(None, max_length=500)


class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=64)
    email: Optional[EmailStr] = None


class PasswordChangeRequest(BaseModel):
    oldPassword: str
    newPassword: str = Field(..., min_length=6, max_length=32)


class AccountDeleteRequest(BaseModel):
    password: str
