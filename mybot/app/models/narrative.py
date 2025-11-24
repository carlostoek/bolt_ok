"""
Modelos ORM para el sistema narrativo del bot.
Incluye fragmentos de historia y decisiones narrativas.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base


class StoryFragment(Base):
    """
    Fragmento narrativo del bot.

    Representa un nodo en el árbol de decisiones narrativas.
    Cada fragmento puede tener múltiples decisiones que llevan a otros fragmentos.
    """
    __tablename__ = 'story_fragments'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Business Key - Identificador único legible por humanos
    key = Column(String(50), unique=True, nullable=False, index=True)

    # Contenido
    text = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)

    # Requerimientos
    min_besitos = Column(Integer, nullable=False, default=0)
    required_role = Column(String(50), nullable=True)

    # Recompensas
    reward_besitos = Column(Integer, nullable=False, default=0)

    # Navegación automática
    auto_next_fragment_key = Column(String(50), nullable=True)

    # Relaciones
    # Decisiones que SALEN de este fragmento (source)
    choices = relationship(
        "NarrativeChoice",
        back_populates="source_fragment",
        foreign_keys="NarrativeChoice.source_fragment_id",
        cascade="all, delete-orphan"
    )

    # Productos que DESBLOQUEAN este fragmento
    unlocking_products = relationship(
        "ShopItem",
        back_populates="unlocks_fragment",
        foreign_keys="ShopItem.unlocks_fragment_key",
        primaryjoin="StoryFragment.key == foreign(ShopItem.unlocks_fragment_key)"
    )

    def __repr__(self):
        return f"<StoryFragment(id={self.id}, key='{self.key}', text='{self.text[:30]}...')>"


class NarrativeChoice(Base):
    """
    Decisión narrativa que conecta dos fragmentos.

    Representa una opción que el usuario puede elegir en un fragmento,
    llevándolo a otro fragmento destino.
    """
    __tablename__ = 'narrative_choices'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    source_fragment_id = Column(
        Integer,
        ForeignKey('story_fragments.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    destination_fragment_key = Column(String(50), nullable=False, index=True)

    # Contenido
    text = Column(String(255), nullable=False)

    # Requerimientos
    required_besitos = Column(Integer, nullable=False, default=0)
    required_role = Column(String(50), nullable=True)

    # Visibilidad
    is_hidden = Column(Boolean, nullable=False, default=False)

    # Relaciones
    source_fragment = relationship(
        "StoryFragment",
        back_populates="choices",
        foreign_keys=[source_fragment_id]
    )

    def __repr__(self):
        return f"<NarrativeChoice(id={self.id}, text='{self.text}', from={self.source_fragment_id}, to='{self.destination_fragment_key}')>"
