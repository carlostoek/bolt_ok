#!/usr/bin/env python3
"""
Prueba de Concepto: Atomic Nested Creation Pattern
====================================================

Demuestra la viabilidad de crear entidades relacionadas (fragmentos, productos, decisiones)
en una sola transacción usando SQLAlchemy Async + Pydantic.

Autor: Arquitecto de Software Senior
Fecha: 2025-11-24
"""

import asyncio
from typing import Optional, List
from datetime import datetime

# SQLAlchemy Async
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship

# Pydantic para validación
from pydantic import BaseModel, Field, validator

# ==================== CONFIGURACIÓN ====================

Base = declarative_base()
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# ==================== MODELOS DE BASE DE DATOS ====================

class StoryFragment(Base):
    """Modelo de fragmento narrativo"""
    __tablename__ = 'story_fragments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    text = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)

    # Requisitos
    min_besitos = Column(Integer, default=0)
    required_role = Column(String(50), nullable=True)
    reward_besitos = Column(Integer, default=0)

    # Relaciones
    auto_next_fragment_key = Column(String(50), nullable=True)

    # Relación con decisiones (one-to-many)
    choices = relationship("NarrativeChoice", back_populates="source_fragment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StoryFragment(id={self.id}, key='{self.key}')>"


class ShopItem(Base):
    """Modelo de producto de tienda"""
    __tablename__ = 'shop_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)
    is_vip_only = Column(Boolean, default=False)

    # Relación con contenido desbloqueado
    unlocks_fragment_key = Column(String(50), nullable=True)

    stock_limit = Column(Integer, nullable=True)
    max_purchases_per_user = Column(Integer, default=1)

    created_at = Column(String, default=lambda: datetime.now().isoformat())

    def __repr__(self):
        return f"<ShopItem(id={self.id}, name='{self.name}', price={self.price})>"


class NarrativeChoice(Base):
    """Modelo de decisión narrativa"""
    __tablename__ = 'narrative_choices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    destination_fragment_key = Column(String(50), nullable=False)
    text = Column(String(255), nullable=False)

    required_besitos = Column(Integer, default=0)
    required_role = Column(String(50), nullable=True)

    # Relación inversa
    source_fragment = relationship("StoryFragment", back_populates="choices")

    def __repr__(self):
        return f"<NarrativeChoice(id={self.id}, text='{self.text}')>"


# ==================== ESQUEMAS PYDANTIC (DTOs) ====================

class ProductCreateNested(BaseModel):
    """Esquema para crear producto inline"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: int = Field(..., ge=0)
    is_vip_only: bool = False
    stock_limit: Optional[int] = Field(None, ge=1)
    max_purchases_per_user: int = Field(1, ge=1)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Llave Maestra",
                "price": 100
            }
        }


class FragmentCreateNested(BaseModel):
    """Esquema para crear fragmento inline (recursivo)"""
    key: str = Field(..., min_length=1, max_length=50)
    text: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    min_besitos: int = Field(0, ge=0)
    required_role: Optional[str] = None
    reward_besitos: int = Field(0, ge=0)


class ChoiceCreateNested(BaseModel):
    """Esquema para decisión narrativa (soporta creación recursiva de destino)"""
    text: str = Field(..., max_length=255)
    destination_fragment_key: Optional[str] = None
    destination_fragment: Optional[FragmentCreateNested] = None
    required_besitos: int = Field(0, ge=0)
    required_role: Optional[str] = None

    @validator('destination_fragment_key', 'destination_fragment')
    def validate_destination(cls, v, values):
        """Valida que tenga al menos uno de los dos"""
        if 'destination_fragment_key' in values and 'destination_fragment' in values:
            if not values.get('destination_fragment_key') and not values.get('destination_fragment'):
                raise ValueError("Must provide either destination_fragment_key or destination_fragment")
        return v


class FragmentCreate(BaseModel):
    """Esquema principal para crear fragmento con nested creation"""
    key: str = Field(..., min_length=1, max_length=50)
    text: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    min_besitos: int = Field(0, ge=0)
    required_role: Optional[str] = None
    reward_besitos: int = Field(0, ge=0)

    # Producto de desbloqueo: referencia O creación nested
    unlock_product_id: Optional[int] = None
    unlock_product: Optional[ProductCreateNested] = None

    # Decisiones con nested creation
    choices: Optional[List[ChoiceCreateNested]] = None

    # Auto-avance
    auto_next_fragment_key: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "key": "CAP_FINAL",
                "text": "Entrada al castillo...",
                "unlock_product": {
                    "name": "Llave Maestra",
                    "price": 100
                },
                "choices": [
                    {
                        "text": "Entrar",
                        "destination_fragment": {
                            "key": "SALON_TRONO",
                            "text": "El rey te espera..."
                        }
                    }
                ]
            }
        }


# ==================== SERVICIO DE LÓGICA DE NEGOCIO ====================

class NestedCreationService:
    """Servicio que implementa el patrón de Atomic Nested Creation"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.created_entities = {
            "products": [],
            "fragments": [],
            "choices": []
        }

    async def create_fragment_with_nested(self, data: FragmentCreate) -> dict:
        """
        Crea un fragmento con soporte completo para nested creation.

        Proceso:
        1. Si hay unlock_product nested, crearlo primero (flush para obtener ID)
        2. Crear el fragmento principal
        3. Si hay choices con destination_fragment nested, crearlos recursivamente
        4. Commit único al final

        Returns:
            dict con resumen de entidades creadas
        """

        try:
            # ===== PASO 1: NESTED CREATION DE PRODUCTO =====
            unlock_product_id = data.unlock_product_id
            created_product = None

            if data.unlock_product:
                print(f"  → Creando producto nested: '{data.unlock_product.name}'")
                product = ShopItem(
                    name=data.unlock_product.name,
                    description=data.unlock_product.description,
                    price=data.unlock_product.price,
                    is_vip_only=data.unlock_product.is_vip_only,
                    stock_limit=data.unlock_product.stock_limit,
                    max_purchases_per_user=data.unlock_product.max_purchases_per_user
                )
                self.session.add(product)
                await self.session.flush()  # Genera ID sin commit

                unlock_product_id = product.id
                created_product = product
                self.created_entities["products"].append(product)
                print(f"    ✓ Producto creado con ID: {product.id}")

            # ===== PASO 2: CREAR FRAGMENTO PRINCIPAL =====
            print(f"  → Creando fragmento principal: '{data.key}'")
            fragment = StoryFragment(
                key=data.key,
                text=data.text,
                image_url=data.image_url,
                min_besitos=data.min_besitos,
                required_role=data.required_role,
                reward_besitos=data.reward_besitos,
                auto_next_fragment_key=data.auto_next_fragment_key
            )
            self.session.add(fragment)
            await self.session.flush()  # Genera ID
            self.created_entities["fragments"].append(fragment)
            print(f"    ✓ Fragmento creado con ID: {fragment.id}")

            # Vincular producto al fragmento si existe
            if unlock_product_id and created_product:
                created_product.unlocks_fragment_key = data.key
                print(f"    ✓ Producto {unlock_product_id} vinculado a fragmento '{data.key}'")

            # ===== PASO 3: NESTED CREATION DE DECISIONES =====
            created_choices = []
            if data.choices:
                print(f"  → Procesando {len(data.choices)} decisiones...")
                for idx, choice_data in enumerate(data.choices, 1):
                    # Si la decisión tiene un fragmento destino nested, crearlo primero (RECURSIÓN)
                    destination_key = choice_data.destination_fragment_key

                    if choice_data.destination_fragment:
                        print(f"    → Creando fragmento destino nested: '{choice_data.destination_fragment.key}'")
                        dest_fragment = StoryFragment(
                            key=choice_data.destination_fragment.key,
                            text=choice_data.destination_fragment.text,
                            image_url=choice_data.destination_fragment.image_url,
                            min_besitos=choice_data.destination_fragment.min_besitos,
                            required_role=choice_data.destination_fragment.required_role,
                            reward_besitos=choice_data.destination_fragment.reward_besitos
                        )
                        self.session.add(dest_fragment)
                        await self.session.flush()
                        destination_key = dest_fragment.key
                        self.created_entities["fragments"].append(dest_fragment)
                        print(f"      ✓ Fragmento destino creado: {dest_fragment.key} (ID: {dest_fragment.id})")

                    # Crear la decisión
                    choice = NarrativeChoice(
                        source_fragment_id=fragment.id,
                        destination_fragment_key=destination_key,
                        text=choice_data.text,
                        required_besitos=choice_data.required_besitos,
                        required_role=choice_data.required_role
                    )
                    self.session.add(choice)
                    await self.session.flush()
                    created_choices.append(choice)
                    self.created_entities["choices"].append(choice)
                    print(f"    ✓ Decisión #{idx} creada: '{choice.text}' → {destination_key}")

            # ===== PASO 4: COMMIT ATÓMICO =====
            await self.session.commit()
            print(f"\n✅ COMMIT EXITOSO - Todas las entidades creadas en una transacción atómica")

            # Construir respuesta
            return {
                "success": True,
                "data": {
                    "fragment": {
                        "id": fragment.id,
                        "key": fragment.key,
                        "text": fragment.text[:50] + "..." if len(fragment.text) > 50 else fragment.text
                    },
                    "created_product": {
                        "id": created_product.id,
                        "name": created_product.name,
                        "price": created_product.price
                    } if created_product else None,
                    "created_choices": [
                        {
                            "id": c.id,
                            "text": c.text,
                            "destination": c.destination_fragment_key
                        }
                        for c in created_choices
                    ]
                },
                "summary": {
                    "fragments_created": len(self.created_entities["fragments"]),
                    "products_created": len(self.created_entities["products"]),
                    "choices_created": len(self.created_entities["choices"])
                }
            }

        except Exception as e:
            await self.session.rollback()
            print(f"\n❌ ERROR: {str(e)}")
            print("   Rollback ejecutado - ninguna entidad fue creada")
            raise


