"""
权限配置和管理
"""
from enum import Enum
from typing import Dict, List, Set


class PermissionCategory(str, Enum):
    """权限分类"""
    FACILITY = "facility"          # 设施管理
    AUTOUNIT = "autounit"          # AutoUnit 包管理
    DRIVER = "driver"              # 驱动包管理
    INTERFACE = "interface"        # 界面管理
    DEPLOYMENT = "deployment"      # 部署清单管理
    BINDING = "binding"            # 绑定管理
    LOG = "log"                    # 日志管理
    USER = "user"                  # 用户管理
    SYSTEM = "system"              # 系统管理


class Permission(str, Enum):
    """系统权限枚举"""
    
    # ========== 设施管理权限 ==========
    # 厂区权限
    FACILITY_FACTORY_VIEW = "facility:factory:view"          # 查看厂区
    FACILITY_FACTORY_CREATE = "facility:factory:create"      # 创建厂区
    FACILITY_FACTORY_EDIT = "facility:factory:edit"          # 编辑厂区
    FACILITY_FACTORY_DELETE = "facility:factory:delete"      # 删除厂区
    
    # 线体权限
    FACILITY_LINE_VIEW = "facility:line:view"                # 查看线体
    FACILITY_LINE_CREATE = "facility:line:create"            # 创建线体
    FACILITY_LINE_EDIT = "facility:line:edit"                # 编辑线体
    FACILITY_LINE_DELETE = "facility:line:delete"            # 删除线体
    
    # 工位权限
    FACILITY_STATION_VIEW = "facility:station:view"          # 查看工位
    FACILITY_STATION_CREATE = "facility:station:create"      # 创建工位
    FACILITY_STATION_EDIT = "facility:station:edit"          # 编辑工位
    FACILITY_STATION_DELETE = "facility:station:delete"      # 删除工位
    FACILITY_EQUIPMENT_VIEW = "facility:equipment:view"
    FACILITY_EQUIPMENT_MANAGE = "facility:equipment:manage"
    
    # ========== AutoUnit 包管理权限 ==========
    AUTOUNIT_VIEW = "autounit:view"                          # 查看 AutoUnit 包
    AUTOUNIT_UPLOAD = "autounit:upload"                      # 上传 AutoUnit 包
    AUTOUNIT_DOWNLOAD = "autounit:download"                  # 下载 AutoUnit 包
    AUTOUNIT_DELETE = "autounit:delete"                      # 删除 AutoUnit 包
    AUTOUNIT_PUBLISH = "autounit:publish"                    # 发布 AutoUnit 包
    AUTOUNIT_RECALL = "autounit:recall"                      # 撤回 AutoUnit 包
    AUTOUNIT_APPLY = "autounit:apply"                        # 应用 AutoUnit 包到工位
    AUTOUNIT_MANAGE_DRAFT = "autounit:manage_draft"
    AUTOUNIT_SUBMIT_TEST = "autounit:submit_test"
    AUTOUNIT_SUBMIT_PUBLISH = "autounit:submit_publish"
    AUTOUNIT_SUBMIT_REMOVE = "autounit:submit_remove"
    
    # ========== 驱动包管理权限 ==========
    DRIVER_VIEW = "driver:view"                              # 查看驱动包
    DRIVER_UPLOAD = "driver:upload"                          # 上传驱动包
    DRIVER_DOWNLOAD = "driver:download"                      # 下载驱动包
    DRIVER_DELETE = "driver:delete"                          # 删除驱动包
    DRIVER_PUBLISH = "driver:publish"                        # 发布驱动包
    DRIVER_UNPUBLISH = "driver:unpublish"                    # 下架驱动包
    DRIVER_RECALL = "driver:recall"                          # 撤回驱动包
    DRIVER_MANAGE_DRAFT = "driver:manage_draft"
    DRIVER_SUBMIT_TEST = "driver:submit_test"
    DRIVER_SUBMIT_PUBLISH = "driver:submit_publish"
    DRIVER_SUBMIT_REMOVE = "driver:submit_remove"

    APPROVAL_TEST_VIEW = "approval:test:view"
    APPROVAL_TEST_REVIEW = "approval:test:review"
    APPROVAL_RELEASE_VIEW = "approval:release:view"
    APPROVAL_RELEASE_REVIEW = "approval:release:review"
    BINDING_AUTOUNIT_MANAGE = "binding:autounit:manage"
    
    # ========== 界面管理权限 ==========
    INTERFACE_VIEW = "interface:view"                        # 查看界面
    INTERFACE_CREATE = "interface:create"                    # 创建界面
    INTERFACE_EDIT = "interface:edit"                        # 编辑界面
    INTERFACE_DELETE = "interface:delete"                    # 删除界面
    INTERFACE_CONFIG = "interface:config"                    # 配置界面
    INTERFACE_PREVIEW = "interface:preview"                  # 预览界面
    
    # ========== 部署清单管理权限 ==========
    DEPLOYMENT_VIEW = "deployment:view"                      # 查看部署清单
    DEPLOYMENT_UPLOAD = "deployment:upload"                  # 上传部署清单
    DEPLOYMENT_DOWNLOAD = "deployment:download"              # 下载部署清单
    DEPLOYMENT_EDIT = "deployment:edit"                      # 编辑部署清单
    DEPLOYMENT_DELETE = "deployment:delete"                  # 删除部署清单
    DEPLOYMENT_BIND = "deployment:bind"                      # 绑定/解绑部署清单
    
    # ========== 绑定管理权限 ==========
    BINDING_VIEW = "binding:view"                            # 查看绑定关系
    BINDING_INTERFACE = "binding:interface"                  # 绑定/解绑界面
    BINDING_MANIFEST = "binding:manifest"                    # 绑定/解绑部署清单（已废弃，使用DEPLOYMENT_BIND）
    
    # ========== 日志管理权限 ==========
    LOG_VIEW = "log:view"                                    # 查看日志
    LOG_EXPORT = "log:export"                                # 导出日志
    LOG_DELETE = "log:delete"                                # 删除日志
    
    # ========== 用户管理权限 ==========
    USER_VIEW = "user:view"                                  # 查看用户
    USER_CREATE = "user:create"                              # 创建用户
    USER_EDIT = "user:edit"                                  # 编辑用户
    USER_DELETE = "user:delete"                              # 删除用户
    USER_ASSIGN_ROLE = "user:assign_role"                    # 分配角色
    USER_ASSIGN_PERMISSION = "user:assign_permission"        # 分配权限
    USER_ROLE_REQUEST = "user:role_request"
    USER_MANAGE = "user:manage"
    
    # ========== 系统管理权限 ==========
    SYSTEM_CONFIG = "system:config"                          # 系统配置
    SYSTEM_BACKUP = "system:backup"                          # 系统备份
    SYSTEM_RESTORE = "system:restore"                        # 系统恢复


