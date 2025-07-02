"""
数据库初始化脚本
创建初始数据和演示数据
"""

import asyncio
from app.core.database import init_db, create_superuser
from app.models.menu import Menu


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

    log_menu = await Menu.create(
        name="system-log",
        title="操作日志",
        path="/system/logs",
        component="system/log/Index",
        icon="el-icon-document",
        parent_id=system_menu.id,
        sort_order=6,
        is_visible=True
    )
    
    print("演示菜单创建完成")
    
    # 为角色分配菜单
    from app.models.role import Role
    
    # 超级管理员拥有所有菜单
    super_admin_role = await Role.get(code="super_admin")
    all_menus = [dashboard_menu, system_menu, user_menu, role_menu, permission_menu, department_menu, menu_menu, log_menu]
    await super_admin_role.menus.add(*all_menus)

    # 系统管理员拥有部分菜单
    system_admin_role = await Role.get(code="system_admin")
    system_admin_menus = [dashboard_menu, system_menu, user_menu, role_menu, department_menu]
    await system_admin_role.menus.add(*system_admin_menus)
    
    # 普通用户只有仪表板
    normal_user_role = await Role.get(code="normal_user")
    await normal_user_role.menus.add(dashboard_menu)
    
    print("菜单权限分配完成")


async def main():
    """主函数"""
    print("开始初始化数据库...")
    
    # 初始化数据库
    await init_db()
    print("数据库连接初始化完成")
    
    # 创建超级用户和基础数据
    await create_superuser()
    
    # 创建演示菜单
    await create_demo_menus()
    
    print("数据库初始化完成！")
    print("\n=== 演示账户信息 ===")
    print("超级管理员: admin/admin123")
    print("系统管理员: manager/manager123")
    print("普通用户: user/user123")
    print("==================")


if __name__ == "__main__":
    asyncio.run(main())
