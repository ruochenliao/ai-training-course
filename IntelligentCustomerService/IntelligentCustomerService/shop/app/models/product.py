from tortoise import fields

from .base import BaseModel


class Category(BaseModel):
    """商品分类"""
    
    name = fields.CharField(max_length=100, description="分类名称")
    description = fields.TextField(null=True, description="分类描述")
    parent = fields.ForeignKeyField("models.Category", related_name="children", null=True, description="父分类")
    sort_order = fields.IntField(default=0, description="排序")
    is_active = fields.BooleanField(default=True, description="是否启用")
    
    class Meta:
        table = "shop_categories"
        
    def __str__(self):
        return self.name


class Product(BaseModel):
    """商品"""
    
    name = fields.CharField(max_length=200, description="商品名称")
    description = fields.TextField(description="商品描述")
    short_description = fields.CharField(max_length=500, null=True, description="简短描述")
    sku = fields.CharField(max_length=100, unique=True, description="商品SKU")
    price = fields.DecimalField(max_digits=10, decimal_places=2, description="价格")
    original_price = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description="原价")
    cost_price = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description="成本价")
    stock = fields.IntField(default=0, description="库存数量")
    min_stock = fields.IntField(default=0, description="最低库存")
    weight = fields.DecimalField(max_digits=8, decimal_places=2, null=True, description="重量(kg)")
    dimensions = fields.CharField(max_length=100, null=True, description="尺寸")
    category = fields.ForeignKeyField("models.Category", related_name="products", description="分类")
    brand = fields.CharField(max_length=100, null=True, description="品牌")
    tags = fields.CharField(max_length=500, null=True, description="标签")
    is_active = fields.BooleanField(default=True, description="是否上架")
    is_featured = fields.BooleanField(default=False, description="是否推荐")
    rating = fields.DecimalField(max_digits=3, decimal_places=2, default=0, description="评分")
    review_count = fields.IntField(default=0, description="评论数量")
    sales_count = fields.IntField(default=0, description="销量")
    view_count = fields.IntField(default=0, description="浏览量")
    
    class Meta:
        table = "shop_products"
        
    def __str__(self):
        return self.name
        
    @property
    def is_in_stock(self):
        """是否有库存"""
        return self.stock > 0
        
    @property
    def is_low_stock(self):
        """是否库存不足"""
        return self.stock <= self.min_stock


class ProductImage(BaseModel):
    """商品图片"""
    
    product = fields.ForeignKeyField("models.Product", related_name="images", description="商品")
    image_url = fields.CharField(max_length=500, description="图片URL")
    alt_text = fields.CharField(max_length=200, null=True, description="替代文本")
    sort_order = fields.IntField(default=0, description="排序")
    is_primary = fields.BooleanField(default=False, description="是否主图")
    
    class Meta:
        table = "shop_product_images"
