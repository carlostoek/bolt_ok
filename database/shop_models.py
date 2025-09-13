"""
Shop System Database Models
Modelos para el sistema de tienda integrado con el ecosistema existente.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class ShopItem(Base):
    """Artículos disponibles en la tienda."""
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)  # Precio en besitos/visitos
    category = Column(String, nullable=True)  # categoria: "tools", "hints", "cosmetics", etc.
    
    # Configuración de acceso
    is_vip_exclusive = Column(Boolean, default=False)
    required_level = Column(Integer, default=1)
    
    # Integración con narrativa
    unlocks_lore_piece_code = Column(String, nullable=True)  # Código de pista que desbloquea
    
    # Configuración del artículo
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=-1)  # -1 = stock ilimitado
    
    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relaciones
    purchases = relationship("UserPurchase", back_populates="item")
    inventory_entries = relationship("UserInventory", back_populates="item")


class UserPurchase(Base):
    """Registro de compras realizadas por usuarios."""
    __tablename__ = "user_purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("shop_items.id"), nullable=False)
    price_paid = Column(Integer, nullable=False)  # Precio pagado en el momento de compra
    quantity = Column(Integer, default=1)
    
    # Metadatos de compra
    purchased_at = Column(DateTime, default=func.now())
    
    # Relaciones
    item = relationship("ShopItem", back_populates="purchases")
    
    # Constraint para prevenir compras duplicadas del mismo artículo
    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uix_user_item_purchase"),
    )


class UserInventory(Base):
    """Inventario personal de cada usuario."""
    __tablename__ = "user_inventory"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("shop_items.id"), primary_key=True)
    quantity = Column(Integer, default=1)
    acquired_at = Column(DateTime, default=func.now())
    
    # Metadatos del artículo en inventario
    is_used = Column(Boolean, default=False)  # Para artículos consumibles
    last_used_at = Column(DateTime, nullable=True)
    
    # Relaciones
    item = relationship("ShopItem", back_populates="inventory_entries")


class ShopCategory(Base):
    """Categorías de artículos para organización."""
    __tablename__ = "shop_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    emoji = Column(String, nullable=True)  # Emoji para mostrar en UI
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())


class ShopDiscount(Base):
    """Descuentos especiales para usuarios VIP o eventos."""
    __tablename__ = "shop_discounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    discount_percentage = Column(Float, nullable=False)  # 0.1 = 10% descuento
    
    # Condiciones de aplicación
    applies_to_vip_only = Column(Boolean, default=False)
    applies_to_category = Column(String, nullable=True)
    applies_to_item_id = Column(Integer, ForeignKey("shop_items.id"), nullable=True)
    
    # Vigencia
    starts_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())