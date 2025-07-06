"""
数据库初始化脚本
创建初始数据和演示数据
包含：用户、角色、权限、菜单、部门、数据权限等完整初始化
"""

import asyncio
from app.core.database import init_db, create_superuser
from app.models.menu import Menu
from app.models.data_permission import DataPermission
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.models.department import Department
from app.core.security import get_password_hash


async def create_permissions():
    """创建权限数据"""
    print("开始创建权限数据...")

    # 检查是否已存在权限
    existing_permission = await Permission.filter(code="system:manage").first()
    if existing_permission:
        print("权限数据已存在")
        return

    # 第一步：创建顶级模块权限
    top_level_permissions = [
        {"name": "系统管理", "code": "system:manage", "module": "系统管理", "resource": "system", "action": "manage", "type": "模块", "sort_order": 1},
        {"name": "用户管理", "code": "user:manage", "module": "用户管理", "resource": "user", "action": "manage", "type": "模块", "sort_order": 2},
        {"name": "角色管理", "code": "role:manage", "module": "角色管理", "resource": "role", "action": "manage", "type": "模块", "sort_order": 3},
        {"name": "权限管理", "code": "permission:manage", "module": "权限管理", "resource": "permission", "action": "manage", "type": "模块", "sort_order": 4},
        {"name": "菜单管理", "code": "menu:manage", "module": "菜单管理", "resource": "menu", "action": "manage", "type": "模块", "sort_order": 5},
        {"name": "部门管理", "code": "department:manage", "module": "部门管理", "resource": "department", "action": "manage", "type": "模块", "sort_order": 6},
        {"name": "数据权限管理", "code": "data_permission:manage", "module": "数据权限管理", "resource": "data_permission", "action": "manage", "type": "模块", "sort_order": 7},
        {"name": "审计日志管理", "code": "audit_log:manage", "module": "审计日志管理", "resource": "audit_log", "action": "manage", "type": "模块", "sort_order": 8},
    ]

    # 创建顶级权限
    created_top_permissions = {}
    for perm_data in top_level_permissions:
        perm = await Permission.create(**perm_data)
        created_top_permissions[perm_data["code"]] = perm
        print(f"创建顶级权限: {perm.name}")

    # 第二步：创建子权限
    child_permissions_data = [
        # 用户管理子权限
        {"name": "用户查看", "code": "user:read", "module": "用户管理", "resource": "user", "action": "read", "type": "功能", "parent_code": "user:manage", "sort_order": 1},
        {"name": "用户创建", "code": "user:create", "module": "用户管理", "resource": "user", "action": "create", "type": "操作", "parent_code": "user:manage", "sort_order": 2},
        {"name": "用户更新", "code": "user:update", "module": "用户管理", "resource": "user", "action": "update", "type": "操作", "parent_code": "user:manage", "sort_order": 3},
        {"name": "用户删除", "code": "user:delete", "module": "用户管理", "resource": "user", "action": "delete", "type": "操作", "parent_code": "user:manage", "sort_order": 4},
        {"name": "用户导入", "code": "user:import", "module": "用户管理", "resource": "user", "action": "import", "type": "操作", "parent_code": "user:manage", "sort_order": 5},
        {"name": "用户导出", "code": "user:export", "module": "用户管理", "resource": "user", "action": "export", "type": "操作", "parent_code": "user:manage", "sort_order": 6},
        {"name": "用户重置密码", "code": "user:reset_password", "module": "用户管理", "resource": "user", "action": "reset_password", "type": "操作", "parent_code": "user:manage", "sort_order": 7},
        {"name": "用户启用禁用", "code": "user:toggle_status", "module": "用户管理", "resource": "user", "action": "toggle_status", "type": "操作", "parent_code": "user:manage", "sort_order": 8},

        # 角色管理子权限
        {"name": "角色查看", "code": "role:read", "module": "角色管理", "resource": "role", "action": "read", "type": "功能", "parent_code": "role:manage", "sort_order": 1},
        {"name": "角色创建", "code": "role:create", "module": "角色管理", "resource": "role", "action": "create", "type": "操作", "parent_code": "role:manage", "sort_order": 2},
        {"name": "角色更新", "code": "role:update", "module": "角色管理", "resource": "role", "action": "update", "type": "操作", "parent_code": "role:manage", "sort_order": 3},
        {"name": "角色删除", "code": "role:delete", "module": "角色管理", "resource": "role", "action": "delete", "type": "操作", "parent_code": "role:manage", "sort_order": 4},
        {"name": "角色权限分配", "code": "role:assign_permissions", "module": "角色管理", "resource": "role", "action": "assign_permissions", "type": "操作", "parent_code": "role:manage", "sort_order": 5},
        {"name": "角色菜单分配", "code": "role:assign_menus", "module": "角色管理", "resource": "role", "action": "assign_menus", "type": "操作", "parent_code": "role:manage", "sort_order": 6},
        {"name": "角色数据权限分配", "code": "role:assign_data_permissions", "module": "角色管理", "resource": "role", "action": "assign_data_permissions", "type": "操作", "parent_code": "role:manage", "sort_order": 7},

        # 权限管理子权限
        {"name": "权限查看", "code": "permission:read", "module": "权限管理", "resource": "permission", "action": "read", "type": "功能", "parent_code": "permission:manage", "sort_order": 1},
        {"name": "权限创建", "code": "permission:create", "module": "权限管理", "resource": "permission", "action": "create", "type": "操作", "parent_code": "permission:manage", "sort_order": 2},
        {"name": "权限更新", "code": "permission:update", "module": "权限管理", "resource": "permission", "action": "update", "type": "操作", "parent_code": "permission:manage", "sort_order": 3},
        {"name": "权限删除", "code": "permission:delete", "module": "权限管理", "resource": "permission", "action": "delete", "type": "操作", "parent_code": "permission:manage", "sort_order": 4},
        {"name": "权限导出", "code": "permission:export", "module": "权限管理", "resource": "permission", "action": "export", "type": "操作", "parent_code": "permission:manage", "sort_order": 5},
        {"name": "权限批量操作", "code": "permission:batch", "module": "权限管理", "resource": "permission", "action": "batch", "type": "操作", "parent_code": "permission:manage", "sort_order": 6},

        # 菜单管理子权限
        {"name": "菜单查看", "code": "menu:read", "module": "菜单管理", "resource": "menu", "action": "read", "type": "功能", "parent_code": "menu:manage", "sort_order": 1},
        {"name": "菜单创建", "code": "menu:create", "module": "菜单管理", "resource": "menu", "action": "create", "type": "操作", "parent_code": "menu:manage", "sort_order": 2},
        {"name": "菜单更新", "code": "menu:update", "module": "菜单管理", "resource": "menu", "action": "update", "type": "操作", "parent_code": "menu:manage", "sort_order": 3},
        {"name": "菜单删除", "code": "menu:delete", "module": "菜单管理", "resource": "menu", "action": "delete", "type": "操作", "parent_code": "menu:manage", "sort_order": 4},

        # 部门管理子权限
        {"name": "部门查看", "code": "department:read", "module": "部门管理", "resource": "department", "action": "read", "type": "功能", "parent_code": "department:manage", "sort_order": 1},
        {"name": "部门创建", "code": "department:create", "module": "部门管理", "resource": "department", "action": "create", "type": "操作", "parent_code": "department:manage", "sort_order": 2},
        {"name": "部门更新", "code": "department:update", "module": "部门管理", "resource": "department", "action": "update", "type": "操作", "parent_code": "department:manage", "sort_order": 3},
        {"name": "部门删除", "code": "department:delete", "module": "部门管理", "resource": "department", "action": "delete", "type": "操作", "parent_code": "department:manage", "sort_order": 4},

        # 系统管理子权限
        {"name": "系统查看", "code": "system:read", "module": "系统管理", "resource": "system", "action": "read", "type": "功能", "parent_code": "system:manage", "sort_order": 1},
        {"name": "系统更新", "code": "system:update", "module": "系统管理", "resource": "system", "action": "update", "type": "操作", "parent_code": "system:manage", "sort_order": 2},
        {"name": "系统配置", "code": "system:config", "module": "系统管理", "resource": "system", "action": "config", "type": "操作", "parent_code": "system:manage", "sort_order": 3},
        {"name": "系统监控", "code": "system:monitor", "module": "系统管理", "resource": "system", "action": "monitor", "type": "功能", "parent_code": "system:manage", "sort_order": 4},

        # 数据权限管理子权限
        {"name": "数据权限查看", "code": "data_permission:read", "module": "数据权限管理", "resource": "data_permission", "action": "read", "type": "功能", "parent_code": "data_permission:manage", "sort_order": 1},
        {"name": "数据权限创建", "code": "data_permission:create", "module": "数据权限管理", "resource": "data_permission", "action": "create", "type": "操作", "parent_code": "data_permission:manage", "sort_order": 2},
        {"name": "数据权限更新", "code": "data_permission:update", "module": "数据权限管理", "resource": "data_permission", "action": "update", "type": "操作", "parent_code": "data_permission:manage", "sort_order": 3},
        {"name": "数据权限删除", "code": "data_permission:delete", "module": "数据权限管理", "resource": "data_permission", "action": "delete", "type": "操作", "parent_code": "data_permission:manage", "sort_order": 4},
        {"name": "数据权限分配", "code": "data_permission:assign", "module": "数据权限管理", "resource": "data_permission", "action": "assign", "type": "操作", "parent_code": "data_permission:manage", "sort_order": 5},

        # 审计日志管理子权限
        {"name": "审计日志查看", "code": "audit_log:read", "module": "审计日志管理", "resource": "audit_log", "action": "read", "type": "功能", "parent_code": "audit_log:manage", "sort_order": 1},
        {"name": "审计日志导出", "code": "audit_log:export", "module": "审计日志管理", "resource": "audit_log", "action": "export", "type": "操作", "parent_code": "audit_log:manage", "sort_order": 2},
        {"name": "审计日志删除", "code": "audit_log:delete", "module": "审计日志管理", "resource": "audit_log", "action": "delete", "type": "操作", "parent_code": "audit_log:manage", "sort_order": 3},
        {"name": "审计日志统计", "code": "audit_log:stats", "module": "审计日志管理", "resource": "audit_log", "action": "stats", "type": "功能", "parent_code": "audit_log:manage", "sort_order": 4},
    ]

    # 创建子权限
    for perm_data in child_permissions_data:
        parent_code = perm_data.pop("parent_code")
        parent_perm = created_top_permissions.get(parent_code)
        if parent_perm:
            perm_data["parent_id"] = parent_perm.id

        perm = await Permission.create(**perm_data)
        print(f"创建子权限: {perm.name} (父权限: {parent_perm.name if parent_perm else '无'})")

    print("权限数据创建完成")


