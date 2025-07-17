# schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import enum

# Import Enums from models to reuse them
from models import OrderStatusEnum, PolicyTypeEnum, FeedbackTypeEnum

# --- Base Models ---
# Define base models with common fields, allowing ORM mode
class BaseSchema(BaseModel):
    class Config:
        orm_mode = True # Enable ORM mode for automatic mapping
        use_enum_values = True # Use enum values instead of names

# --- Enums for Schemas (optional, can use model enums directly) ---
# Often useful if API enums differ slightly or for clarity

# --- Product Schemas ---
class ProductBase(BaseSchema):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0) # Price must be greater than 0
    sku: Optional[str] = None
    image_url: Optional[str] = None
    specifications: Optional[str] = None # Consider using Dict[str, Any] if parsing JSON

class ProductCreate(ProductBase):
    stock_quantity: int = Field(..., ge=0) # Stock cannot be negative
    category_id: int

class Product(ProductBase): # Schema for reading product data
    id: int
    stock_quantity: int
    category_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class ProductSearchResult(BaseSchema):
    id: int
    name: str
    price: float
    image_url: Optional[str] = None
    stock_quantity: int

# --- Category Schemas ---
class CategoryBase(BaseSchema):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase): # Schema for reading category data
    id: int
    products: List[Product] = [] # Include related products

# --- Order Schemas ---
class OrderItemBase(BaseSchema):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderItemCreate(OrderItemBase):
    pass # Price per unit will be set based on current product price

class OrderItem(OrderItemBase): # Schema for reading order item data
    id: int
    price_per_unit: float
    product: ProductSearchResult # Show basic product info

class OrderBase(BaseSchema):
    user_id: int # In real c_app, get from auth token
    shipping_address_id: int
    billing_address_id: int

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class ShipmentBase(BaseSchema):
    order_id: int
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    status: Optional[str] = None

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentInfo(ShipmentBase):
    pass

class Order(OrderBase): # Schema for reading order data
    id: int
    order_number: str
    order_date: datetime
    status: OrderStatusEnum # Use the enum
    total_amount: float
    items: List[OrderItem]
    shipment: Optional[ShipmentInfo] = None # Include shipment details if available

class OrderStatusUpdate(BaseSchema):
    status: OrderStatusEnum

class OrderStatusResult(BaseSchema):
    order_number: str
    status: OrderStatusEnum
    estimated_delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None # Example: Generate tracking URL

class OrderCancelResult(BaseSchema):
    order_number: str
    status: OrderStatusEnum # Should be 'cancelled'
    message: str
# --- Promotion Schemas ---
class PromotionBase(BaseSchema):
    code: Optional[str] = None
    description: str
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount_amount: Optional[float] = Field(None, ge=0)
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    minimum_spend: Optional[float] = Field(None, ge=0)

class PromotionCreate(PromotionBase):
    pass

class Promotion(PromotionBase): # Schema for reading promotion data
    id: int

# --- Policy Schemas ---
class PolicyBase(BaseSchema):
    policy_type: PolicyTypeEnum
    content: str
    version: Optional[str] = None

class PolicyCreate(PolicyBase):
    pass

class Policy(PolicyBase): # Schema for reading policy data
    id: int
    last_updated: datetime

# --- Return Schemas ---
class ReturnRequestBase(BaseSchema):
    order_id: int
    product_id: int
    reason: str

class ReturnRequestCreate(ReturnRequestBase):
    user_id: int # Should ideally come from auth

class ReturnRequest(ReturnRequestBase): # Schema for reading return request data
    id: int
    user_id: int
    status: str
    requested_date: datetime
    resolution_date: Optional[datetime] = None

class ReturnEligibilityCheck(BaseSchema):
    order_number: str
    product_sku: str

class ReturnEligibilityResult(BaseSchema):
    is_eligible: bool
    reason: Optional[str] = None # Reason if not eligible
    policy_summary: Optional[str] = None # Snippet of return policy

# --- Feedback Schemas ---
class FeedbackBase(BaseSchema):
    feedback_type: FeedbackTypeEnum
    subject: Optional[str] = None
    content: str
    email: Optional[EmailStr] = None # Allow anonymous feedback with optional email

class FeedbackCreate(FeedbackBase):
    user_id: Optional[int] = None # Optional user ID

class Feedback(FeedbackBase): # Schema for reading feedback data
    id: int
    user_id: Optional[int] = None
    timestamp: datetime
    is_resolved: bool

# --- User Schemas (Simplified) ---
class UserBase(BaseSchema):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str # Plain password during creation, hash before saving

class User(UserBase): # Schema for reading user data
    id: int
    is_active: bool
    created_at: datetime

# --- Address Schemas ---
class AddressBase(BaseSchema):
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "CN"

class AddressCreate(AddressBase):
    user_id: int

class Address(AddressBase): # Schema for reading address data
    id: int
    user_id: int
    is_default_shipping: bool
    is_default_billing: bool

