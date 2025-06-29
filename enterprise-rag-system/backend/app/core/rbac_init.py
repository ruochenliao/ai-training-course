"""
RBAC权限系统初始化数据
"""

from loguru import logger

from app.models import Department, Role, Permission, RolePermission, PermissionGroup


async def init_rbac_data():
    """初始化RBAC基础数据"""
    try:
        logger.info("开始初始化RBAC基础数据...")

        # 检查RBAC表是否存在，如果不存在则跳过初始化
        try:
            from app.models import PermissionGroup
            await PermissionGroup.all().limit(1)
        except Exception as e:
            logger.warning(f"RBAC表不存在或结构不匹配，跳过初始化: {e}")
            return

        # 1. 创建权限分组
        await create_permission_groups()

        # 2. 创建基础权限
        await create_basic_permissions()

        # 3. 创建基础角色
        await create_basic_roles()

        # 4. 创建基础部门
        await create_basic_departments()

        # 5. 分配角色权限
        await assign_role_permissions()

        logger.info("RBAC基础数据初始化完成")

    except Exception as e:
        logger.error(f"RBAC基础数据初始化失败: {e}")
        # 不抛出异常，允许系统继续启动
        logger.warning("RBAC初始化失败，系统将以基础模式启动")


async def create_permission_groups():
    """创建权限分组"""
    groups = [
        {"name": "系统管理", "code": "system", "description": "系统管理相关权限"},
        {"name": "用户管理", "code": "user", "description": "用户管理相关权限"},
        {"name": "角色管理", "code": "role", "description": "角色管理相关权限"},
        {"name": "权限管理", "code": "permission", "description": "权限管理相关权限"},
        {"name": "部门管理", "code": "department", "description": "部门管理相关权限"},
        {"name": "知识库管理", "code": "knowledge", "description": "知识库管理相关权限"},
        {"name": "文档管理", "code": "document", "description": "文档管理相关权限"},
        {"name": "聊天功能", "code": "chat", "description": "聊天功能相关权限"},
        {"name": "搜索功能", "code": "search", "description": "搜索功能相关权限"},
        {"name": "监控管理", "code": "monitor", "description": "监控管理相关权限"},
    ]
    
    for group_data in groups:
        group = await PermissionGroup.get_or_none(code=group_data["code"])
        if not group:
            await PermissionGroup.create(**group_data)
            logger.info(f"创建权限分组: {group_data['name']}")


