from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base, TimestampMixin


class ShopItem(Base, TimestampMixin):
    __tablename__ = 'shop_items'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    item_type = Column(String(50), nullable=False)  # currency, boost, cosmetic, etc.
    is_active = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)  # Use NULL for unlimited
    
    # Relationships
    product_files = relationship("ProductFile", back_populates="shop_item")
    inventory_items = relationship("InventoryItem", back_populates="item")


class ProductFile(Base, TimestampMixin):
    __tablename__ = 'product_files'
    
    id = Column(Integer, primary_key=True, index=True)
    shop_item_id = Column(Integer, ForeignKey('shop_items.id'), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    shop_item = relationship("ShopItem", back_populates="product_files")


class InventoryItem(Base, TimestampMixin):
    __tablename__ = 'inventory_items'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    shop_item_id = Column(Integer, ForeignKey('shop_items.id'))
    quantity = Column(Integer, default=1)
    is_consumed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="inventory_items")
    item = relationship("ShopItem", back_populates="inventory_items")


class UserPurchase(Base, TimestampMixin):
    __tablename__ = 'user_purchases'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    shop_item_id = Column(Integer, ForeignKey('shop_items.id'))
    quantity = Column(Integer, default=1)
    total_amount = Column(Numeric(10, 2), nullable=False)
    transaction_id = Column(String(255))  # External transaction ID
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    item = relationship("ShopItem")