```markdown
# E-Commerce Microservices Backend

A production-ready microservices backend built with FastAPI, PostgreSQL, and Redis.

## Architecture

```
Client
  │
  ├── Auth Service (Port 8001)
  │     └── PostgreSQL (Port 5436)
  │
  ├── Product Service (Port 8002)
  │     ├── PostgreSQL (Port 5433)
  │     └── Redis Cache (Port 6379)
  │
  ├── Order Service (Port 8003)
  │     └── PostgreSQL (Port 5434)
  │
  └── Payment Service (Port 8004)
        └── PostgreSQL (Port 5435)