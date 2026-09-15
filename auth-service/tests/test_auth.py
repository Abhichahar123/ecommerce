import pytest


# Test data — har jagah same user use karenge
TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "mypassword123"
}


# ─── Helper Function ─────────────────────────────────────

def signup_user(client, user_data=None):
    """Helper — user signup karo, baar baar code repeat na karo"""
    if user_data is None:
        user_data = TEST_USER
    return client.post("/auth/signup", json=user_data)


def login_user(client, email=None, password=None):
    """Helper — user login karo"""
    return client.post("/auth/login", json={
        "email": email or TEST_USER["email"],
        "password": password or TEST_USER["password"]
    })


# ─── Signup Tests ────────────────────────────────────────

def test_signup_success(client):
    """
    Normal signup — sab sahi data ke saath
    Expected: 201 Created, user info return
    """
    response = signup_user(client)

    # Status code check karo
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    data = response.json()

    # Response mein sahi fields hain?
    assert data["email"] == TEST_USER["email"]
    assert data["username"] == TEST_USER["username"]
    assert data["is_active"] == True
    assert "id" in data          # id generate hua?
    assert "created_at" in data  # timestamp set hua?

    # Password response mein nahi hona chahiye — security!
    assert "password" not in data
    assert "hashed_password" not in data

    print("✓ Signup test passed")


def test_signup_duplicate_email(client):
    """
    Same email se dobara signup — nahi hona chahiye
    Expected: 400 Bad Request
    """
    # Pehle ek baar signup karo
    signup_user(client)

    # Same email se dobara signup karo
    response = signup_user(client)

    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

    print("✓ Duplicate email test passed")


def test_signup_duplicate_username(client):
    """
    Same username se dobara signup — nahi hona chahiye
    Expected: 400 Bad Request
    """
    # Pehle signup
    signup_user(client)

    # Same username, alag email
    response = signup_user(client, {
        "email": "different@example.com",
        "username": "testuser",  # same username
        "password": "password123"
    })

    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]

    print("✓ Duplicate username test passed")


def test_signup_invalid_email(client):
    """
    Invalid email format — reject hona chahiye
    Expected: 422 Unprocessable Entity (Pydantic validation)
    """
    response = signup_user(client, {
        "email": "not-an-email",  # invalid format
        "username": "testuser",
        "password": "password123"
    })

    assert response.status_code == 422

    print("✓ Invalid email test passed")


# ─── Login Tests ─────────────────────────────────────────

def test_login_success(client):
    """
    Sahi credentials se login
    Expected: 200 OK, access_token return
    """
    # Pehle signup karo
    signup_user(client)

    # Login karo
    response = login_user(client)

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0  # token empty nahi hona chahiye

    print("✓ Login success test passed")


def test_login_wrong_password(client):
    """
    Galat password se login — fail hona chahiye
    Expected: 401 Unauthorized
    """
    signup_user(client)

    response = login_user(client, password="wrongpassword")

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

    print("✓ Wrong password test passed")


def test_login_wrong_email(client):
    """
    Galat email se login — fail hona chahiye
    Expected: 401 Unauthorized
    """
    signup_user(client)

    response = login_user(client, email="wrong@example.com")

    assert response.status_code == 401

    print("✓ Wrong email test passed")


def test_login_nonexistent_user(client):
    """
    User exist hi nahi karta — login fail hona chahiye
    Expected: 401 Unauthorized
    """
    # Signup nahi kiya
    response = login_user(client)

    assert response.status_code == 401

    print("✓ Nonexistent user test passed")


# ─── /me Tests ───────────────────────────────────────────

def test_get_me_success(client):
    """
    Valid token se /me call karo
    Expected: 200 OK, user info
    """
    # Signup + Login
    signup_user(client)
    login_response = login_user(client)
    token = login_response.json()["access_token"]

    # /me call karo token ke saath
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["username"] == TEST_USER["username"]
    assert "password" not in data

    print("✓ Get me test passed")


def test_get_me_no_token(client):
    """
    Bina token ke /me call karo
    Expected: 401 Unauthorized
    """
    response = client.get("/auth/me")

    assert response.status_code == 401

    print("✓ No token test passed")


def test_get_me_invalid_token(client):
    """
    Galat token se /me call karo
    Expected: 401 Unauthorized
    """
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401

    print("✓ Invalid token test passed")