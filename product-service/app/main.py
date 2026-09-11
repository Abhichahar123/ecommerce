from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routes import products

app = FastAPI(title="Product Service")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("✓ Product tables created successfully")


@app.get("/")
def read_root():
    return {"message": "Product service is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "product"}


app.include_router(products.router)