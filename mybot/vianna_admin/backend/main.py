from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

import models as m

app = FastAPI(title="ViannaBot Admin API")

# Dependencia para obtener la sesión de la BBDD
def get_db():
    db = m.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/narrative_fragments", response_model=m.NarrativeFragment, status_code=201)
def create_narrative_fragment(
    fragment_data: m.NarrativeFragmentCreate, 
    db: Session = Depends(get_db)
):
    """
    Crea un fragmento narrativo. Si se incluye 'new_product_lock',
    crea el producto y lo vincula al fragmento en una única transacción atómica.
    """
    # Validar que la 'key' del fragmento sea única
    if db.query(m.NarrativeFragmentDB).filter(m.NarrativeFragmentDB.key == fragment_data.key).first():
        raise HTTPException(status_code=400, detail=f"La key '{fragment_data.key}' ya existe para otro fragmento.")

    try:
        # --- INICIO DE LA LÓGICA TRANSACCIONAL ---
        
        # 1. Crear el fragmento narrativo (StoryFragment)
        new_fragment_db = m.NarrativeFragmentDB(
            key=fragment_data.key,
            text=fragment_data.text,
        )
        db.add(new_fragment_db)
        db.flush() # Para obtener el ID y la key del fragmento antes del commit

        # 2. Si se pasa un objeto para crear un nuevo producto (ShopItem)
        if fragment_data.new_product_lock:
            print("Detectado 'new_product_lock', creando producto vinculado...")
            new_product_db = m.ProductDB(
                name=fragment_data.new_product_lock.name,
                description=fragment_data.new_product_lock.description,
                price=fragment_data.new_product_lock.price,
                image_file_id=fragment_data.new_product_lock.image_file_id,
                unlocks_fragment_key=new_fragment_db.key # Vinculamos el producto al fragmento
            )
            db.add(new_product_db)
            print(f"Producto '{new_product_db.name}' creado y vinculado a fragmento '{new_fragment_db.key}'")

        db.commit() # Si todo fue bien, se confirman los cambios (fragmento y producto si aplica)
        db.refresh(new_fragment_db)
        
        print("Transacción completada. Fragmento y producto (si aplica) guardados.")
        return new_fragment_db

    except Exception as e:
        print(f"ERROR: Ocurrió un error, revirtiendo la transacción. Detalle: {e}")
        db.rollback() # Si algo falla, se deshace todo
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")

@app.get("/products", response_model=List[m.Product])
def get_products(search: Optional[str] = None, db: Session = Depends(get_db)):
    """Obtiene una lista de productos (ShopItems), con opción de búsqueda por nombre."""
    query = db.query(m.ProductDB)
    if search:
        query = query.filter(m.ProductDB.name.ilike(f"%{search}%"))
    return query.limit(100).all()

@app.get("/")
def read_root():
    return {"status": "ViannaBot Admin API is running!"}