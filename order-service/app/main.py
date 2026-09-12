from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routes import orders
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Order Service")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("✓ Order tables created successfully")


@app.get("/")
def read_root():
    return {"message": "Order service is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "order"}


app.include_router(orders.router)