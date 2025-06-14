from enum import Enum

from tortoise import fields

from .base import BaseModel


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"  # 待付款
    PAID = "paid"  # 已付款
    SHIPPED = "shipped"  # 已发货
    DELIVERED = "delivered"  # 已送达
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款


class Order(BaseModel):
    """订单"""
    
    order_number = fields.CharField(max_length=50, unique=True, description="订单号")
    customer = fields.ForeignKeyField("models.Customer", related_name="orders", description="客户")
    status = fields.CharEnumField(OrderStatus, default=OrderStatus.PENDING, description="订单状态")
    
    # 金额信息
    subtotal = fields.DecimalField(max_digits=12, decimal_places=2, description="小计")
    shipping_fee = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="运费")
    discount_amount = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="折扣金额")
    total_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="总金额")
    
    # 收货信息
    shipping_name = fields.CharField(max_length=100, description="收货人姓名")
    shipping_phone = fields.CharField(max_length=20, description="收货人电话")
    shipping_address = fields.CharField(max_length=500, description="收货地址")
    
    # 物流信息
    tracking_number = fields.CharField(max_length=100, null=True, description="物流单号")
    shipping_company = fields.CharField(max_length=100, null=True, description="物流公司")
    
    # 时间信息
    paid_at = fields.DatetimeField(null=True, description="付款时间")
    shipped_at = fields.DatetimeField(null=True, description="发货时间")
    delivered_at = fields.DatetimeField(null=True, description="送达时间")
    
    # 备注
    notes = fields.TextField(null=True, description="订单备注")
    
    class Meta:
        table = "shop_orders"
        
    def __str__(self):
        return f"订单 {self.order_number}"


class OrderItem(BaseModel):
    """订单项"""
    
    order = fields.ForeignKeyField("models.Order", related_name="items", description="订单")
    product = fields.ForeignKeyField("models.Product", related_name="order_items", description="商品")
    product_name = fields.CharField(max_length=200, description="商品名称")
    product_sku = fields.CharField(max_length=100, description="商品SKU")
    price = fields.DecimalField(max_digits=10, decimal_places=2, description="单价")
    quantity = fields.IntField(description="数量")
    total_price = fields.DecimalField(max_digits=12, decimal_places=2, description="小计")
    
    class Meta:
        table = "shop_order_items"
        
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
