/**
 * 中文语言包
 */

export default {
  // 通用
  common: {
    confirm: '确认',
    cancel: '取消',
    submit: '提交',
    reset: '重置',
    search: '搜索',
    add: '添加',
    edit: '编辑',
    delete: '删除',
    detail: '详情',
    back: '返回',
    save: '保存',
    success: '操作成功',
    failed: '操作失败',
    loading: '加载中...',
    noData: '暂无数据',
    pleaseSelect: '请选择',
    pleaseInput: '请输入',
    all: '全部',
    more: '更多',
    yes: '是',
    no: '否',
    enable: '启用',
    disable: '禁用',
    enabled: '已启用',
    disabled: '已禁用',
    status: '状态',
    action: '操作',
    remark: '备注',
    createTime: '创建时间',
    updateTime: '更新时间',
    creator: '创建人',
    updater: '更新人',
    unknown: '未知'
  },
  
  // 菜单
  menu: {
    dashboard: '仪表盘',
    system: '系统管理',
    user: '用户管理',
    role: '角色管理',
    permission: '权限管理',
    menu: '菜单管理',
    department: '部门管理',
    position: '岗位管理',
    dict: '字典管理',
    log: '日志管理',
    loginLog: '登录日志',
    operationLog: '操作日志',
    setting: '系统设置',
    profile: '个人中心'
  },
  
  // 登录页
  login: {
    title: 'RBAC权限管理系统',
    username: '用户名',
    password: '密码',
    captcha: '验证码',
    rememberMe: '记住我',
    forgetPassword: '忘记密码',
    login: '登录',
    loginSuccess: '登录成功',
    loginFailed: '登录失败',
    usernameRequired: '请输入用户名',
    passwordRequired: '请输入密码',
    captchaRequired: '请输入验证码',
    userNotExist: '用户不存在',
    passwordError: '密码错误',
    accountLocked: '账号已锁定',
    accountDisabled: '账号已禁用',
    captchaError: '验证码错误'
  },
  
  // 用户管理
  user: {
    username: '用户名',
    nickname: '昵称',
    realName: '真实姓名',
    password: '密码',
    confirmPassword: '确认密码',
    email: '邮箱',
    mobile: '手机号',
    gender: '性别',
    male: '男',
    female: '女',
    birthday: '生日',
    avatar: '头像',
    role: '角色',
    department: '部门',
    position: '岗位',
    lastLoginTime: '最后登录时间',
    lastLoginIp: '最后登录IP',
    passwordNotMatch: '两次输入的密码不一致',
    resetPassword: '重置密码',
    resetPasswordSuccess: '重置密码成功',
    resetPasswordFailed: '重置密码失败',
    changePassword: '修改密码',
    oldPassword: '原密码',
    newPassword: '新密码',
    confirmNewPassword: '确认新密码',
    changePasswordSuccess: '修改密码成功',
    changePasswordFailed: '修改密码失败',
    oldPasswordError: '原密码错误'
  },
  
  // 角色管理
  role: {
    roleName: '角色名称',
    roleCode: '角色编码',
    roleDesc: '角色描述',
    permission: '权限',
    assignPermission: '分配权限',
    assignPermissionSuccess: '分配权限成功',
    assignPermissionFailed: '分配权限失败'
  },
  
  // 权限管理
  permission: {
    permissionName: '权限名称',
    permissionCode: '权限编码',
    permissionDesc: '权限描述',
    permissionType: '权限类型',
    menu: '菜单',
    button: '按钮',
    api: 'API',
    permissionUrl: '权限URL',
    permissionMethod: '请求方法',
    permissionParent: '父级权限',
    permissionIcon: '图标',
    permissionSort: '排序',
    permissionStatus: '状态'
  },
  
  // 部门管理
  department: {
    departmentName: '部门名称',
    departmentCode: '部门编码',
    departmentDesc: '部门描述',
    departmentParent: '父级部门',
    departmentLeader: '部门负责人',
    departmentSort: '排序'
  },
  
  // 岗位管理
  position: {
    positionName: '岗位名称',
    positionCode: '岗位编码',
    positionDesc: '岗位描述',
    positionSort: '排序'
  },
  
  // 字典管理
  dict: {
    dictName: '字典名称',
    dictCode: '字典编码',
    dictDesc: '字典描述',
    dictType: '字典类型',
    dictValue: '字典值',
    dictLabel: '字典标签',
    dictSort: '排序',
    dictStatus: '状态'
  },
  
  // 日志管理
  log: {
    loginLog: '登录日志',
    operationLog: '操作日志',
    username: '用户名',
    operation: '操作',
    method: '方法',
    params: '参数',
    result: '结果',
    ip: 'IP地址',
    time: '耗时',
    createTime: '创建时间',
    status: '状态',
    success: '成功',
    failed: '失败'
  },
  
  // 系统设置
  setting: {
    systemName: '系统名称',
    systemLogo: '系统Logo',
    systemDesc: '系统描述',
    systemFooter: '系统页脚',
    systemTheme: '系统主题',
    systemColor: '系统颜色',
    systemLanguage: '系统语言',
    systemNotice: '系统公告',
    systemVersion: '系统版本',
    systemAuthor: '系统作者',
    systemAuthorWebsite: '作者网站',
    systemCopyright: '版权信息'
  },
  
  // 个人中心
  profile: {
    basicInfo: '基本信息',
    securitySetting: '安全设置',
    changePassword: '修改密码',
    bindMobile: '绑定手机',
    bindEmail: '绑定邮箱',
    accountSecurity: '账号安全',
    loginLog: '登录日志',
    operationLog: '操作日志'
  },
  
  // 错误页面
  error: {
    notFound: '页面不存在',
    serverError: '服务器错误',
    forbidden: '没有权限',
    unauthorized: '未授权',
    goBack: '返回上一页',
    goHome: '返回首页'
  }
}