async def assign_role_permissions():
    """为角色分配权限"""
    print("开始为角色分配权限...")

    # 超级管理员拥有所有权限
    super_admin_role = await Role.get(code="super_admin")
    all_permissions = await Permission.all()
    await super_admin_role.permissions.add(*all_permissions)
    print(f"为超级管理员分配了 {len(all_permissions)} 个权限")

    # 系统管理员拥有部分权限
    system_admin_role = await Role.get(code="system_admin")
    system_admin_permission_codes = [
        # 用户管理权限
        "user:manage", "user:read", "user:create", "user:update", "user:delete",
        "user:import", "user:export", "user:reset_password", "user:toggle_status",

        # 角色管理权限
        "role:manage", "role:read", "role:create", "role:update", "role:delete",
        "role:assign_permissions", "role:assign_menus",

        # 部门管理权限
        "department:manage", "department:read", "department:create", "department:update", "department:delete",

        # 系统管理权限
        "system:read", "system:monitor",

        # 审计日志权限
        "audit_log:manage", "audit_log:read", "audit_log:export", "audit_log:stats"
    ]
    system_admin_permissions = await Permission.filter(code__in=system_admin_permission_codes)
    await system_admin_role.permissions.add(*system_admin_permissions)
    print(f"为系统管理员分配了 {len(system_admin_permissions)} 个权限")

    # 普通用户只有基本查看权限
    normal_user_role = await Role.get(code="normal_user")
    normal_user_permission_codes = [
        "user:read", "role:read", "department:read"
    ]
    normal_user_permissions = await Permission.filter(code__in=normal_user_permission_codes)
    await normal_user_role.permissions.add(*normal_user_permissions)
    print(f"为普通用户分配了 {len(normal_user_permissions)} 个权限")

    # 创建部门经理角色并分配权限
    dept_manager_role = await Role.filter(code="dept_manager").first()
    if not dept_manager_role:
        dept_manager_role = await Role.create(
            name="部门经理",
            code="dept_manager",
            description="部门经理角色，可以管理本部门用户",
            is_active=True,
            sort_order=4
        )

    dept_manager_permission_codes = [
        "user:read", "user:create", "user:update", "user:export",
        "role:read", "department:read",
        "audit_log:read"
    ]
    dept_manager_permissions = await Permission.filter(code__in=dept_manager_permission_codes)
    await dept_manager_role.permissions.add(*dept_manager_permissions)
    print(f"为部门经理分配了 {len(dept_manager_permissions)} 个权限")

    print("角色权限分配完成")


