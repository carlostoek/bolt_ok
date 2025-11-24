"""
Modelos ORM para el sistema de usuarios del bot.
Incluye gestión de usuarios, roles, VIP y puntos.
"""
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
import enum


class UserRole(str, enum.Enum):
    """Roles de usuario disponibles en el sistema."""
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    """
    Usuario del sistema.

    Representa un usuario de Telegram con su información, roles, puntos y estado VIP.
    """
    __tablename__ = 'users'

    # Primary Key - Telegram User ID
    id = Column(BigInteger, primary_key=True)

    # Información de Telegram
    username = Column(String(255), nullable=True, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    # Estado y roles
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER, index=True)
    is_banned = Column(Boolean, nullable=False, default=False)
    is_vip = Column(Boolean, nullable=False, default=False)
    vip_expires_at = Column(DateTime, nullable=True)

    # Puntos y progreso
    points = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)

    # Metadata
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime, nullable=True)

    # Relaciones
    narrative_state = relationship(
        "UserNarrativeState",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    inventory_items = relationship(
        "InventoryItem",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}', points={self.points})>"


class UserNarrativeState(Base):
    """
    Estado narrativo de un usuario.

    Almacena el progreso narrativo de cada usuario, incluyendo fragmentos visitados
    y fragmentos desbloqueados.
    """
    __tablename__ = 'user_narrative_states'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    user_id = Column(
        BigInteger,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )

    # Progreso narrativo
    current_fragment_key = Column(String(50), nullable=True, index=True)
    fragments_viewed = Column(Integer, nullable=False, default=0)
    choices_made = Column(Integer, nullable=False, default=0)

    # Fragmentos desbloqueados (JSON array)
    unlocked_fragments = Column(JSON, nullable=False, default=[])

    # Metadata
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relaciones
    user = relationship(
        "User",
        back_populates="narrative_state"
    )

    def __repr__(self):
        return f"<UserNarrativeState(user_id={self.user_id}, current='{self.current_fragment_key}', viewed={self.fragments_viewed})>"


class InventoryItem(Base):
    """
    Ítem en el inventario de un usuario.

    Representa productos que el usuario ha adquirido y puede usar.
    """
    __tablename__ = 'inventory_items'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id = Column(
        BigInteger,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = Column(
        Integer,
        ForeignKey('shop_items.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Información del ítem
    quantity = Column(Integer, nullable=False, default=1)
    acquired_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relaciones
    user = relationship(
        "User",
        back_populates="inventory_items"
    )
    product = relationship(
        "ShopItem",
        backref="inventory_owners"
    )

    def __repr__(self):
        return f"<InventoryItem(user_id={self.user_id}, product_id={self.product_id}, quantity={self.quantity})>"