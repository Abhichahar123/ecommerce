import pytest


# Test data
TEST_PRODUCT = {
    "name": "iPhone 15",
    "description": "Apple ka latest phone",
    "price": 79999.0,
    "stock": 50,
    "category": "phones"
}

TEST_PRODUCT_2 = {
    "name": "Samsung Galaxy S24",
    "description": "Samsung flagship",
    "price": 74999.0,
    "stock": 30,
    "category": "phones"
}


# ─── Helper Functions ────────────────────────────────────

def create_product(client, product_data=None):
    """Helper — product banao"""
    if product_data is None:
        product_data = TEST_PRODUCT
    return client.post("/products/", json=product_data)


# ─── Create Product Tests ────────────────────────────────

def test_create_product_success(client):
    """
    Normal product creation
    Expected: 201 Created, product info return
    """
    response = create_product(client)

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == TEST_PRODUCT["name"]
    assert data["price"] == TEST_PRODUCT["price"]
    assert data["stock"] == TEST_PRODUCT["stock"]
    assert data["category"] == TEST_PRODUCT["category"]
    assert data["is_available"] == True
    assert "id" in data
    assert "created_at" in data

    print("✓ Create product test passed")


def test_create_product_without_description(client):
    """
    Description optional hai — bina description ke bhi banana chahiye
    Expected: 201 Created
    """
    response = create_product(client, {
        "name": "Test Product",
        "price": 999.0,
        "stock": 10
        # description nahi diya
    })

    assert response.status_code == 201
    assert response.json()["description"] is None

    print("✓ Product without description test passed")


def test_create_product_invalid_price(client):
    """
    Price string diya — invalid
    Expected: 422 Unprocessable Entity
    """
    response = create_product(client, {
        "name": "Test Product",
        "price": "not-a-number",  # invalid
        "stock": 10
    })

    assert response.status_code == 422

    print("✓ Invalid price test passed")


def test_create_product_missing_name(client):
    """
    Name nahi diya — required field
    Expected: 422 Unprocessable Entity
    """
    response = create_product(client, {
        "price": 999.0,
        "stock": 10
        # name nahi diya
    })

    assert response.status_code == 422

    print("✓ Missing name test passed")


# ─── Get Products Tests ──────────────────────────────────

def test_get_products_empty(client):
    """
    Koi product nahi hai — empty list return honi chahiye
    Expected: 200 OK, empty list
    """
    response = client.get("/products/")

    assert response.status_code == 200
    assert response.json() == []

    print("✓ Get empty products test passed")


def test_get_products_success(client):
    """
    Products hain — list return honi chahiye
    Expected: 200 OK, products list
    """
    # Do products banao
    create_product(client, TEST_PRODUCT)
    create_product(client, TEST_PRODUCT_2)

    response = client.get("/products/")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == TEST_PRODUCT["name"]
    assert data[1]["name"] == TEST_PRODUCT_2["name"]

    print("✓ Get products test passed")


def test_get_products_caching(client):
    """
    Caching test — doosri request cache se aani chahiye
    Expected: dono requests same data return karein
    """
    create_product(client)

    # Pehli request — database se
    response1 = client.get("/products/")
    assert response1.status_code == 200

    # Doosri request — cache se
    response2 = client.get("/products/")
    assert response2.status_code == 200

    # Dono same data return karein
    assert response1.json() == response2.json()

    print("✓ Caching test passed")


# ─── Get Single Product Tests ────────────────────────────

def test_get_single_product_success(client):
    """
    Existing product ki detail
    Expected: 200 OK, product info
    """
    created = create_product(client).json()
    product_id = created["id"]

    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["id"] == product_id
    assert response.json()["name"] == TEST_PRODUCT["name"]

    print("✓ Get single product test passed")


def test_get_nonexistent_product(client):
    """
    Product exist nahi karta
    Expected: 404 Not Found
    """
    response = client.get("/products/99999")

    assert response.status_code == 404
    assert "Product not found" in response.json()["detail"]

    print("✓ Nonexistent product test passed")


# ─── Update Product Tests ────────────────────────────────

def test_update_product_success(client):
    """
    Product update karo
    Expected: 200 OK, updated product
    """
    created = create_product(client).json()
    product_id = created["id"]

    response = client.put(
        f"/products/{product_id}",
        json={"price": 74999.0}  # sirf price update
    )

    assert response.status_code == 200
    assert response.json()["price"] == 74999.0
    assert response.json()["name"] == TEST_PRODUCT["name"]  # name same

    print("✓ Update product test passed")


def test_update_nonexistent_product(client):
    """
    Non-existent product update karna
    Expected: 404 Not Found
    """
    response = client.put(
        "/products/99999",
        json={"price": 999.0}
    )

    assert response.status_code == 404

    print("✓ Update nonexistent product test passed")


def test_update_product_stock(client):
    """
    Stock update karo
    Expected: 200 OK, updated stock
    """
    created = create_product(client).json()
    product_id = created["id"]

    response = client.put(
        f"/products/{product_id}",
        json={"stock": 25}
    )

    assert response.status_code == 200
    assert response.json()["stock"] == 25

    print("✓ Update stock test passed")


# ─── Delete Product Tests ────────────────────────────────

def test_delete_product_success(client):
    """
    Product delete karo
    Expected: 200 OK, success message
    """
    created = create_product(client).json()
    product_id = created["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    print("✓ Delete product test passed")


def test_delete_nonexistent_product(client):
    """
    Non-existent product delete karna
    Expected: 404 Not Found
    """
    response = client.delete("/products/99999")

    assert response.status_code == 404

    print("✓ Delete nonexistent product test passed")


def test_deleted_product_not_in_list(client):
    """
    Delete ke baad product list mein nahi aana chahiye
    Expected: empty list
    """
    created = create_product(client).json()
    product_id = created["id"]

    # Delete karo
    client.delete(f"/products/{product_id}")

    # List mein check karo
    response = client.get("/products/")
    assert response.status_code == 200
    assert len(response.json()) == 0

    print("✓ Deleted product not in list test passed")