async def create_demo_menus():
    """创建演示菜单数据"""
    # 检查是否已存在菜单
    existing_menu = await Menu.filter(name="dashboard").first()
    if existing_menu:
        print("演示菜单已存在")
        return

    # 创建主菜单
    dashboard_menu = await Menu.create(
        name="dashboard",
        title="仪表板",
        path="/dashboard",
        component="Dashboard",
        icon="el-icon-odometer",
        sort_order=1,
        is_visible=True
    )

    system_menu = await Menu.create(
        name="system",
        title="系统管理",
        path="/system",
        component="Layout",
        icon="el-icon-setting",
        sort_order=2,
        is_visible=True
    )

    # 创建系统管理子菜单
    user_menu = await Menu.create(
        name="system-user",
        title="用户管理",
        path="/system/users",
        component="system/user/Index",
        icon="el-icon-user",
        parent_id=system_menu.id,
        sort_order=1,
        is_visible=True
    )

    role_menu = await Menu.create(
        name="system-role",
        title="角色管理",
        path="/system/roles",
        component="system/role/Index",
        icon="el-icon-s-custom",
        parent_id=system_menu.id,
        sort_order=2,
        is_visible=True
    )

    permission_menu = await Menu.create(
        name="system-permission",
        title="权限管理",
        path="/system/permissions",
        component="system/permission/Index",
        icon="el-icon-key",
        parent_id=system_menu.id,
        sort_order=3,
        is_visible=True
    )

    department_menu = await Menu.create(
        name="system-department",
        title="部门管理",
        path="/system/departments",
        component="system/department/Index",
        icon="el-icon-office-building",
        parent_id=system_menu.id,
        sort_order=4,
        is_visible=True
    )

    menu_menu = await Menu.create(
        name="system-menu",
        title="菜单管理",
        path="/system/menus",
        component="system/menu/Index",
        icon="el-icon-menu",
        parent_id=system_menu.id,
        sort_order=5,
        is_visible=True
    )

    # 添加数据权限管理菜单
    data_permission_menu = await Menu.create(
        name="system-data-permission",
        title="数据权限管理",
        path="/system/data-permissions",
        component="system/data-permission/Index",
        icon="el-icon-key",
        parent_id=system_menu.id,
        sort_order=6,
        is_visible=True
    )

    # 添加审计日志菜单
    audit_log_menu = await Menu.create(
        name="system-audit-log",
        title="审计日志",
        path="/system/audit-logs",
        component="system/audit-log/Index",
        icon="el-icon-document",
        parent_id=system_menu.id,
        sort_order=7,
        is_visible=True
    )

    print("演示菜单创建完成")

    # 为角色分配菜单
    from app.models.role import Role

    # 超级管理员拥有所有菜单
    super_admin_role = await Role.get(code="super_admin")
    all_menus = [dashboard_menu, system_menu, user_menu, role_menu, permission_menu,
                 department_menu, menu_menu, data_permission_menu, audit_log_menu]
    await super_admin_role.menus.add(*all_menus)

    # 系统管理员拥有部分菜单
    system_admin_role = await Role.get(code="system_admin")
    system_admin_menus = [dashboard_menu, system_menu, user_menu, role_menu,
                         department_menu, audit_log_menu]
    await system_admin_role.menus.add(*system_admin_menus)

    # 普通用户只有仪表板
    normal_user_role = await Role.get(code="normal_user")
    await normal_user_role.menus.add(dashboard_menu)

    print("菜单权限分配完成")


