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
    super_admin_role = await Role.create(
        name="超级管理员",
        code="super_admin",
        description="系统超级管理员，拥有所有权限",
        is_active=True,
        sort_order=1
    )
    
    # 创建系统管理员角色
    system_admin_role = await Role.create(
        name="系统管理员", 
        code="system_admin",
        description="系统管理员，拥有用户和角色管理权限",
        is_active=True,
        sort_order=2
    )
    
    # 创建普通用户角色
    normal_user_role = await Role.create(
        name="普通用户",
        code="normal_user", 
        description="普通用户，只有基础查看权限",
        is_active=True,
        sort_order=3
    )
    
    # 创建权限
    permissions_data = [
        # 用户管理权限
        {"name": "用户查看", "code": "user:read", "resource": "user", "action": "read"},
        {"name": "用户创建", "code": "user:create", "resource": "user", "action": "create"},
        {"name": "用户更新", "code": "user:update", "resource": "user", "action": "update"},
        {"name": "用户删除", "code": "user:delete", "resource": "user", "action": "delete"},
        
        # 角色管理权限
        {"name": "角色查看", "code": "role:read", "resource": "role", "action": "read"},
        {"name": "角色创建", "code": "role:create", "resource": "role", "action": "create"},
        {"name": "角色更新", "code": "role:update", "resource": "role", "action": "update"},
        {"name": "角色删除", "code": "role:delete", "resource": "role", "action": "delete"},
        
        # 权限管理权限
        {"name": "权限查看", "code": "permission:read", "resource": "permission", "action": "read"},
        {"name": "权限创建", "code": "permission:create", "resource": "permission", "action": "create"},
        {"name": "权限更新", "code": "permission:update", "resource": "permission", "action": "update"},
        {"name": "权限删除", "code": "permission:delete", "resource": "permission", "action": "delete"},
        
        # 菜单管理权限
        {"name": "菜单查看", "code": "menu:read", "resource": "menu", "action": "read"},
        {"name": "菜单创建", "code": "menu:create", "resource": "menu", "action": "create"},
        {"name": "菜单更新", "code": "menu:update", "resource": "menu", "action": "update"},
        {"name": "菜单删除", "code": "menu:delete", "resource": "menu", "action": "delete"},

        # 部门管理权限
        {"name": "部门查看", "code": "department:read", "resource": "department", "action": "read"},
        {"name": "部门创建", "code": "department:create", "resource": "department", "action": "create"},
        {"name": "部门更新", "code": "department:update", "resource": "department", "action": "update"},
        {"name": "部门删除", "code": "department:delete", "resource": "department", "action": "delete"},

        # 系统管理权限
        {"name": "系统查看", "code": "system:read", "resource": "system", "action": "read"},
        {"name": "系统更新", "code": "system:update", "resource": "system", "action": "update"},
    ]
    
    created_permissions = []
    for perm_data in permissions_data:
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
