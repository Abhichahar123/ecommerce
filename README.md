# E-Commerce Microservices Backend

A production-ready microservices backend built with FastAPI, PostgreSQL, Redis, and Docker. Deployed on Render with Neon DB (cloud PostgreSQL).

## Live Demo

All services are deployed and accessible:

| Service | URL | API Docs |
|---|---|---|
| Auth Service | https://ecommerce-auth-service-z0pv.onrender.com | [Swagger](https://ecommerce-auth-service-z0pv.onrender.com/docs) |
| Product Service | https://ecommerce-product-service-w8a3.onrender.com | [Swagger](https://ecommerce-product-service-w8a3.onrender.com/docs) |
| Order Service | https://ecommerce-order-service-cd4c.onrender.com | [Swagger](https://ecommerce-order-service-cd4c.onrender.com/docs) |
| Payment Service | https://ecommerce-payment-service-1mgm.onrender.com | [Swagger](https://ecommerce-payment-service-1mgm.onrender.com/docs) |

> Note: Free tier services may take 30-50 seconds to wake up on first request.

---

## Architecture

```
Client
  │
  ├── Auth Service (Port 8001)
  │     └── PostgreSQL (Neon DB)
  │
  ├── Product Service (Port 8002)
  │     ├── PostgreSQL (Neon DB)
  │     └── Redis Cache
  │
  ├── Order Service (Port 8003)
  │     └── PostgreSQL (Neon DB)
  │
  └── Payment Service (Port 8004)
        └── PostgreSQL (Neon DB)
```

---

## Services

### Auth Service
- User signup and login
- JWT token generation and verification
- Password hashing with bcrypt
- Token expiry (30 minutes)

### Product Service
- Product CRUD operations
- Redis caching for fast product listing (5 min TTL)
- Cache invalidation on data changes
- Stock management

### Order Service
- Order placement with stock validation
- Inter-service communication (calls Auth and Product services)
- Redis distributed locking for race condition prevention
- Lock retry mechanism (3 attempts, 100ms interval)

### Payment Service
- Mock payment processing (90% success rate)
- Idempotency to prevent double charges
- Payment status tracking (pending/success/failed)
- Failure reason tracking

---

## Key Technical Concepts

| Concept | Implementation |
|---|---|
| JWT Authentication | python-jose, 30 min expiry, Bearer token |
| Password Security | bcrypt hashing — plain passwords never stored |
| Redis Caching | Cache-aside pattern, 5 min TTL, auto invalidation |
| Race Condition Prevention | Redis distributed lock (SET NX PX) with retry |
| Idempotency | Unique key per payment — no double charges |
| Inter-service Communication | HTTP calls via httpx |
| Database Isolation | Separate PostgreSQL DB per service |
| CORS | Enabled on all services for browser access |

---

## Tech Stack

| Technology | Purpose |
|---|---|
| FastAPI | Web framework |
| PostgreSQL (Neon DB) | Primary database (separate per service) |
| Redis | Caching + Distributed locking |
| SQLAlchemy | ORM |
| Docker + Docker Compose | Local development |
| Render | Cloud deployment |
| pytest | Unit testing (26 tests) |
| Locust | Load testing |

---

## API Endpoints

### Auth Service
| Method | Endpoint | Description |
|---|---|---|
| POST | /auth/signup | Register new user |
| POST | /auth/login | Login and get JWT token |
| GET | /auth/me | Get current user info (protected) |

### Product Service
| Method | Endpoint | Description |
|---|---|---|
| POST | /products/ | Create product |
| GET | /products/ | List all products (Redis cached) |
| GET | /products/{id} | Get product detail |
| PUT | /products/{id} | Update product |
| DELETE | /products/{id} | Delete product |

### Order Service
| Method | Endpoint | Description |
|---|---|---|
| POST | /orders/ | Place order (with distributed lock) |
| GET | /orders/ | List user orders (protected) |
| GET | /orders/{id} | Get order detail (protected) |

### Payment Service
| Method | Endpoint | Description |
|---|---|---|
| POST | /payments/ | Process payment (idempotent) |
| GET | /payments/ | List user payments (protected) |
| GET | /payments/{id} | Get payment detail (protected) |

---

## Load Testing Results

Tested with Locust (100 concurrent users):

| Endpoint | Median Response | Failure Rate |
|---|---|---|
| GET /products/ (cached) | 10ms | 0% |
| GET /orders/ | 50ms | 0% |
| POST /auth/login | 820ms | 0% |
| Overall | 15ms | 0% |

> Product listing achieves 10ms median response time due to Redis caching.

---

## Testing

```bash
# Auth Service — 11 tests
cd auth-service
pytest tests/ -v

# Product Service — 15 tests
cd product-service
pytest tests/ -v

# Total: 26 tests, 100% pass rate
```

---

## Getting Started (Local)

### Prerequisites
- Docker Desktop
- Python 3.11+

### Run the Project

1. Clone the repository
```bash
git clone https://github.com/Abhichahar123/ecommerce.git
cd ecommerce
```

2. Start Redis
```bash
docker-compose up -d
```

3. Setup each service
```bash
cd auth-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8001
```

Repeat for product-service (8002), order-service (8003), payment-service (8004).

4. Copy `.env.example` to `.env` in each service and fill in your credentials.

### API Documentation
Each service has auto-generated Swagger docs:
- Auth: http://localhost:8001/docs
- Product: http://localhost:8002/docs
- Order: http://localhost:8003/docs
- Payment: http://localhost:8004/docs

---

## Project Structure

```
ecommerce/
├── auth-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routes/
│   │       └── auth.py
│   ├── tests/
│   │   └── test_auth.py
│   ├── requirements.txt
│   └── .env.example
├── product-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routes/
│   │       └── products.py
│   ├── tests/
│   │   └── test_products.py
│   ├── requirements.txt
│   └── .env.example
├── order-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routes/
│   │       └── orders.py
│   ├── requirements.txt
│   └── .env.example
├── payment-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routes/
│   │       └── payments.py
│   ├── requirements.txt
│   └── .env.example
├── docker-compose.yml
├── locustfile.py
├── frontend.html
└── README.md
```

---

## Resume Highlights

- Built microservices e-commerce backend with 4 independent services communicating via HTTP
- Implemented Redis distributed locking (SET NX PX) for race condition prevention in inventory management
- Achieved 10ms median response time on product listing via Redis cache-aside pattern
- Implemented idempotent payment processing to prevent double charges using unique idempotency keys
- Load tested with 100 concurrent users — 0% failure rate, 48 req/sec throughput
- Wrote 26 unit tests (pytest) with 100% pass rate using dependency injection for test isolation
- Deployed all 4 services on Render with Neon DB (cloud PostgreSQL) — live demo available

---

## Future Improvements

- Add Kafka for async event-driven communication between services
- Implement API Gateway for single entry point
- Add Kubernetes for container orchestration
- Implement circuit breaker pattern for service resilience
- Add monitoring with Prometheus and Grafana