# 权限描述映射
PERMISSION_DESCRIPTIONS: Dict[str, str] = {
    # 设施管理
    Permission.FACILITY_FACTORY_VIEW: "查看厂区信息",
    Permission.FACILITY_FACTORY_CREATE: "创建新厂区",
    Permission.FACILITY_FACTORY_EDIT: "编辑厂区信息",
    Permission.FACILITY_FACTORY_DELETE: "删除厂区",
    Permission.FACILITY_LINE_VIEW: "查看线体信息",
    Permission.FACILITY_LINE_CREATE: "创建新线体",
    Permission.FACILITY_LINE_EDIT: "编辑线体信息",
    Permission.FACILITY_LINE_DELETE: "删除线体",
    Permission.FACILITY_STATION_VIEW: "查看工位信息",
    Permission.FACILITY_STATION_CREATE: "创建新工位",
    Permission.FACILITY_STATION_EDIT: "编辑工位信息",
    Permission.FACILITY_STATION_DELETE: "删除工位",
    
    # AutoUnit 包管理
    Permission.AUTOUNIT_VIEW: "查看 AutoUnit 包列表和详情",
    Permission.AUTOUNIT_UPLOAD: "上传新的 AutoUnit 包",
    Permission.AUTOUNIT_DOWNLOAD: "下载 AutoUnit 包",
    Permission.AUTOUNIT_DELETE: "删除 AutoUnit 包",
    Permission.AUTOUNIT_PUBLISH: "发布 AutoUnit 包",
    Permission.AUTOUNIT_RECALL: "撤回已发布的 AutoUnit 包",
    Permission.AUTOUNIT_APPLY: "应用 AutoUnit 包到工位",
    
    # 驱动包管理
    Permission.DRIVER_VIEW: "查看驱动包列表和详情",
    Permission.DRIVER_UPLOAD: "上传新的驱动包",
    Permission.DRIVER_DOWNLOAD: "下载驱动包",
    Permission.DRIVER_DELETE: "删除驱动包",
    Permission.DRIVER_PUBLISH: "发布驱动包",
    Permission.DRIVER_UNPUBLISH: "下架驱动包",
    Permission.DRIVER_RECALL: "撤回驱动包",
    
    # 界面管理
    Permission.INTERFACE_VIEW: "查看界面列表和详情",
    Permission.INTERFACE_CREATE: "创建新界面",
    Permission.INTERFACE_EDIT: "编辑界面信息",
    Permission.INTERFACE_DELETE: "删除界面",
    Permission.INTERFACE_CONFIG: "配置界面详细参数",
    Permission.INTERFACE_PREVIEW: "预览界面效果",
    
    # 部署清单管理
    Permission.DEPLOYMENT_VIEW: "查看部署清单列表和详情",
    Permission.DEPLOYMENT_UPLOAD: "上传新的部署清单",
    Permission.DEPLOYMENT_DOWNLOAD: "下载部署清单",
    Permission.DEPLOYMENT_EDIT: "编辑部署清单",
    Permission.DEPLOYMENT_DELETE: "删除部署清单",
    
    # 绑定管理
    Permission.BINDING_VIEW: "查看工位绑定关系",
    Permission.BINDING_INTERFACE: "绑定/解绑界面到工位",
    Permission.BINDING_MANIFEST: "绑定/解绑部署清单到工位",
    
    # 日志管理
    Permission.LOG_VIEW: "查看操作日志",
    Permission.LOG_EXPORT: "导出日志文件",
    Permission.LOG_DELETE: "删除日志记录",
    
    # 用户管理
    Permission.USER_VIEW: "查看用户列表和信息",
    Permission.USER_CREATE: "创建新用户",
    Permission.USER_EDIT: "编辑用户信息",
    Permission.USER_DELETE: "删除用户",
    Permission.USER_ASSIGN_ROLE: "为用户分配角色",
    Permission.USER_ASSIGN_PERMISSION: "为用户分配权限",
    
    # 系统管理
    Permission.SYSTEM_CONFIG: "修改系统配置",
    Permission.SYSTEM_BACKUP: "备份系统数据",
    Permission.SYSTEM_RESTORE: "恢复系统数据",
}


