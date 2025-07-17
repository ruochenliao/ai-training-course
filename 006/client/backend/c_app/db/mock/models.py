# models.py
from sqlalchemy import (Column, Integer, String, Float, DateTime, ForeignKey,
                        Text, Enum as SQLAlchemyEnum, Boolean)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # For default timestamp
import enum

from database import Base # Import Base from database.py

# --- Enums ---
# Using Python's standard Enum
class OrderStatusEnum(str, enum.Enum): # Inherit from str for easier JSON serialization
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURN_REQUESTED = "return_requested"
    RETURNED = "returned"

class PolicyTypeEnum(str, enum.Enum): # Inherit from str
    RETURN = "return"
    SHIPPING = "shipping"
    PAYMENT = "payment"
    PRIVACY = "privacy"
    TERMS = "terms"

class FeedbackTypeEnum(str, enum.Enum): # Inherit from str
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    PRAISE = "praise"

# --- Models ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False) # Store hashed passwords only!
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    orders = relationship("Order", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")
    addresses = relationship("Address", back_populates="user")

class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False, default="CN") # Example default
    is_default_shipping = Column(Boolean, default=False)
    is_default_billing = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="addresses")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)

    # Relationships
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    sku = Column(String, unique=True, index=True) # Stock Keeping Unit
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String) # URL to product image
    specifications = Column(Text) # Could be JSON stored as text
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    returns = relationship("ReturnRequest", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False) # Public facing order ID
    user_id = Column(Integer, ForeignKey("users.id"))
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    # Use SQLAlchemyEnum with the Python Enum. Pass the Enum class itself.
    status = Column(SQLAlchemyEnum(OrderStatusEnum, name="orderstatusenum"), default=OrderStatusEnum.PENDING, nullable=False)
    total_amount = Column(Float, nullable=False)
    shipping_address_id = Column(Integer, ForeignKey("addresses.id")) # Link to address table
    billing_address_id = Column(Integer, ForeignKey("addresses.id")) # Link to address table

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    shipment = relationship("Shipment", back_populates="order", uselist=False) # One-to-one

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False) # Price at the time of order

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True) # Each order has one shipment record
    carrier = Column(String)
    tracking_number = Column(String, index=True)
    shipped_date = Column(DateTime(timezone=True))
    estimated_delivery_date = Column(DateTime(timezone=True))
    actual_delivery_date = Column(DateTime(timezone=True))
    status = Column(String) # e.g., 'In Transit', 'Out for Delivery'

    # Relationships
    order = relationship("Order", back_populates="shipment")

class Promotion(Base):
    __tablename__ = "promotions"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True) # e.g., SUMMER20
    description = Column(Text, nullable=False)
    discount_percentage = Column(Float) # e.g., 10.0 for 10%
    discount_amount = Column(Float) # e.g., 50.0 for ¥50 off
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    minimum_spend = Column(Float) # Minimum order value to apply

class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    # **MODIFIED LINE BELOW**
    # Ensure SQLAlchemy uses the enum *values* ('return', 'shipping') for DB mapping
    # by providing values_callable. This aligns with Pydantic's use_enum_values=True.
    # Also added inherit_schema=True for potentially better cross-DB compatibility.
    policy_type = Column(SQLAlchemyEnum(PolicyTypeEnum,
                                        name="policytypeenum_check", # Explicit name for the constraint/type in DB
                                        values_callable=lambda obj: [e.value for e in obj], # Use enum values
                                        inherit_schema=True), # Helps with some DB backends/schemas
                         nullable=False, index=True)
    content = Column(Text, nullable=False) # The actual policy text
    version = Column(String) # e.g., "v1.2"
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ReturnRequest(Base):
    __tablename__ = "return_requests"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(Integer, ForeignKey("users.id")) # User who requested
    reason = Column(Text)
    status = Column(String, default="Pending") # e.g., Pending, Approved, Rejected, Received, Refunded
    requested_date = Column(DateTime(timezone=True), server_default=func.now())
    resolution_date = Column(DateTime(timezone=True))

    # Relationships
    order = relationship("Order") # Simplified relationship
    product = relationship("Product", back_populates="returns")
    user = relationship("User")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Can be anonymous
    email = Column(String, nullable=True) # If anonymous user provides email
    feedback_type = Column(SQLAlchemyEnum(FeedbackTypeEnum, name="feedbacktypeenum"), nullable=False) # Pass Enum class
    subject = Column(String)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_resolved = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="feedback")

# Also ensure other Enums inherit from str and are passed correctly to SQLAlchemyEnum
# Updated OrderStatusEnum, PolicyTypeEnum, FeedbackTypeEnum to inherit str
# Updated Order.status and Feedback.feedback_type to pass Enum class to SQLAlchemyEnum constructor