async def create_basic_permissions():
    """创建基础权限"""
    permissions = [
        # 系统管理权限
        {"name": "系统管理", "code": "system:manage", "group": "system", "resource": "system", "action": "manage", "permission_type": "menu", "menu_path": "/system", "menu_icon": "SettingOutlined", "description": "系统管理菜单"},
        {"name": "系统配置", "code": "system:config", "group": "system", "resource": "system", "action": "config", "permission_type": "api", "description": "系统配置管理"},
        {"name": "系统监控", "code": "system:monitor", "group": "system", "resource": "system", "action": "monitor", "permission_type": "api", "description": "系统监控"},
        
        # 用户管理权限
        {"name": "用户管理", "code": "user:manage", "group": "user", "resource": "user", "action": "manage", "permission_type": "menu", "menu_path": "/system/users", "menu_icon": "UserOutlined", "description": "用户管理菜单"},
        {"name": "查看用户", "code": "user:view", "group": "user", "resource": "user", "action": "view", "permission_type": "api", "description": "查看用户信息"},
        {"name": "创建用户", "code": "user:create", "group": "user", "resource": "user", "action": "create", "permission_type": "api", "description": "创建用户"},
        {"name": "编辑用户", "code": "user:update", "group": "user", "resource": "user", "action": "update", "permission_type": "api", "description": "编辑用户信息"},
        {"name": "删除用户", "code": "user:delete", "group": "user", "resource": "user", "action": "delete", "permission_type": "api", "description": "删除用户"},
        {"name": "重置密码", "code": "user:reset_password", "group": "user", "resource": "user", "action": "reset_password", "permission_type": "api", "description": "重置用户密码"},
        
        # 角色管理权限
        {"name": "角色管理", "code": "role:manage", "group": "role", "resource": "role", "action": "manage", "permission_type": "menu", "menu_path": "/system/roles", "menu_icon": "TeamOutlined", "description": "角色管理菜单"},
        {"name": "查看角色", "code": "role:view", "group": "role", "resource": "role", "action": "view", "permission_type": "api", "description": "查看角色信息"},
        {"name": "创建角色", "code": "role:create", "group": "role", "resource": "role", "action": "create", "permission_type": "api", "description": "创建角色"},
        {"name": "编辑角色", "code": "role:update", "group": "role", "resource": "role", "action": "update", "permission_type": "api", "description": "编辑角色信息"},
        {"name": "删除角色", "code": "role:delete", "group": "role", "resource": "role", "action": "delete", "permission_type": "api", "description": "删除角色"},
        {"name": "分配权限", "code": "role:assign_permission", "group": "role", "resource": "role", "action": "assign_permission", "permission_type": "api", "description": "为角色分配权限"},
        
        # 权限管理权限
        {"name": "权限管理", "code": "permission:manage", "group": "permission", "resource": "permission", "action": "manage", "permission_type": "menu", "menu_path": "/system/permissions", "menu_icon": "SafetyOutlined", "description": "权限管理菜单"},
        {"name": "查看权限", "code": "permission:view", "group": "permission", "resource": "permission", "action": "view", "permission_type": "api", "description": "查看权限信息"},
        {"name": "创建权限", "code": "permission:create", "group": "permission", "resource": "permission", "action": "create", "permission_type": "api", "description": "创建权限"},
        {"name": "编辑权限", "code": "permission:update", "group": "permission", "resource": "permission", "action": "update", "permission_type": "api", "description": "编辑权限信息"},
        {"name": "删除权限", "code": "permission:delete", "group": "permission", "resource": "permission", "action": "delete", "permission_type": "api", "description": "删除权限"},
        
        # 部门管理权限
        {"name": "部门管理", "code": "dept:manage", "group": "department", "resource": "department", "action": "manage", "permission_type": "menu", "menu_path": "/system/departments", "menu_icon": "ApartmentOutlined", "description": "部门管理菜单"},
        {"name": "查看部门", "code": "dept:view", "group": "department", "resource": "department", "action": "view", "permission_type": "api", "description": "查看部门信息"},
        {"name": "创建部门", "code": "dept:create", "group": "department", "resource": "department", "action": "create", "permission_type": "api", "description": "创建部门"},
        {"name": "编辑部门", "code": "dept:update", "group": "department", "resource": "department", "action": "update", "permission_type": "api", "description": "编辑部门信息"},
        {"name": "删除部门", "code": "dept:delete", "group": "department", "resource": "department", "action": "delete", "permission_type": "api", "description": "删除部门"},
        
        # 用户角色分配权限
        {"name": "用户角色管理", "code": "user_role:manage", "group": "user", "resource": "user_role", "action": "manage", "permission_type": "api", "description": "用户角色分配管理"},
        
        # 知识库管理权限
        {"name": "知识库管理", "code": "knowledge:manage", "group": "knowledge", "resource": "knowledge", "action": "manage", "permission_type": "menu", "menu_path": "/knowledge", "menu_icon": "BookOutlined", "description": "知识库管理菜单"},
        {"name": "查看知识库", "code": "knowledge:view", "group": "knowledge", "resource": "knowledge", "action": "view", "permission_type": "api", "description": "查看知识库"},
        {"name": "创建知识库", "code": "knowledge:create", "group": "knowledge", "resource": "knowledge", "action": "create", "permission_type": "api", "description": "创建知识库"},
        {"name": "编辑知识库", "code": "knowledge:update", "group": "knowledge", "resource": "knowledge", "action": "update", "permission_type": "api", "description": "编辑知识库"},
        {"name": "删除知识库", "code": "knowledge:delete", "group": "knowledge", "resource": "knowledge", "action": "delete", "permission_type": "api", "description": "删除知识库"},
        
        # 文档管理权限
        {"name": "文档管理", "code": "document:manage", "group": "document", "resource": "document", "action": "manage", "permission_type": "menu", "menu_path": "/documents", "menu_icon": "FileTextOutlined", "description": "文档管理菜单"},
        {"name": "查看文档", "code": "document:view", "group": "document", "resource": "document", "action": "view", "permission_type": "api", "description": "查看文档"},
        {"name": "上传文档", "code": "document:upload", "group": "document", "resource": "document", "action": "upload", "permission_type": "api", "description": "上传文档"},
        {"name": "编辑文档", "code": "document:update", "group": "document", "resource": "document", "action": "update", "permission_type": "api", "description": "编辑文档"},
        {"name": "删除文档", "code": "document:delete", "group": "document", "resource": "document", "action": "delete", "permission_type": "api", "description": "删除文档"},
        
        # 聊天功能权限
        {"name": "聊天功能", "code": "chat:access", "group": "chat", "resource": "chat", "action": "access", "permission_type": "menu", "menu_path": "/chat", "menu_icon": "MessageOutlined", "description": "聊天功能菜单"},
        {"name": "发送消息", "code": "chat:send", "group": "chat", "resource": "chat", "action": "send", "permission_type": "api", "description": "发送聊天消息"},
        {"name": "查看历史", "code": "chat:history", "group": "chat", "resource": "chat", "action": "history", "permission_type": "api", "description": "查看聊天历史"},
        
        # 搜索功能权限
        {"name": "搜索功能", "code": "search:access", "group": "search", "resource": "search", "action": "access", "permission_type": "menu", "menu_path": "/search", "menu_icon": "SearchOutlined", "description": "搜索功能菜单"},
        {"name": "基础搜索", "code": "search:basic", "group": "search", "resource": "search", "action": "basic", "permission_type": "api", "description": "基础搜索功能"},
        {"name": "高级搜索", "code": "search:advanced", "group": "search", "resource": "search", "action": "advanced", "permission_type": "api", "description": "高级搜索功能"},
        
        # 监控管理权限
        {"name": "监控管理", "code": "monitor:view", "group": "monitor", "resource": "monitor", "action": "view", "permission_type": "menu", "menu_path": "/monitor", "menu_icon": "DashboardOutlined", "description": "监控管理菜单"},
        {"name": "系统监控", "code": "monitor:system", "group": "monitor", "resource": "monitor", "action": "system", "permission_type": "api", "description": "系统监控"},
        {"name": "业务监控", "code": "monitor:business", "group": "monitor", "resource": "monitor", "action": "business", "permission_type": "api", "description": "业务监控"},
    ]
    
    for perm_data in permissions:
        permission = await Permission.get_or_none(code=perm_data["code"])
        if not permission:
            await Permission.create(**perm_data)
            logger.info(f"创建权限: {perm_data['name']}")


