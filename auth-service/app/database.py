from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# .env file se variables load karo
load_dotenv()

# DATABASE_URL environment se read karo
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine = Python aur PostgreSQL ke beech actual connection
# Socho isko ek phone line ki tarah
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # har request se pehle connection check karo
    pool_recycle=300,        # 5 minute baad connection refresh karo
    pool_size=5,             # max 5 connections pool mein
    max_overflow=10          # extra 10 connections allowed
)

# SessionLocal = ek factory jo database sessions banati hai
# Har API request ko apna alag session milta hai
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = parent class jo sabhi database models inherit karenge
# SQLAlchemy isko use karta hai tables identify karne ke liye
Base = declarative_base()


# Dependency function — routes use karenge DB session lene ke liye
def get_db():
    db = SessionLocal()
    try:
        yield db      # route ko session do
    finally:
        db.close()    # request khatam hone par session band karo