# 权限分组
PERMISSION_GROUPS: Dict[PermissionCategory, List[Permission]] = {
    PermissionCategory.FACILITY: [
        Permission.FACILITY_FACTORY_VIEW,
        Permission.FACILITY_FACTORY_CREATE,
        Permission.FACILITY_FACTORY_EDIT,
        Permission.FACILITY_FACTORY_DELETE,
        Permission.FACILITY_LINE_VIEW,
        Permission.FACILITY_LINE_CREATE,
        Permission.FACILITY_LINE_EDIT,
        Permission.FACILITY_LINE_DELETE,
        Permission.FACILITY_STATION_VIEW,
        Permission.FACILITY_STATION_CREATE,
        Permission.FACILITY_STATION_EDIT,
        Permission.FACILITY_STATION_DELETE,
    ],
    PermissionCategory.AUTOUNIT: [
        Permission.AUTOUNIT_VIEW,
        Permission.AUTOUNIT_UPLOAD,
        Permission.AUTOUNIT_DOWNLOAD,
        Permission.AUTOUNIT_DELETE,
        Permission.AUTOUNIT_PUBLISH,
        Permission.AUTOUNIT_RECALL,
        Permission.AUTOUNIT_APPLY,
    ],
    PermissionCategory.DRIVER: [
        Permission.DRIVER_VIEW,
        Permission.DRIVER_UPLOAD,
        Permission.DRIVER_DOWNLOAD,
        Permission.DRIVER_DELETE,
        Permission.DRIVER_PUBLISH,
        Permission.DRIVER_UNPUBLISH,
        Permission.DRIVER_RECALL,
    ],
    PermissionCategory.INTERFACE: [
        Permission.INTERFACE_VIEW,
        Permission.INTERFACE_CREATE,
        Permission.INTERFACE_EDIT,
        Permission.INTERFACE_DELETE,
        Permission.INTERFACE_CONFIG,
        Permission.INTERFACE_PREVIEW,
    ],
    PermissionCategory.DEPLOYMENT: [
        Permission.DEPLOYMENT_VIEW,
        Permission.DEPLOYMENT_UPLOAD,
        Permission.DEPLOYMENT_DOWNLOAD,
        Permission.DEPLOYMENT_EDIT,
        Permission.DEPLOYMENT_DELETE,
    ],
    PermissionCategory.BINDING: [
        Permission.BINDING_VIEW,
        Permission.BINDING_INTERFACE,
        Permission.BINDING_MANIFEST,
    ],
    PermissionCategory.LOG: [
        Permission.LOG_VIEW,
        Permission.LOG_EXPORT,
        Permission.LOG_DELETE,
    ],
    PermissionCategory.USER: [
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.USER_EDIT,
        Permission.USER_DELETE,
        Permission.USER_ASSIGN_ROLE,
        Permission.USER_ASSIGN_PERMISSION,
    ],
    PermissionCategory.SYSTEM: [
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_BACKUP,
        Permission.SYSTEM_RESTORE,
    ],
}


