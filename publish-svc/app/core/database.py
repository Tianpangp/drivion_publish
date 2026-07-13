"""
数据库连接配置
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建声明基类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话依赖
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库（创建所有表）
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_roles()


async def seed_roles():
    """初始化发布系统固定角色，不覆盖已有角色。"""
    from sqlalchemy import select
    from app.models.user import Role

    definitions = [
        (1, "admin", "系统管理员", "Administrator", "管理用户和全部发布业务"),
        (2, "developer", "开发人员", "Developer", "维护制品草稿并提交审批"),
        (3, "tester", "测试人员", "Tester", "处理测试审批"),
        (4, "release_manager", "发布管理员", "Release manager", "处理发布和下架审批"),
        (5, "engineer", "现场工程师", "Engineer", "维护现场结构和设备绑定"),
        (6, "viewer", "查看人员", "Viewer", "只读查看发布数据"),
    ]
    async with AsyncSessionLocal() as session:
        existing_rows = (await session.execute(select(Role.id, Role.code))).all()
        existing_codes = {code for _, code in existing_rows}
        used_ids = {role_id for role_id, _ in existing_rows}
        next_id = max(used_ids, default=0) + 1
        for role_id, code, name, name_en, description in definitions:
            if code in existing_codes:
                continue
            assigned_id = role_id
            if assigned_id in used_ids:
                assigned_id = next_id
                next_id += 1
            used_ids.add(assigned_id)
            session.add(Role(id=assigned_id, code=code, name=name, name_en=name_en, description=description, enabled=True))
        await session.commit()


async def close_db():
    """
    关闭数据库连接
    """
    await engine.dispose()
