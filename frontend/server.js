const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const PORT = Number(process.env.FRONTEND_PORT || process.env.PORT || 5173);
const PUBLIC_DIR = path.join(__dirname, "public");

const services = [
  { prefix: "/api/auth", target: "http://127.0.0.1:8001", rewrite: "/auth" },
  { prefix: "/api/products", target: "http://127.0.0.1:8002", rewrite: "/products" },
  { prefix: "/api/orders", target: "http://127.0.0.1:8003", rewrite: "/orders" },
  { prefix: "/api/payments", target: "http://127.0.0.1:8004", rewrite: "/payments" },
  { prefix: "/api/health/auth", target: "http://127.0.0.1:8001", rewrite: "/health" },
  { prefix: "/api/health/products", target: "http://127.0.0.1:8002", rewrite: "/health" },
  { prefix: "/api/health/orders", target: "http://127.0.0.1:8003", rewrite: "/health" },
  { prefix: "/api/health/payments", target: "http://127.0.0.1:8004", rewrite: "/health" }
];

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon"
};

function matchService(urlPath) {
  return services.find((service) => urlPath === service.prefix || urlPath.startsWith(`${service.prefix}/`));
}

function sendJson(res, statusCode, body) {
  res.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(body));
}

function serveStatic(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const requestedPath = decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname);
  const filePath = path.normalize(path.join(PUBLIC_DIR, requestedPath));

  if (!filePath.startsWith(PUBLIC_DIR)) {
    sendJson(res, 403, { detail: "Forbidden" });
    return;
  }

  fs.readFile(filePath, (error, data) => {
    if (error) {
      fs.readFile(path.join(PUBLIC_DIR, "index.html"), (fallbackError, fallbackData) => {
        if (fallbackError) {
          sendJson(res, 404, { detail: "Not found" });
          return;
        }
        res.writeHead(200, { "Content-Type": contentTypes[".html"] });
        res.end(fallbackData);
      });
      return;
    }

    const ext = path.extname(filePath);
    res.writeHead(200, { "Content-Type": contentTypes[ext] || "application/octet-stream" });
    res.end(data);
  });
}

async function proxyRequest(req, res, service) {
  const incomingUrl = new URL(req.url, `http://${req.headers.host}`);
  const suffix = incomingUrl.pathname.slice(service.prefix.length);
  const targetUrl = new URL(`${service.rewrite}${suffix}${incomingUrl.search}`, service.target);
  const headers = { ...req.headers };
  delete headers.host;

  let body;
  if (!["GET", "HEAD"].includes(req.method || "")) {
    body = await new Promise((resolve, reject) => {
      const chunks = [];
      req.on("data", (chunk) => chunks.push(chunk));
      req.on("end", () => resolve(Buffer.concat(chunks)));
      req.on("error", reject);
    });
  }

  try {
    const upstream = await fetch(targetUrl, {
      method: req.method,
      headers,
      body
    });

    const responseHeaders = {
      "Content-Type": upstream.headers.get("content-type") || "application/json; charset=utf-8"
    };
    res.writeHead(upstream.status, responseHeaders);
    res.end(Buffer.from(await upstream.arrayBuffer()));
  } catch (error) {
    sendJson(res, 502, {
      detail: `Could not reach ${service.target}. Start the matching backend service and try again.`
    });
  }
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const service = matchService(url.pathname);

  if (service) {
    proxyRequest(req, res, service);
    return;
  }

  serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log(`Frontend running at http://localhost:${PORT}`);
});
