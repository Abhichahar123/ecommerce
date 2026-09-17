# Ecom Console Frontend

Dependency-free browser frontend for the FastAPI ecommerce microservices.

## Run

```powershell
cd frontend
npm.cmd run dev
```

Open `http://localhost:5173`.

The frontend proxy expects these services:

- Auth service: `http://127.0.0.1:8001`
- Product service: `http://127.0.0.1:8002`
- Order service: `http://127.0.0.1:8003`
- Payment service: `http://127.0.0.1:8004`

The browser calls `/api/...` paths on the frontend server, and `server.js` forwards them to the matching backend service. This avoids CORS changes during local development.
