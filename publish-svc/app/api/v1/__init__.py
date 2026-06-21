"""
API v1
"""
from fastapi import APIRouter
from app.api.v1 import auth, facilities, interfaces, bindings, autounit, drivers, deployment, logs, exe

api_router = APIRouter()

# 注册路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(facilities.router, prefix="/facilities", tags=["设施管理"])
api_router.include_router(interfaces.router, prefix="/interfaces", tags=["界面管理"])
api_router.include_router(bindings.router, prefix="/bindings", tags=["工位绑定"])
api_router.include_router(autounit.router, prefix="/autounit", tags=["AutoUnit包管理"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["驱动包管理"])
api_router.include_router(deployment.router, prefix="/deployment", tags=["部署清单管理"])
api_router.include_router(logs.router, prefix="/logs", tags=["日志管理"])
api_router.include_router(exe.router, prefix="/exe", tags=["Exe拉取"])
