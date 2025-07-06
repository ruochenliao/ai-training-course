"""
数据库配置模块
配置Tortoise ORM数据库连接和初始化
"""

from tortoise import Tortoise
from app.core.config import settings


# Tortoise ORM配置
TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "app.models.role",
                "app.models.permission",
                "app.models.menu",
                "app.models.department",
                "app.models.audit_log",
                "app.models.data_permission",
                "aerich.models"
            ],
            "default_connection": "default",
        },
    },
}


async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    """关闭数据库连接"""
    await Tortoise.close_connections()


async def create_superuser():
    """创建超级管理员用户"""
    from app.models.user import User
    from app.models.role import Role
    from app.models.permission import Permission
    from app.models.menu import Menu
    from app.models.department import Department
    from app.core.security import get_password_hash
    
    # 检查是否已存在超级管理员
    admin_user = await User.filter(username="admin").first()
    if admin_user:
        print("超级管理员已存在")
        return
    
    # 创建超级管理员角色
    super_admin_role = await Role.get_or_none(code="super_admin")
    if not super_admin_role:
        super_admin_role = await Role.create(
            name="超级管理员",
            code="super_admin",
            description="系统超级管理员，拥有所有权限",
            is_active=True,
            sort_order=1
        )

    # 创建系统管理员角色
    system_admin_role = await Role.get_or_none(code="system_admin")
    if not system_admin_role:
        system_admin_role = await Role.create(
            name="系统管理员",
            code="system_admin",
            description="系统管理员，拥有用户和角色管理权限",
            is_active=True,
            sort_order=2
        )

    # 创建普通用户角色
    normal_user_role = await Role.get_or_none(code="normal_user")
    if not normal_user_role:
        normal_user_role = await Role.create(
            name="普通用户",
            code="normal_user",
            description="普通用户，只有基础查看权限",
            is_active=True,
            sort_order=3
        )
    
    # 创建权限 - 先创建父级权限，再创建子权限
    # 第一步：创建顶级模块权限
    top_level_permissions = [
        {"name": "系统管理", "code": "system:manage", "module": "系统管理", "resource": "system", "action": "manage", "type": "模块"},
        {"name": "用户管理", "code": "user:manage", "module": "用户管理", "resource": "user", "action": "manage", "type": "模块"},
        {"name": "角色管理", "code": "role:manage", "module": "角色管理", "resource": "role", "action": "manage", "type": "模块"},
        {"name": "权限管理", "code": "permission:manage", "module": "权限管理", "resource": "permission", "action": "manage", "type": "模块"},
        {"name": "菜单管理", "code": "menu:manage", "module": "菜单管理", "resource": "menu", "action": "manage", "type": "模块"},
        {"name": "部门管理", "code": "department:manage", "module": "部门管理", "resource": "department", "action": "manage", "type": "模块"},
    ]

    # 创建顶级权限
    created_top_permissions = {}
    for perm_data in top_level_permissions:
        existing_perm = await Permission.get_or_none(code=perm_data["code"])
        if not existing_perm:
            perm = await Permission.create(**perm_data)
            created_top_permissions[perm_data["code"]] = perm
        else:
            created_top_permissions[perm_data["code"]] = existing_perm

    # 第二步：创建子权限
    child_permissions_data = [
        # 用户管理子权限
        {"name": "用户查看", "code": "user:read", "module": "用户管理", "resource": "user", "action": "read", "parent_code": "user:manage"},
        {"name": "用户创建", "code": "user:create", "module": "用户管理", "resource": "user", "action": "create", "parent_code": "user:manage"},
        {"name": "用户更新", "code": "user:update", "module": "用户管理", "resource": "user", "action": "update", "parent_code": "user:manage"},
        {"name": "用户删除", "code": "user:delete", "module": "用户管理", "resource": "user", "action": "delete", "parent_code": "user:manage"},

        # 角色管理子权限
        {"name": "角色查看", "code": "role:read", "module": "角色管理", "resource": "role", "action": "read", "parent_code": "role:manage"},
        {"name": "角色创建", "code": "role:create", "module": "角色管理", "resource": "role", "action": "create", "parent_code": "role:manage"},
        {"name": "角色更新", "code": "role:update", "module": "角色管理", "resource": "role", "action": "update", "parent_code": "role:manage"},
        {"name": "角色删除", "code": "role:delete", "module": "角色管理", "resource": "role", "action": "delete", "parent_code": "role:manage"},

        # 权限管理子权限
        {"name": "权限查看", "code": "permission:read", "module": "权限管理", "resource": "permission", "action": "read", "parent_code": "permission:manage"},
        {"name": "权限创建", "code": "permission:create", "module": "权限管理", "resource": "permission", "action": "create", "parent_code": "permission:manage"},
        {"name": "权限更新", "code": "permission:update", "module": "权限管理", "resource": "permission", "action": "update", "parent_code": "permission:manage"},
        {"name": "权限删除", "code": "permission:delete", "module": "权限管理", "resource": "permission", "action": "delete", "parent_code": "permission:manage"},

        # 菜单管理子权限
        {"name": "菜单查看", "code": "menu:read", "module": "菜单管理", "resource": "menu", "action": "read", "parent_code": "menu:manage"},
        {"name": "菜单创建", "code": "menu:create", "module": "菜单管理", "resource": "menu", "action": "create", "parent_code": "menu:manage"},
        {"name": "菜单更新", "code": "menu:update", "module": "菜单管理", "resource": "menu", "action": "update", "parent_code": "menu:manage"},
        {"name": "菜单删除", "code": "menu:delete", "module": "菜单管理", "resource": "menu", "action": "delete", "parent_code": "menu:manage"},

        # 部门管理子权限
        {"name": "部门查看", "code": "department:read", "module": "部门管理", "resource": "department", "action": "read", "parent_code": "department:manage"},
        {"name": "部门创建", "code": "department:create", "module": "部门管理", "resource": "department", "action": "create", "parent_code": "department:manage"},
        {"name": "部门更新", "code": "department:update", "module": "部门管理", "resource": "department", "action": "update", "parent_code": "department:manage"},
        {"name": "部门删除", "code": "department:delete", "module": "部门管理", "resource": "department", "action": "delete", "parent_code": "department:manage"},

        # 系统管理子权限
        {"name": "系统查看", "code": "system:read", "module": "系统管理", "resource": "system", "action": "read", "parent_code": "system:manage"},
        {"name": "系统更新", "code": "system:update", "module": "系统管理", "resource": "system", "action": "update", "parent_code": "system:manage"},
    ]

    # 创建子权限
    created_permissions = list(created_top_permissions.values())
    for perm_data in child_permissions_data:
        parent_code = perm_data.pop("parent_code")
        parent_perm = created_top_permissions.get(parent_code)
        if parent_perm:
            perm_data["parent_id"] = parent_perm.id
        permission = await Permission.get_or_none(code=perm_data["code"])
        if not permission:
            permission = await Permission.create(**perm_data)
        created_permissions.append(permission)
    
    # 为超级管理员分配所有权限
    await super_admin_role.permissions.add(*created_permissions)
    
    # 为系统管理员分配部分权限
    system_admin_permissions = [p for p in created_permissions if p.resource in ["user", "role"]]
    await system_admin_role.permissions.add(*system_admin_permissions)
    
    # 为普通用户分配查看权限
    normal_user_permissions = [p for p in created_permissions if p.action == "read"]
    await normal_user_role.permissions.add(*normal_user_permissions)

    # 创建部门
    root_dept = await Department.create(
        name="总公司",
        code="ROOT",
        description="公司总部",
        parent_id=None,
        level=0,
        sort_order=1,
        is_active=True
    )

    tech_dept = await Department.create(
        name="技术部",
        code="TECH",
        description="技术研发部门",
        parent_id=root_dept.id,
        level=1,
        sort_order=1,
        is_active=True
    )

    hr_dept = await Department.create(
        name="人事部",
        code="HR",
        description="人力资源部门",
        parent_id=root_dept.id,
        level=1,
        sort_order=2,
        is_active=True
    )

    finance_dept = await Department.create(
        name="财务部",
        code="FINANCE",
        description="财务管理部门",
        parent_id=root_dept.id,
        level=1,
        sort_order=3,
        is_active=True
    )

    # 创建用户并分配部门
    admin_user = await User.create(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="系统管理员",
        is_active=True,
        is_superuser=True,
        department_id=root_dept.id
    )

    manager_user = await User.create(
        username="manager",
        email="manager@example.com",
        hashed_password=get_password_hash("manager123"),
        full_name="技术部经理",
        is_active=True,
        is_superuser=False,
        department_id=tech_dept.id
    )

    normal_user = await User.create(
        username="user",
        email="user@example.com",
        hashed_password=get_password_hash("user123"),
        full_name="普通用户",
        is_active=True,
        is_superuser=False,
        department_id=tech_dept.id
    )

    # 设置部门负责人
    tech_dept.manager_id = manager_user.id
    await tech_dept.save()
    
    # 分配角色
    await admin_user.roles.add(super_admin_role)
    await manager_user.roles.add(system_admin_role)
    await normal_user.roles.add(normal_user_role)
    
    print("初始数据创建完成")
    print("超级管理员: admin/admin123")
    print("系统管理员: manager/manager123") 
    print("普通用户: user/user123")