class RoleType(str, Enum):
    """系统角色类型"""
    ADMIN = "admin"                      # 系统管理员
    DEVELOPER = "developer"              # 开发人员
    TESTER = "tester"                    # 测试人员
    PROJECT_MANAGER = "project_manager"  # 项目经理
    OPERATOR = "operator"                # 操作员
    PROCESS_ENGINEER = "process_engineer"  # 工艺工程师
    RELEASE_MANAGER = "release_manager"
    ENGINEER = "engineer"
    VIEWER = "viewer"


# 角色权限映射
ROLE_PERMISSIONS: Dict[RoleType, Set[Permission]] = {
    # 系统管理员 - 拥有所有权限
    RoleType.ADMIN: set(Permission),
    
    # 开发人员 - 可以上传驱动/包、创建工位和线体,但不能创建厂区
    RoleType.DEVELOPER: {
        # AutoUnit 包 - 上传和管理
        Permission.AUTOUNIT_VIEW,
        Permission.AUTOUNIT_UPLOAD,
        Permission.AUTOUNIT_DOWNLOAD,
        Permission.AUTOUNIT_DELETE,
        Permission.AUTOUNIT_APPLY,
        
        # 驱动包 - 上传和管理
        Permission.DRIVER_VIEW,
        Permission.DRIVER_UPLOAD,
        Permission.DRIVER_DOWNLOAD,
        Permission.DRIVER_DELETE,
        
        # 界面 - 全权限
        Permission.INTERFACE_VIEW,
        Permission.INTERFACE_CREATE,
        Permission.INTERFACE_EDIT,
        Permission.INTERFACE_DELETE,
        Permission.INTERFACE_CONFIG,
        Permission.INTERFACE_PREVIEW,
        
        # 部署清单 - 全权限
        Permission.DEPLOYMENT_VIEW,
        Permission.DEPLOYMENT_UPLOAD,
        Permission.DEPLOYMENT_DOWNLOAD,
        Permission.DEPLOYMENT_EDIT,
        Permission.DEPLOYMENT_DELETE,
        
        # 绑定 - 全权限
        Permission.BINDING_VIEW,
        Permission.BINDING_INTERFACE,
        Permission.BINDING_MANIFEST,
        
        # 设施 - 可以创建线体和工位,不能创建厂区
        Permission.FACILITY_FACTORY_VIEW,
        Permission.FACILITY_LINE_VIEW,
        Permission.FACILITY_LINE_CREATE,
        Permission.FACILITY_LINE_EDIT,
        Permission.FACILITY_LINE_DELETE,
        Permission.FACILITY_STATION_VIEW,
        Permission.FACILITY_STATION_CREATE,
        Permission.FACILITY_STATION_EDIT,
        Permission.FACILITY_STATION_DELETE,
        
        # 日志查看
        Permission.LOG_VIEW,
    },
    
    # 测试人员 - 测试环境与用例管理权限
    RoleType.TESTER: {
        # 查看所有资源
        Permission.FACILITY_FACTORY_VIEW,
        Permission.FACILITY_LINE_VIEW,
        Permission.FACILITY_STATION_VIEW,
        Permission.AUTOUNIT_VIEW,
        Permission.AUTOUNIT_DOWNLOAD,
        Permission.DRIVER_VIEW,
        Permission.DRIVER_DOWNLOAD,
        Permission.INTERFACE_VIEW,
        Permission.INTERFACE_PREVIEW,
        Permission.DEPLOYMENT_VIEW,
        Permission.DEPLOYMENT_DOWNLOAD,
        Permission.BINDING_VIEW,
        
        # 应用包到工位进行测试
        Permission.AUTOUNIT_APPLY,
        
        # 绑定界面和清单进行测试
        Permission.BINDING_INTERFACE,
        Permission.BINDING_MANIFEST,
        
        # 日志查看
        Permission.LOG_VIEW,
        Permission.LOG_EXPORT,
    },
    
    # 项目经理 - 可以审批所有包和驱动等操作
    RoleType.PROJECT_MANAGER: {
        # AutoUnit 包 - 审批(发布/撤回)
        Permission.AUTOUNIT_VIEW,
        Permission.AUTOUNIT_DOWNLOAD,
        Permission.AUTOUNIT_PUBLISH,
        Permission.AUTOUNIT_RECALL,
        
        # 驱动包 - 审批(发布/下架/撤回)
        Permission.DRIVER_VIEW,
        Permission.DRIVER_DOWNLOAD,
        Permission.DRIVER_PUBLISH,
        Permission.DRIVER_UNPUBLISH,
        Permission.DRIVER_RECALL,
        
        # 界面 - 查看和预览
        Permission.INTERFACE_VIEW,
        Permission.INTERFACE_PREVIEW,
        
        # 部署清单 - 查看
        Permission.DEPLOYMENT_VIEW,
        Permission.DEPLOYMENT_DOWNLOAD,
        
        # 设施 - 查看权限
        Permission.FACILITY_FACTORY_VIEW,
        Permission.FACILITY_LINE_VIEW,
        Permission.FACILITY_STATION_VIEW,
        
        # 绑定 - 查看
        Permission.BINDING_VIEW,
        
        # 日志 - 查看和导出
        Permission.LOG_VIEW,
        Permission.LOG_EXPORT,
        
        # 用户管理 - 查看用户
        Permission.USER_VIEW,
    },
    
    # 操作员 - 一线操作人员,具备生产运行相关权限
    RoleType.OPERATOR: {
        # 查看权限
        Permission.FACILITY_FACTORY_VIEW,
        Permission.FACILITY_LINE_VIEW,
        Permission.FACILITY_STATION_VIEW,
        Permission.AUTOUNIT_VIEW,
        Permission.AUTOUNIT_DOWNLOAD,
        Permission.DRIVER_VIEW,
        Permission.DRIVER_DOWNLOAD,
        Permission.INTERFACE_VIEW,
        Permission.INTERFACE_PREVIEW,
        Permission.DEPLOYMENT_VIEW,
        Permission.DEPLOYMENT_DOWNLOAD,
        
        # 应用和绑定权限
        Permission.AUTOUNIT_APPLY,
        Permission.BINDING_VIEW,
        Permission.BINDING_INTERFACE,
        Permission.BINDING_MANIFEST,
        
        # 日志查看
        Permission.LOG_VIEW,
    },
    
    # 工艺工程师 - 负责工艺参数与流程维护
    RoleType.PROCESS_ENGINEER: {
        # 设施管理 - 编辑工位和线体
        Permission.FACILITY_FACTORY_VIEW,
        Permission.FACILITY_LINE_VIEW,
        Permission.FACILITY_LINE_EDIT,
        Permission.FACILITY_STATION_VIEW,
        Permission.FACILITY_STATION_EDIT,
        
        # 界面 - 配置界面
        Permission.INTERFACE_VIEW,
        Permission.INTERFACE_EDIT,
        Permission.INTERFACE_CONFIG,
        Permission.INTERFACE_PREVIEW,
        
        # 部署清单 - 编辑
        Permission.DEPLOYMENT_VIEW,
        Permission.DEPLOYMENT_DOWNLOAD,
        Permission.DEPLOYMENT_EDIT,
        
        # 绑定 - 全权限
        Permission.BINDING_VIEW,
        Permission.BINDING_INTERFACE,
        Permission.BINDING_MANIFEST,
        
        # 查看包和驱动
        Permission.AUTOUNIT_VIEW,
        Permission.AUTOUNIT_DOWNLOAD,
        Permission.AUTOUNIT_APPLY,
        Permission.DRIVER_VIEW,
        Permission.DRIVER_DOWNLOAD,
        
        # 日志查看
        Permission.LOG_VIEW,
    },
}


