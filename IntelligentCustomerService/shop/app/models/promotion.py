from enum import Enum

from tortoise import fields

from .base import BaseModel


class PromotionType(str, Enum):
    """促销类型"""
    DISCOUNT = "discount"  # 折扣
    FIXED_AMOUNT = "fixed_amount"  # 固定金额
    FREE_SHIPPING = "free_shipping"  # 免运费
    BUY_ONE_GET_ONE = "buy_one_get_one"  # 买一送一


class CouponType(str, Enum):
    """优惠券类型"""
    PERCENTAGE = "percentage"  # 百分比折扣
    FIXED_AMOUNT = "fixed_amount"  # 固定金额
    FREE_SHIPPING = "free_shipping"  # 免运费


class Promotion(BaseModel):
    """促销活动"""
    
    name = fields.CharField(max_length=200, description="活动名称")
    description = fields.TextField(description="活动描述")
    type = fields.CharEnumField(PromotionType, description="促销类型")
    discount_value = fields.DecimalField(max_digits=10, decimal_places=2, description="折扣值")
    min_order_amount = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="最低订单金额")
    max_discount_amount = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description="最大折扣金额")
    start_date = fields.DatetimeField(description="开始时间")
    end_date = fields.DatetimeField(description="结束时间")
    is_active = fields.BooleanField(default=True, description="是否启用")
    usage_limit = fields.IntField(null=True, description="使用次数限制")
    used_count = fields.IntField(default=0, description="已使用次数")
    
    class Meta:
        table = "shop_promotions"
        
    def __str__(self):
        return self.name
        
    @property
    def is_available(self):
        """是否可用"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return (self.is_active and
                self.start_date <= now <= self.end_date and
                (self.usage_limit is None or self.used_count < self.usage_limit))


class Coupon(BaseModel):
    """优惠券"""
    
    code = fields.CharField(max_length=50, unique=True, description="优惠券代码")
    name = fields.CharField(max_length=200, description="优惠券名称")
    description = fields.TextField(null=True, description="优惠券描述")
    type = fields.CharEnumField(CouponType, description="优惠券类型")
    discount_value = fields.DecimalField(max_digits=10, decimal_places=2, description="折扣值")
    min_order_amount = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="最低订单金额")
    max_discount_amount = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description="最大折扣金额")
    start_date = fields.DatetimeField(description="开始时间")
    end_date = fields.DatetimeField(description="结束时间")
    is_active = fields.BooleanField(default=True, description="是否启用")
    usage_limit = fields.IntField(null=True, description="使用次数限制")
    used_count = fields.IntField(default=0, description="已使用次数")
    user_limit = fields.IntField(default=1, description="每用户使用次数限制")
    
    class Meta:
        table = "shop_coupons"
        
    def __str__(self):
        return f"{self.name} ({self.code})"
        
    @property
    def is_available(self):
        """是否可用"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return (self.is_active and
                self.start_date <= now <= self.end_date and
                (self.usage_limit is None or self.used_count < self.usage_limit))


class CouponUsage(BaseModel):
    """优惠券使用记录"""
    
    coupon = fields.ForeignKeyField("models.Coupon", related_name="usages", description="优惠券")
    customer = fields.ForeignKeyField("models.Customer", related_name="coupon_usages", description="客户")
    order = fields.ForeignKeyField("models.Order", related_name="coupon_usages", description="订单")
    discount_amount = fields.DecimalField(max_digits=10, decimal_places=2, description="折扣金额")
    
    class Meta:
        table = "shop_coupon_usages"
        
    def __str__(self):
        return f"{self.customer.username} 使用 {self.coupon.code}"
