# models.py
from sqlalchemy import (create_engine, Column, Integer, String, Float,
                        Boolean, ForeignKey, Text) # Import Text for content
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from pydantic import BaseModel, Field, model_validator
from typing import Optional

# --- Configuración de SQLAlchemy ---
# IMPORTANTE: Reemplaza esta línea con la cadena de conexión de tu base de datos real.
DATABASE_URL = "sqlite+aiosqlite:///adventure_bot.db" 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Modelos de Base de Datos (SQLAlchemy) ---
# Ajustado para coincidir con ShopItem del bot
class ProductDB(Base):
    __tablename__ = "shop_items" # Coincide con el bot
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False) # Coincide con el bot
    description = Column(Text) # Coincide con el bot
    price = Column(Integer, nullable=False) # Coincide con el bot (Integer)
    image_file_id = Column(String(255), nullable=True) # Coincide con el bot
    unlocks_fragment_key = Column(String(50), nullable=True) # Campo clave para el bloqueo

# Ajustado para coincidir con StoryFragment del bot
class NarrativeFragmentDB(Base):
    __tablename__ = "story_fragments" # Coincide con el bot
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False) # Coincide con el bot (key)
    text = Column(Text, nullable=False) # Coincide con el bot (text)
    # is_locked no existe en StoryFragment, la lógica de bloqueo está en ShopItem
    # unlock_product_id y relationship eliminados, la relación es inversa

# --- Modelos de API (Pydantic) ---
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=3)
    description: Optional[str] = None
    price: int = Field(..., gt=0) # Ajustado a int
    image_file_id: Optional[str] = None # Ajustado a image_file_id

class NarrativeFragmentCreate(BaseModel):
    key: str = Field(..., min_length=3, description="ID legible único para el fragmento (key).") # Ajustado a key
    text: str # Ajustado a text
    
    # is_locked se infiere si se proporciona un producto de bloqueo
    # unlock_product_id eliminado, la relación es inversa
    new_product_lock: Optional[ProductCreate] = None

    @model_validator(mode='after')
    def check_product_lock_presence(self):
        # Si new_product_lock está presente, se asume que el fragmento estará bloqueado por este nuevo producto.
        # No hay un campo is_locked directo en StoryFragment.
        return self

class Product(BaseModel):
    id: int
    name: str
    price: int # Ajustado a int
    image_file_id: Optional[str] = None # Ajustado a image_file_id
    unlocks_fragment_key: Optional[str] = None # Añadido para mostrar la relación

    class Config:
        from_attributes = True

class NarrativeFragment(BaseModel):
    id: int
    key: str # Ajustado a key
    text: str # Ajustado a text
    # unlock_product eliminado, la relación es inversa
    
    class Config:
        from_attributes = True

# Línea para crear las tablas si no existieran.
# La mantenemos comentada porque nos conectaremos a una BBDD existente.
# Base.metadata.create_all(bind=engine)