async def create_basic_roles():
    """创建基础角色"""
    roles = [
        {
            "name": "超级管理员",
            "code": "super_admin",
            "description": "系统超级管理员，拥有所有权限",
            "role_type": "system",
            "data_scope": "all"
        },
        {
            "name": "系统管理员",
            "code": "admin",
            "description": "系统管理员，拥有系统管理权限",
            "role_type": "system",
            "data_scope": "all"
        },
        {
            "name": "部门管理员",
            "code": "dept_admin",
            "description": "部门管理员，拥有本部门及子部门数据权限",
            "role_type": "custom",
            "data_scope": "dept_and_child"
        },
        {
            "name": "普通用户",
            "code": "user",
            "description": "普通用户，拥有基础功能权限",
            "role_type": "custom",
            "data_scope": "dept"
        },
        {
            "name": "访客",
            "code": "guest",
            "description": "访客用户，只有查看权限",
            "role_type": "custom",
            "data_scope": "custom"
        }
    ]
    
    for role_data in roles:
        role = await Role.get_or_none(code=role_data["code"])
        if not role:
            await Role.create(**role_data)
            logger.info(f"创建角色: {role_data['name']}")


async def create_basic_departments():
    """创建基础部门"""
    departments = [
        {
            "name": "总公司",
            "code": "company",
            "description": "总公司",
            "parent_id": None,
            "level": 0,
            "sort_order": 1
        },
        {
            "name": "技术部",
            "code": "tech",
            "description": "技术开发部门",
            "parent_id": None,  # 将在创建后设置
            "level": 1,
            "sort_order": 1
        },
        {
            "name": "产品部",
            "code": "product",
            "description": "产品管理部门",
            "parent_id": None,  # 将在创建后设置
            "level": 1,
            "sort_order": 2
        },
        {
            "name": "运营部",
            "code": "operation",
            "description": "运营管理部门",
            "parent_id": None,  # 将在创建后设置
            "level": 1,
            "sort_order": 3
        }
    ]
    
    # 创建总公司
    company = await Department.get_or_none(code="company")
    if not company:
        company = await Department.create(departments[0])
        logger.info(f"创建部门: {departments[0]['name']}")
    
    # 创建子部门
    for dept_data in departments[1:]:
        dept = await Department.get_or_none(code=dept_data["code"])
        if not dept:
            dept_data["parent_id"] = company.id
            await Department.create(dept_data)
            logger.info(f"创建部门: {dept_data['name']}")


