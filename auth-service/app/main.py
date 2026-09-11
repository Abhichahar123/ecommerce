from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routes import auth

app = FastAPI(title="Auth Service")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


@app.get("/")
def read_root():
    return {"message": "Auth service is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auth"}


# Auth routes register karo
app.include_router(auth.router)