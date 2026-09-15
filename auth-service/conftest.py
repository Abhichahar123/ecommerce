import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Test ke liye SQLite use karenge
# :memory: matlab RAM mein database — test khatam → sab delete
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# SQLite engine banao
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
    # check_same_thread=False → SQLite ko multiple threads allow karo
    # PostgreSQL mein yeh zaroorat nahi hoti
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def override_get_db():
    """
    Production get_db() ko replace karo test database se.
    Tests mein Neon DB nahi, local SQLite use hogi.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """
    Har test ke liye:
    1. Fresh database banao
    2. TestClient do
    3. Test khatam → database delete karo
    
    scope="function" → har test function ke liye naya setup
    Matlab ek test ka data doosre test ko affect nahi karta
    """
    # Tables banao
    Base.metadata.create_all(bind=engine)

    # Production DB ki jagah Test DB use karo
    app.dependency_overrides[get_db] = override_get_db

    # TestClient banao
    with TestClient(app) as test_client:
        yield test_client

    # Test khatam → sab tables delete karo → fresh start next test ke liye
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()