# 角色描述映射
ROLE_DESCRIPTIONS: Dict[RoleType, str] = {
    RoleType.ADMIN: "系统管理员 - 拥有系统所有权限",
    RoleType.DEVELOPER: "开发人员 - 负责包开发、界面开发、部署配置,可创建线体和工位",
    RoleType.TESTER: "测试人员 - 负责测试环境与用例管理,可应用包和绑定资源",
    RoleType.PROJECT_MANAGER: "项目经理 - 负责项目管理与资源调度,可审批包和驱动的发布",
    RoleType.OPERATOR: "操作员 - 一线操作人员,具备生产运行相关权限",
    RoleType.PROCESS_ENGINEER: "工艺工程师 - 负责工艺参数与流程维护,可配置界面和编辑设施",
}

# 发布系统内置角色。旧角色权限保留给兼容接口，新主流程只分配以下角色。
_PUBLISH_VIEW = {
    Permission.FACILITY_FACTORY_VIEW, Permission.FACILITY_LINE_VIEW,
    Permission.FACILITY_STATION_VIEW, Permission.FACILITY_EQUIPMENT_VIEW,
    Permission.AUTOUNIT_VIEW, Permission.AUTOUNIT_DOWNLOAD,
    Permission.DRIVER_VIEW, Permission.DRIVER_DOWNLOAD,
    Permission.BINDING_VIEW, Permission.LOG_VIEW,
}
ROLE_PERMISSIONS[RoleType.VIEWER] = set(_PUBLISH_VIEW) | {Permission.USER_ROLE_REQUEST}
ROLE_PERMISSIONS[RoleType.DEVELOPER] |= _PUBLISH_VIEW | {
    Permission.AUTOUNIT_MANAGE_DRAFT, Permission.AUTOUNIT_SUBMIT_TEST,
    Permission.AUTOUNIT_SUBMIT_PUBLISH, Permission.AUTOUNIT_SUBMIT_REMOVE,
    Permission.DRIVER_MANAGE_DRAFT, Permission.DRIVER_SUBMIT_TEST,
    Permission.DRIVER_SUBMIT_PUBLISH, Permission.DRIVER_SUBMIT_REMOVE,
    Permission.USER_ROLE_REQUEST,
}
ROLE_PERMISSIONS[RoleType.TESTER] = _PUBLISH_VIEW | {
    Permission.APPROVAL_TEST_VIEW, Permission.APPROVAL_TEST_REVIEW,
    Permission.USER_ROLE_REQUEST,
}
ROLE_PERMISSIONS[RoleType.RELEASE_MANAGER] = _PUBLISH_VIEW | {
    Permission.APPROVAL_RELEASE_VIEW, Permission.APPROVAL_RELEASE_REVIEW,
    Permission.USER_ROLE_REQUEST,
}
ROLE_PERMISSIONS[RoleType.ENGINEER] = _PUBLISH_VIEW | {
    Permission.FACILITY_FACTORY_CREATE, Permission.FACILITY_FACTORY_EDIT, Permission.FACILITY_FACTORY_DELETE,
    Permission.FACILITY_LINE_CREATE, Permission.FACILITY_LINE_EDIT, Permission.FACILITY_LINE_DELETE,
    Permission.FACILITY_STATION_CREATE, Permission.FACILITY_STATION_EDIT, Permission.FACILITY_STATION_DELETE,
    Permission.FACILITY_EQUIPMENT_MANAGE, Permission.BINDING_AUTOUNIT_MANAGE,
    Permission.USER_ROLE_REQUEST,
}
ROLE_DESCRIPTIONS.update({
    RoleType.RELEASE_MANAGER: "发布管理员 - 审批发布、重新上架和下架",
    RoleType.ENGINEER: "现场工程师 - 管理现场结构和设备绑定",
    RoleType.VIEWER: "查看人员 - 只读查看发布系统数据",
})


