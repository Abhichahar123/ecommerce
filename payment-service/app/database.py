from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# PostgreSQL se connection
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10
)

# Session factory
# autocommit=False → manually commit karenge
# autoflush=False  → hum control karenge kab write karna hai
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class — jo bhi class isse inherit kare woh table ban jaati hai
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db        # route ko session do
    finally:
        db.close()      # kaam khatam → session band karo