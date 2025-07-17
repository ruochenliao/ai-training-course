from tortoise import fields

from .base import BaseModel


class Customer(BaseModel):
    """客户"""
    
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    email = fields.CharField(max_length=100, unique=True, description="邮箱")
    phone = fields.CharField(max_length=20, null=True, description="手机号")
    password_hash = fields.CharField(max_length=255, description="密码哈希")
    first_name = fields.CharField(max_length=50, null=True, description="名")
    last_name = fields.CharField(max_length=50, null=True, description="姓")
    avatar = fields.CharField(max_length=500, null=True, description="头像URL")
    birth_date = fields.DateField(null=True, description="生日")
    gender = fields.CharField(max_length=10, null=True, description="性别")
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_verified = fields.BooleanField(default=False, description="是否验证")
    last_login = fields.DatetimeField(null=True, description="最后登录时间")
    total_orders = fields.IntField(default=0, description="总订单数")
    total_spent = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="总消费金额")
    
    class Meta:
        table = "shop_customers"
        
    def __str__(self):
        return self.username
        
    @property
    def full_name(self):
        """全名"""
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        return self.username


class CustomerAddress(BaseModel):
    """客户地址"""
    
    customer = fields.ForeignKeyField("models.Customer", related_name="addresses", description="客户")
    name = fields.CharField(max_length=100, description="收货人姓名")
    phone = fields.CharField(max_length=20, description="收货人电话")
    province = fields.CharField(max_length=50, description="省份")
    city = fields.CharField(max_length=50, description="城市")
    district = fields.CharField(max_length=50, description="区县")
    address = fields.CharField(max_length=200, description="详细地址")
    postal_code = fields.CharField(max_length=10, null=True, description="邮政编码")
    is_default = fields.BooleanField(default=False, description="是否默认地址")
    
    class Meta:
        table = "shop_customer_addresses"
        
    def __str__(self):
        return f"{self.name} - {self.province}{self.city}{self.district}{self.address}"
