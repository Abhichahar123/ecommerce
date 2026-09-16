import pytest
import fakeredis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from app.main import app
from app.database import Base, get_db

# Test database — SQLite
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_products.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def override_get_db():
    """Production PostgreSQL ki jagah SQLite use karo"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """
    Har test ke liye:
    1. Fresh SQLite database
    2. Fake Redis (real Redis nahi)
    3. TestClient
    4. Test khatam → sab clean
    """
    # Tables banao
    Base.metadata.create_all(bind=engine)

    # Production DB override
    app.dependency_overrides[get_db] = override_get_db

    # Fake Redis banao
    # fakeredis.FakeRedis() → real Redis jaisa behave karta hai
    # lekin memory mein — koi Docker nahi chahiye
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    # app.database.redis_client ko fake se replace karo
    with patch("app.routes.products.redis_client", fake_redis):
        with TestClient(app) as test_client:
            yield test_client

    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()