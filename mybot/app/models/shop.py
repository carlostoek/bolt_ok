"""
Modelos ORM para el sistema de tienda del bot.
Incluye productos y sus relaciones con la narrativa.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base


class ShopItem(Base):
    """
    Producto disponible en la tienda del bot.

    Los productos pueden desbloquear fragmentos narrativos cuando son comprados.
    """
    __tablename__ = 'shop_items'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Información básica
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Precio y disponibilidad
    price = Column(Integer, nullable=False)
    is_vip_only = Column(Boolean, nullable=False, default=False)

    # Relación con narrativa
    unlocks_fragment_key = Column(String(50), nullable=True, index=True)
    unlocks_lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=True)

    # Imagen del producto
    image_file_id = Column(String(255), nullable=True)

    # Control de stock
    stock_limit = Column(Integer, nullable=True)  # NULL = ilimitado
    max_purchases_per_user = Column(Integer, nullable=False, default=1)

    # Disponibilidad temporal
    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)

    # Requisitos de desbloqueo
    unlock_requirements = Column(JSON, nullable=True)

    # Estado
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")

    # Relaciones
    unlocks_fragment = relationship(
        "StoryFragment",
        back_populates="unlocking_products",
        foreign_keys=[unlocks_fragment_key],
        primaryjoin="foreign(ShopItem.unlocks_fragment_key) == StoryFragment.key",
        uselist=False
    )
    
    unlocks_lore = relationship(
        "LorePiece",
        back_populates="unlocking_products",
        foreign_keys=[unlocks_lore_piece_id]
    )

    def __repr__(self):
        return f"<ShopItem(id={self.id}, name='{self.name}', price={self.price}, unlocks='{self.unlocks_fragment_key}')>"