async def create_data_permissions():
    """创建数据权限演示数据"""
    # 检查是否已存在数据权限
    existing_data_perm = await DataPermission.filter(code="user_dept_data").first()
    if existing_data_perm:
        print("数据权限已存在")
        return

    # 创建部门数据权限
    dept_data_perm = await DataPermission.create(
        name="部门数据权限",
        code="user_dept_data",
        description="用户只能查看本部门的数据",
        permission_type="department",
        scope="user",
        resource_type="user",
        is_active=True,
        sort_order=1
    )

    # 创建个人数据权限
    personal_data_perm = await DataPermission.create(
        name="个人数据权限",
        code="user_personal_data",
        description="用户只能查看自己的数据",
        permission_type="self",
        scope="user",
        resource_type="user",
        custom_conditions={"user_id": "current_user_id"},
        is_active=True,
        sort_order=2
    )

    # 创建全部数据权限
    all_data_perm = await DataPermission.create(
        name="全部数据权限",
        code="user_all_data",
        description="用户可以查看所有数据",
        permission_type="all",
        scope="user",
        resource_type="user",
        is_active=True,
        sort_order=3
    )

    print("数据权限创建完成")

    # 为角色分配数据权限
    from app.models.role import Role

    # 超级管理员拥有全部数据权限
    super_admin_role = await Role.get(code="super_admin")
    await super_admin_role.data_permissions.add(all_data_perm)

    # 系统管理员拥有部门数据权限
    system_admin_role = await Role.get(code="system_admin")
    await system_admin_role.data_permissions.add(dept_data_perm)

    # 普通用户只有个人数据权限
    normal_user_role = await Role.get(code="normal_user")
    await normal_user_role.data_permissions.add(personal_data_perm)

    print("数据权限分配完成")


