# RBAC错误修复指南

## 问题描述

如果您遇到以下错误：
```
(1054, "Unknown column 'menu_icon' in 'field list'")
```

这是因为数据库中的表结构与新的RBAC模型不匹配导致的。

## 快速修复方法

### 方法一：使用自动修复脚本（推荐）

```bash
cd enterprise-rag-system/backend
python fix_rbac_error.py
```

这个脚本会：
1. 删除有问题的RBAC相关表
2. 更新users表结构
3. 重新创建正确的表结构
4. 创建默认管理员用户

### 方法二：完整重置RBAC系统

```bash
cd enterprise-rag-system/backend
python setup_rbac.py
```

这个脚本会：
1. 完全重置RBAC数据库
2. 重新初始化所有RBAC数据
3. 创建默认用户和角色
4. 分配基础权限

### 方法三：手动修复

如果自动脚本无法解决问题，可以手动执行以下SQL：

```sql
-- 禁用外键检查
SET FOREIGN_KEY_CHECKS = 0;

-- 删除RBAC相关表
DROP TABLE IF EXISTS user_events;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS user_permissions;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS role_departments;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS permission_groups;

-- 为users表添加department_id字段（如果不存在）
ALTER TABLE users ADD COLUMN department_id INT NULL COMMENT '所属部门ID';

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;
```

## 修复后的操作

1. **重新启动应用程序**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **使用默认管理员账户登录**
   - 用户名: `admin`
   - 密码: `admin123`

3. **访问管理界面配置权限**
   - 角色管理: `/admin/roles`
   - 权限管理: `/admin/permissions`
   - 用户管理: `/admin/users`

## 默认创建的账户

修复脚本会创建以下测试账户：

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | admin123 | 超级管理员 | 拥有所有权限 |
| test_user | test123 | 普通用户 | 基础功能权限 |
| dept_admin | dept123 | 部门管理员 | 部门数据权限 |

## 验证修复结果

修复完成后，您可以：

1. **检查表结构**
   ```sql
   SHOW TABLES LIKE '%role%';
   SHOW TABLES LIKE '%permission%';
   SHOW TABLES LIKE '%department%';
   ```

2. **测试登录**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin&password=admin123"
   ```

3. **测试权限API**
   ```bash
   # 获取角色列表
   curl -X GET "http://localhost:8000/api/v1/rbac/roles" \
        -H "Authorization: Bearer YOUR_TOKEN"
   
   # 获取权限列表
   curl -X GET "http://localhost:8000/api/v1/rbac/permissions" \
        -H "Authorization: Bearer YOUR_TOKEN"
   ```

## 常见问题

### Q: 修复脚本运行失败怎么办？

A: 请检查：
1. 数据库连接配置是否正确
2. 数据库用户是否有足够的权限（CREATE, DROP, ALTER）
3. 网络连接是否正常

### Q: 修复后仍然有错误怎么办？

A: 请尝试：
1. 完全删除数据库并重新创建
2. 检查环境变量配置
3. 查看详细的错误日志

### Q: 如何备份现有数据？

A: 在运行修复脚本前，建议备份数据库：
```bash
mysqldump -u root -p enterprise_rag > backup.sql
```

### Q: 如何恢复备份？

A: 如果需要恢复备份：
```bash
mysql -u root -p enterprise_rag < backup.sql
```

## 技术支持

如果您在修复过程中遇到问题，请：

1. 查看应用程序日志
2. 检查数据库错误日志
3. 确认环境配置正确
4. 联系技术支持团队

## 预防措施

为避免类似问题再次发生：

1. **定期备份数据库**
2. **在生产环境中谨慎执行数据库迁移**
3. **使用版本控制管理数据库结构变更**
4. **在测试环境中先验证所有变更**

---

**注意**: 这些修复脚本会删除现有的RBAC相关数据。如果您有重要的用户角色权限数据，请先备份数据库。