def get_role_permissions(role: str) -> Set[str]:
    """
    获取角色的所有权限
    
    Args:
        role: 角色代码
        
    Returns:
        权限代码集合
    """
    try:
        role_type = RoleType(role)
        return {perm.value for perm in ROLE_PERMISSIONS.get(role_type, set())}
    except ValueError:
        return set()


def has_permission(role: str, permission: str) -> bool:
    """
    检查角色是否拥有指定权限
    
    Args:
        role: 角色代码
        permission: 权限代码
        
    Returns:
        是否拥有权限
    """
    # 管理员拥有所有权限
    if role == RoleType.ADMIN.value:
        return True
    
    role_perms = get_role_permissions(role)
    return permission in role_perms


def get_all_permissions() -> List[Dict[str, str]]:
    """
    获取所有权限列表
    
    Returns:
        权限列表,包含权限代码和描述
    """
    return [
        {
            "code": perm.value,
            "description": PERMISSION_DESCRIPTIONS.get(perm, ""),
            "category": _get_permission_category(perm)
        }
        for perm in Permission
    ]


def _get_permission_category(permission: Permission) -> str:
    """获取权限所属分类"""
    for category, perms in PERMISSION_GROUPS.items():
        if permission in perms:
            return category.value
    return "unknown"


def get_permissions_by_category() -> Dict[str, List[Dict[str, str]]]:
    """
    按分类获取权限列表
    
    Returns:
        分类权限字典
    """
    result = {}
    for category, perms in PERMISSION_GROUPS.items():
        result[category.value] = [
            {
                "code": perm.value,
                "description": PERMISSION_DESCRIPTIONS.get(perm, "")
            }
            for perm in perms
        ]
    return result


def get_role_info(role: str) -> Dict:
    """
    获取角色信息
    
    Args:
        role: 角色代码
        
    Returns:
        角色信息字典
    """
    try:
        role_type = RoleType(role)
        return {
            "code": role_type.value,
            "description": ROLE_DESCRIPTIONS.get(role_type, ""),
            "permissions": list(get_role_permissions(role))
        }
    except ValueError:
        return {
            "code": role,
            "description": "未知角色",
            "permissions": []
        }


def get_all_roles() -> List[Dict]:
    """
    获取所有角色信息
    
    Returns:
        角色列表
    """
    return [get_role_info(role.value) for role in RoleType]