async def create_additional_users():
    """创建额外的演示用户"""
    from app.models.user import User
    from app.models.role import Role
    from app.models.department import Department
    from app.core.security import get_password_hash

    # 检查是否已存在额外用户
    existing_user = await User.filter(username="hr_manager").first()
    if existing_user:
        print("额外演示用户已存在")
        return

    # 获取部门
    hr_dept = await Department.get(code="HR")
    finance_dept = await Department.get(code="FINANCE")
    tech_dept = await Department.get(code="TECH")

    # 获取角色
    system_admin_role = await Role.get(code="system_admin")
    normal_user_role = await Role.get(code="normal_user")

    # 创建人事部经理
    hr_manager = await User.create(
        username="hr_manager",
        email="hr_manager@example.com",
        hashed_password=get_password_hash("hr123"),
        full_name="人事部经理",
        is_active=True,
        is_superuser=False,
        department_id=hr_dept.id
    )
    await hr_manager.roles.add(system_admin_role)

    # 创建财务部经理
    finance_manager = await User.create(
        username="finance_manager",
        email="finance_manager@example.com",
        hashed_password=get_password_hash("finance123"),
        full_name="财务部经理",
        is_active=True,
        is_superuser=False,
        department_id=finance_dept.id
    )
    await finance_manager.roles.add(system_admin_role)

    # 创建技术部员工
    tech_user1 = await User.create(
        username="tech_user1",
        email="tech_user1@example.com",
        hashed_password=get_password_hash("tech123"),
        full_name="技术部员工1",
        is_active=True,
        is_superuser=False,
        department_id=tech_dept.id
    )
    await tech_user1.roles.add(normal_user_role)

    tech_user2 = await User.create(
        username="tech_user2",
        email="tech_user2@example.com",
        hashed_password=get_password_hash("tech123"),
        full_name="技术部员工2",
        is_active=True,
        is_superuser=False,
        department_id=tech_dept.id
    )
    await tech_user2.roles.add(normal_user_role)

    # 设置部门负责人
    hr_dept.manager_id = hr_manager.id
    await hr_dept.save()

    finance_dept.manager_id = finance_manager.id
    await finance_dept.save()

    print("额外演示用户创建完成")


async def main():
    """主函数"""
    print("开始初始化数据库...")

    # 初始化数据库
    await init_db()
    print("数据库连接初始化完成")

    # 创建超级用户和基础数据（包含角色和部门）
    await create_superuser()

    # 创建权限数据
    await create_permissions()

    # 为角色分配权限
    await assign_role_permissions()

    # 创建演示菜单
    await create_demo_menus()

    # 创建数据权限
    await create_data_permissions()

    # 创建额外用户
    await create_additional_users()

    print("数据库初始化完成！")
    print("\n=== 演示账户信息 ===")
    print("超级管理员: admin/admin123")
    print("系统管理员: manager/manager123")
    print("人事部经理: hr_manager/hr123")
    print("财务部经理: finance_manager/finance123")
    print("普通用户: user/user123")
    print("技术部员工1: tech_user1/tech123")
    print("技术部员工2: tech_user2/tech123")
    print("==================")
    print("\n=== 权限统计 ===")

    # 统计权限数据
    total_permissions = await Permission.all().count()
    top_level_permissions = await Permission.filter(parent_id__isnull=True).count()
    child_permissions = await Permission.filter(parent_id__isnull=False).count()

    print(f"总权限数: {total_permissions}")
    print(f"顶级权限: {top_level_permissions}")
    print(f"子权限: {child_permissions}")

    # 统计角色数据
    total_roles = await Role.all().count()
    print(f"总角色数: {total_roles}")

    # 统计用户数据
    total_users = await User.all().count()
    print(f"总用户数: {total_users}")

    # 统计部门数据
    total_departments = await Department.all().count()
    print(f"总部门数: {total_departments}")

    print("==================")


if __name__ == "__main__":
    asyncio.run(main())
