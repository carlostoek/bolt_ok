"""
Modelos ORM para el sistema de lore del bot.
Incluye piezas de lore que pueden ser desbloqueadas por usuarios.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class LorePiece(Base):
    """
    Pieza de lore del bot.

    Representa contenido de trasfondo, historias secundarias o información
    adicional que los usuarios pueden desbloquear.
    """
    __tablename__ = 'lore_pieces'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Business Key - Identificador único legible por humanos
    lore_id = Column(String(50), unique=True, nullable=False, index=True)

    # Contenido
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)

    # Disponibilidad
    is_unlocked_by_default = Column(Boolean, nullable=False, default=False)
    required_role = Column(String(50), nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relaciones
    unlocking_products = relationship(
        "ShopItem",
        back_populates="unlocks_lore",
        foreign_keys="ShopItem.unlocks_lore_piece_id"
    )

    def __repr__(self):
        return f"<LorePiece(id={self.id}, lore_id='{self.lore_id}', title='{self.title}')>"