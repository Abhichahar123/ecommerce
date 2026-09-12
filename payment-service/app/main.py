from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routes import payments
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Payment Service")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("✓ Payment tables created successfully")


@app.get("/")
def read_root():
    return {"message": "Payment service is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "payment"}


app.include_router(payments.router)
