"""
Modelos ORM para el sistema de tienda del bot.
Incluye productos y sus relaciones con la narrativa.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean
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

    # Control de stock
    stock_limit = Column(Integer, nullable=True)  # NULL = ilimitado
    max_purchases_per_user = Column(Integer, nullable=False, default=1)

    # Relaciones
    unlocks_fragment = relationship(
        "StoryFragment",
        back_populates="unlocking_products",
        foreign_keys=[unlocks_fragment_key],
        primaryjoin="foreign(ShopItem.unlocks_fragment_key) == StoryFragment.key",
        uselist=False
    )

    def __repr__(self):
        return f"<ShopItem(id={self.id}, name='{self.name}', price={self.price}, unlocks='{self.unlocks_fragment_key}')>"
