from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from ..database import get_db, redis_client
from ..models import Product
from ..schemas import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])

# Cache kitni der tak valid rahega (seconds mein)
CACHE_EXPIRE = 300  # 5 minutes


# ─── Helper Functions ───────────────────────────────────

def get_cached_products():
    """Redis se cached products lo"""
    cached = redis_client.get("all_products")
    if cached:
        return json.loads(cached)  # string → Python list
    return None


def set_cached_products(products: list):
    """Products ko Redis mein save karo"""
    redis_client.setex(
        "all_products",      # key naam
        CACHE_EXPIRE,        # 300 seconds baad expire
        json.dumps(products) # Python list → string
    )


def invalidate_cache():
    """Cache delete karo — jab product add/update/delete ho"""
    redis_client.delete("all_products")


# ─── Endpoints ──────────────────────────────────────────

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Naya product banao"""

    new_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=product_data.stock,
        category=product_data.category
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    # Naya product aaya → purana cache invalid ho gaya
    invalidate_cache()

    return new_product


@router.get("/", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    """Sab products lo — pehle cache check karo"""

    # Step 1: Redis mein check karo
    cached = get_cached_products()
    if cached:
        print("✓ Cache se data mila")
        return cached

    # Step 2: Cache miss — database se lo
    print("✗ Cache miss — database se lo")
    products = db.query(Product).filter(Product.is_available == True).all()

    # Step 3: Result ko cache mein save karo future requests ke liye
    products_list = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "stock": p.stock,
            "category": p.category,
            "is_available": p.is_available,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat() if p.updated_at else None
        }
        for p in products
    ]
    set_cached_products(products_list)

    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Ek product ki detail lo"""

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Product update karo"""

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Sirf wahi fields update karo jo request mein aaye
    # exclude_unset=True → jo fields nahi bheje unhe ignore karo
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    # Product update hua → cache invalid karo
    invalidate_cache()

    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Product delete karo"""

    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    # Product delete hua → cache invalid karo
    invalidate_cache()

    return {"message": f"Product {product_id} deleted successfully"}