async def assign_role_permissions():
    """分配角色权限"""
    # 超级管理员拥有所有权限
    super_admin = await Role.get_or_none(code="super_admin")
    if super_admin:
        permissions = await Permission.all()
        for permission in permissions:
            role_perm = await RolePermission.get_or_none(role_id=super_admin.id, permission_id=permission.id)
            if not role_perm:
                await RolePermission.create(role_id=super_admin.id, permission_id=permission.id)
        logger.info("为超级管理员分配所有权限")
    
    # 系统管理员权限
    admin = await Role.get_or_none(code="admin")
    if admin:
        admin_permissions = [
            "system:manage", "system:config", "system:monitor",
            "user:manage", "user:view", "user:create", "user:update", "user:delete", "user:reset_password",
            "role:manage", "role:view", "role:create", "role:update", "role:delete", "role:assign_permission",
            "permission:manage", "permission:view",
            "dept:manage", "dept:view", "dept:create", "dept:update", "dept:delete",
            "user_role:manage",
            "knowledge:manage", "knowledge:view", "knowledge:create", "knowledge:update", "knowledge:delete",
            "document:manage", "document:view", "document:upload", "document:update", "document:delete",
            "chat:access", "chat:send", "chat:history",
            "search:access", "search:basic", "search:advanced",
            "monitor:view", "monitor:system", "monitor:business"
        ]
        await _assign_permissions_to_role(admin, admin_permissions)
        logger.info("为系统管理员分配权限")
    
    # 部门管理员权限
    dept_admin = await Role.get_or_none(code="dept_admin")
    if dept_admin:
        dept_admin_permissions = [
            "user:view", "user:create", "user:update",
            "knowledge:view", "knowledge:create", "knowledge:update",
            "document:view", "document:upload", "document:update",
            "chat:access", "chat:send", "chat:history",
            "search:access", "search:basic", "search:advanced"
        ]
        await _assign_permissions_to_role(dept_admin, dept_admin_permissions)
        logger.info("为部门管理员分配权限")
    
    # 普通用户权限
    user = await Role.get_or_none(code="user")
    if user:
        user_permissions = [
            "knowledge:view",
            "document:view", "document:upload",
            "chat:access", "chat:send", "chat:history",
            "search:access", "search:basic"
        ]
        await _assign_permissions_to_role(user, user_permissions)
        logger.info("为普通用户分配权限")
    
    # 访客权限
    guest = await Role.get_or_none(code="guest")
    if guest:
        guest_permissions = [
            "knowledge:view",
            "document:view",
            "search:access", "search:basic"
        ]
        await _assign_permissions_to_role(guest, guest_permissions)
        logger.info("为访客分配权限")


async def _assign_permissions_to_role(role: Role, permission_codes: list):
    """为角色分配权限"""
    for perm_code in permission_codes:
        permission = await Permission.get_or_none(code=perm_code)
        if permission:
            role_perm = await RolePermission.get_or_none(role_id=role.id, permission_id=permission.id)
            if not role_perm:
                await RolePermission.create(role_id=role.id, permission_id=permission.id)