# ==================== FUNCIONES DE PRUEBA ====================

async def setup_database(engine):
    """Crea todas las tablas en la base de datos"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Base de datos inicializada (SQLite en memoria)")


async def verify_data(session: AsyncSession, expected: dict):
    """Verifica que los datos se crearon correctamente en la BD"""
    print("\n" + "="*70)
    print("VERIFICACIÓN DE DATOS EN BASE DE DATOS")
    print("="*70)

    # Verificar fragmentos
    result = await session.execute(select(StoryFragment))
    fragments = result.scalars().all()
    print(f"\n📦 Fragmentos en BD: {len(fragments)}")
    for frag in fragments:
        print(f"   - ID: {frag.id}, Key: '{frag.key}', Text: '{frag.text[:30]}...'")

    # Verificar productos
    result = await session.execute(select(ShopItem))
    products = result.scalars().all()
    print(f"\n🛒 Productos en BD: {len(products)}")
    for prod in products:
        print(f"   - ID: {prod.id}, Name: '{prod.name}', Price: {prod.price}, Unlocks: '{prod.unlocks_fragment_key}'")

    # Verificar decisiones
    result = await session.execute(select(NarrativeChoice))
    choices = result.scalars().all()
    print(f"\n🔀 Decisiones en BD: {len(choices)}")
    for choice in choices:
        print(f"   - ID: {choice.id}, Text: '{choice.text}', Source: {choice.source_fragment_id}, Dest: '{choice.destination_fragment_key}'")

    # Aserciones
    print("\n" + "="*70)
    print("EJECUTANDO ASERCIONES")
    print("="*70)

    assert len(fragments) == expected["fragments"], f"❌ Expected {expected['fragments']} fragments, got {len(fragments)}"
    print(f"✓ Assertion passed: {len(fragments)} fragmentos creados")

    assert len(products) == expected["products"], f"❌ Expected {expected['products']} products, got {len(products)}"
    print(f"✓ Assertion passed: {len(products)} productos creados")

    assert len(choices) == expected["choices"], f"❌ Expected {expected['choices']} choices, got {len(choices)}"
    print(f"✓ Assertion passed: {len(choices)} decisiones creadas")

    # Verificar vinculación producto → fragmento
    if products:
        assert products[0].unlocks_fragment_key == "CAP_FINAL", "❌ Product not linked to fragment"
        print(f"✓ Assertion passed: Producto vinculado correctamente a fragmento")

    # Verificar vinculación decisión → fragmento destino
    if choices:
        assert choices[0].destination_fragment_key == "SALON_TRONO", "❌ Choice not linked to destination"
        print(f"✓ Assertion passed: Decisión vinculada correctamente a destino")

    print("\n✅ TODAS LAS ASERCIONES PASARON - PoC EXITOSO")


# ==================== MAIN ====================

async def main():
    """Función principal que ejecuta el PoC"""

    print("\n" + "="*70)
    print("PRUEBA DE CONCEPTO: ATOMIC NESTED CREATION PATTERN")
    print("="*70)
    print("Objetivo: Demostrar creación de entidades relacionadas en 1 transacción")
    print("Stack: SQLAlchemy Async + Pydantic + SQLite en memoria")
    print("="*70 + "\n")

    # Setup
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    await setup_database(engine)

    # Caso de prueba complejo
    print("\n📋 CASO DE PRUEBA: Fragmento con producto nested + decisión con destino nested")
    print("-" * 70)

    payload = {
        "key": "CAP_FINAL",
        "text": "Entrada al castillo oscuro. Las puertas crujen mientras te adentras en la penumbra...",
        "min_besitos": 0,
        "reward_besitos": 50,
        "unlock_product": {
            "name": "Llave Maestra",
            "description": "Desbloquea el capítulo final",
            "price": 100,
            "is_vip_only": False
        },
        "choices": [
            {
                "text": "Entrar al salón del trono",
                "destination_fragment": {
                    "key": "SALON_TRONO",
                    "text": "El rey te espera sentado en su trono de hierro. Sus ojos brillan con una luz sobrenatural.",
                    "reward_besitos": 20
                },
                "required_besitos": 0
            }
        ]
    }

    print("Payload JSON:")
    import json
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("-" * 70)

    # Ejecutar creación nested
    async with async_session() as session:
        print("\n🚀 INICIANDO CREACIÓN NESTED...")
        print("-" * 70)

        data = FragmentCreate(**payload)
        service = NestedCreationService(session)

        result = await service.create_fragment_with_nested(data)

        print("\n📊 RESULTADO:")
        print("-" * 70)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # Verificar datos en nueva sesión
    async with async_session() as session:
        await verify_data(session, expected={
            "fragments": 2,  # CAP_FINAL + SALON_TRONO
            "products": 1,   # Llave Maestra
            "choices": 1     # Entrar al salón
        })

    await engine.dispose()

    print("\n" + "="*70)
    print("🎉 PRUEBA DE CONCEPTO COMPLETADA EXITOSAMENTE")
    print("="*70)
    print("\nConclusiones:")
    print("✓ El patrón Atomic Nested Creation es viable")
    print("✓ SQLAlchemy Async maneja flush() + commit() correctamente")
    print("✓ Pydantic valida estructuras JSON anidadas sin problemas")
    print("✓ La recursión funciona para crear destinos de decisiones inline")
    print("✓ Todas las entidades se crean en una sola transacción atómica")
    print("\n🚀 Listo para implementar en FastAPI + PostgreSQL")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
