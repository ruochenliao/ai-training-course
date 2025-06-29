from tortoise import fields

from .base import BaseModel


class Cart(BaseModel):
    """购物车"""
    
    customer = fields.ForeignKeyField("models.Customer", related_name="carts", description="客户")
    session_id = fields.CharField(max_length=255, null=True, description="会话ID（用于未登录用户）")
    
    class Meta:
        table = "shop_carts"
        
    def __str__(self):
        return f"Cart for {self.customer.username if self.customer else self.session_id}"


class CartItem(BaseModel):
    """购物车项"""
    
    cart = fields.ForeignKeyField("models.Cart", related_name="items", description="购物车")
    product = fields.ForeignKeyField("models.Product", related_name="cart_items", description="商品")
    quantity = fields.IntField(description="数量")
    
    class Meta:
        table = "shop_cart_items"
        unique_together = (("cart", "product"),)
        
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
        
    @property
    def subtotal(self):
        """小计"""
        return self.product.price * self.quantity if self.product else 0
