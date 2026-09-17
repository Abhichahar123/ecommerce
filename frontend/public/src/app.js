const state = {
  token: localStorage.getItem("ecom_token") || "",
  user: null,
  products: [],
  orders: [],
  payments: [],
  services: {},
  selectedProductId: null,
  view: "shop",
  authMode: "login",
  busy: false,
  message: null
};

const app = document.querySelector("#app");

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD"
});

function html(strings, ...values) {
  return strings.reduce((result, string, index) => {
    const value = values[index] ?? "";
    return result + string + value;
  }, "");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function endpoint(path) {
  return `/api${path}`;
}

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(endpoint(path), {
    ...options,
    headers
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof payload === "object" ? payload.detail : payload;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail || "Request failed");
  }

  return payload;
}

function setMessage(type, text) {
  state.message = { type, text };
  render();
  window.clearTimeout(setMessage.timer);
  setMessage.timer = window.setTimeout(() => {
    state.message = null;
    render();
  }, 4500);
}

async function withBusy(task, successMessage) {
  state.busy = true;
  render();
  try {
    const result = await task();
    if (successMessage) setMessage("success", successMessage);
    return result;
  } catch (error) {
    setMessage("error", error.message);
    return null;
  } finally {
    state.busy = false;
    render();
  }
}

async function loadHealth() {
  const keys = ["auth", "products", "orders", "payments"];
  const results = await Promise.allSettled(keys.map((key) => api(`/health/${key}`)));
  state.services = keys.reduce((services, key, index) => {
    services[key] = results[index].status === "fulfilled";
    return services;
  }, {});
}

async function loadProducts() {
  state.products = await api("/products/");
  if (!state.selectedProductId && state.products.length) {
    state.selectedProductId = state.products[0].id;
  }
}

async function loadAccountData() {
  if (!state.token) return;
  try {
    state.user = await api("/auth/me");
  } catch (error) {
    localStorage.removeItem("ecom_token");
    state.token = "";
    state.user = null;
    state.orders = [];
    state.payments = [];
    throw error;
  }
  const [orders, payments] = await Promise.allSettled([api("/orders/"), api("/payments/")]);
  state.orders = orders.status === "fulfilled" ? orders.value : [];
  state.payments = payments.status === "fulfilled" ? payments.value : [];
}

async function bootstrap() {
  await withBusy(async () => {
    await loadHealth();
    await Promise.all([loadProducts(), loadAccountData()]);
  });
}

function servicePill(name) {
  const online = state.services[name];
  return `<span class="service ${online ? "online" : "offline"}"><span></span>${escapeHtml(name)}</span>`;
}

function renderShell() {
  const tabs = [
    ["shop", "Shop"],
    ["manage", "Products"],
    ["orders", "Orders"],
    ["payments", "Payments"]
  ];

  return html`
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">EC</div>
        <div>
          <h1>Ecom Console</h1>
          <p>FastAPI microservices storefront</p>
        </div>
      </div>
      <nav class="tabs">
        ${tabs.map(([id, label]) => `<button class="${state.view === id ? "active" : ""}" data-view="${id}">${label}</button>`).join("")}
      </nav>
      <div class="account">
        ${state.user ? `<span>${escapeHtml(state.user.username)}</span><button class="ghost" data-action="logout">Logout</button>` : ""}
      </div>
    </header>
    <main>
      <section class="status-row">
        ${servicePill("auth")}
        ${servicePill("products")}
        ${servicePill("orders")}
        ${servicePill("payments")}
      </section>
      ${state.message ? `<div class="notice ${state.message.type}">${escapeHtml(state.message.text)}</div>` : ""}
      ${!state.user ? renderAuth() : ""}
      ${state.user ? renderCurrentView() : ""}
    </main>
  `;
}

function renderAuth() {
  const isSignup = state.authMode === "signup";
  return html`
    <section class="auth-layout">
      <div class="intro-panel">
        <p class="eyebrow">Storefront Console</p>
        <h2>Browse inventory, place orders, and run mock payments from one focused UI.</h2>
        <div class="metric-grid">
          <div><strong>${state.products.length}</strong><span>Products live</span></div>
          <div><strong>${Object.values(state.services).filter(Boolean).length}/4</strong><span>Services online</span></div>
        </div>
      </div>
      <form class="panel auth-card" data-form="${state.authMode}">
        <div class="segmented">
          <button type="button" class="${!isSignup ? "active" : ""}" data-auth-mode="login">Login</button>
          <button type="button" class="${isSignup ? "active" : ""}" data-auth-mode="signup">Signup</button>
        </div>
        ${isSignup ? `<label>Username<input name="username" autocomplete="username" required /></label>` : ""}
        <label>Email<input name="email" type="email" autocomplete="email" required /></label>
        <label>Password<input name="password" type="password" autocomplete="${isSignup ? "new-password" : "current-password"}" required /></label>
        <button class="primary" type="submit" ${state.busy ? "disabled" : ""}>${isSignup ? "Create account" : "Login"}</button>
      </form>
    </section>
  `;
}

function renderCurrentView() {
  if (state.view === "manage") return renderManageProducts();
  if (state.view === "orders") return renderOrders();
  if (state.view === "payments") return renderPayments();
  return renderShop();
}

function productCard(product) {
  return html`
    <article class="product-card">
      <div class="product-media">${escapeHtml((product.category || product.name || "P").slice(0, 2).toUpperCase())}</div>
      <div class="product-body">
        <div>
          <p class="category">${escapeHtml(product.category || "General")}</p>
          <h3>${escapeHtml(product.name)}</h3>
          <p>${escapeHtml(product.description || "No description added yet.")}</p>
        </div>
        <div class="product-meta">
          <strong>${money.format(product.price)}</strong>
          <span>${product.stock} in stock</span>
        </div>
        <form class="buy-row" data-form="order" data-product-id="${product.id}">
          <input type="number" name="quantity" min="1" max="${Math.max(product.stock, 1)}" value="1" aria-label="Quantity" />
          <button class="primary" ${product.stock < 1 || state.busy ? "disabled" : ""}>Order</button>
        </form>
      </div>
    </article>
  `;
}

function renderShop() {
  const featured = state.products.reduce((best, product) => (!best || product.price > best.price ? product : best), null);
  return html`
    <section class="dashboard">
      <div class="summary-band">
        <div>
          <p class="eyebrow">Catalog</p>
          <h2>${featured ? escapeHtml(featured.name) : "No products yet"}</h2>
          <p>${featured ? escapeHtml(featured.description || "Ready for orders.") : "Create your first product from the Products tab."}</p>
        </div>
        <div class="summary-stat">
          <strong>${state.orders.length}</strong>
          <span>Your orders</span>
        </div>
      </div>
      <div class="product-grid">
        ${state.products.length ? state.products.map(productCard).join("") : `<div class="empty">No products returned by the product service.</div>`}
      </div>
    </section>
  `;
}

function renderManageProducts() {
  return html`
    <section class="two-column">
      <form class="panel form-stack" data-form="product">
        <h2>Add product</h2>
        <label>Name<input name="name" required /></label>
        <label>Description<textarea name="description" rows="3"></textarea></label>
        <div class="field-grid">
          <label>Price<input name="price" type="number" min="0.01" step="0.01" required /></label>
          <label>Stock<input name="stock" type="number" min="0" step="1" value="0" required /></label>
        </div>
        <label>Category<input name="category" /></label>
        <button class="primary" ${state.busy ? "disabled" : ""}>Create product</button>
      </form>
      <div class="panel table-panel">
        <h2>Inventory</h2>
        <div class="table">
          ${state.products.map((product) => html`
            <div class="table-row">
              <span>${escapeHtml(product.name)}</span>
              <span>${money.format(product.price)}</span>
              <span>${product.stock} units</span>
              <button class="danger" data-action="delete-product" data-product-id="${product.id}">Delete</button>
            </div>
          `).join("") || `<div class="empty">No inventory yet.</div>`}
        </div>
      </div>
    </section>
  `;
}

function renderOrders() {
  return html`
    <section class="panel table-panel">
      <div class="panel-heading">
        <h2>Orders</h2>
        <button class="ghost" data-action="refresh">Refresh</button>
      </div>
      <div class="table">
        ${state.orders.map((order) => html`
          <div class="table-row order-row">
            <span>#${order.id}</span>
            <span>Product ${order.product_id}</span>
            <span>${order.quantity} item${order.quantity === 1 ? "" : "s"}</span>
            <strong>${money.format(order.total_price)}</strong>
            <span class="badge">${escapeHtml(order.status)}</span>
            <button class="primary small" data-action="pay-order" data-order-id="${order.id}" data-amount="${order.total_price}">Pay</button>
          </div>
        `).join("") || `<div class="empty">Orders will appear here after checkout.</div>`}
      </div>
    </section>
  `;
}

function renderPayments() {
  return html`
    <section class="panel table-panel">
      <div class="panel-heading">
        <h2>Payments</h2>
        <button class="ghost" data-action="refresh">Refresh</button>
      </div>
      <div class="table">
        ${state.payments.map((payment) => html`
          <div class="table-row">
            <span>#${payment.id}</span>
            <span>Order ${payment.order_id}</span>
            <strong>${money.format(payment.amount)}</strong>
            <span class="badge ${payment.status === "success" ? "success" : "failed"}">${escapeHtml(payment.status)}</span>
            <span>${escapeHtml(payment.failure_reason || payment.idempotency_key)}</span>
          </div>
        `).join("") || `<div class="empty">Payment attempts will appear here.</div>`}
      </div>
    </section>
  `;
}

function render() {
  app.innerHTML = renderShell();
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function submitAuth(form) {
  const data = formData(form);
  await withBusy(async () => {
    if (form.dataset.form === "signup") {
      await api("/auth/signup", {
        method: "POST",
        body: JSON.stringify(data)
      });
    }

    const token = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: data.email, password: data.password })
    });
    state.token = token.access_token;
    localStorage.setItem("ecom_token", state.token);
    await loadAccountData();
  }, form.dataset.form === "signup" ? "Account created and signed in." : "Signed in.");
}

async function submitProduct(form) {
  const data = formData(form);
  await withBusy(async () => {
    await api("/products/", {
      method: "POST",
      body: JSON.stringify({
        name: data.name,
        description: data.description || null,
        price: Number(data.price),
        stock: Number(data.stock),
        category: data.category || null
      })
    });
    await loadProducts();
    form.reset();
  }, "Product created.");
}

async function submitOrder(form) {
  const productId = Number(form.dataset.productId);
  const quantity = Number(formData(form).quantity);
  await withBusy(async () => {
    await api("/orders/", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity })
    });
    await Promise.all([loadProducts(), loadAccountData()]);
  }, "Order confirmed.");
}

async function payOrder(orderId, amount) {
  await withBusy(async () => {
    await api("/payments/", {
      method: "POST",
      body: JSON.stringify({
        order_id: Number(orderId),
        amount: Number(amount),
        idempotency_key: `order-${orderId}-${state.user.id}`
      })
    });
    await loadAccountData();
    state.view = "payments";
  }, "Payment processed.");
}

app.addEventListener("click", async (event) => {
  const target = event.target.closest("button");
  if (!target) return;

  const { action, view, authMode, productId, orderId, amount } = target.dataset;

  if (view) {
    state.view = view;
    render();
  }

  if (authMode) {
    state.authMode = authMode;
    render();
  }

  if (action === "logout") {
    localStorage.removeItem("ecom_token");
    state.token = "";
    state.user = null;
    state.orders = [];
    state.payments = [];
    render();
  }

  if (action === "refresh") {
    await withBusy(async () => {
      await Promise.all([loadHealth(), loadProducts(), loadAccountData()]);
    }, "Data refreshed.");
  }

  if (action === "delete-product") {
    await withBusy(async () => {
      await api(`/products/${productId}`, { method: "DELETE" });
      await loadProducts();
    }, "Product deleted.");
  }

  if (action === "pay-order") {
    await payOrder(orderId, amount);
  }
});

app.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;

  if (form.dataset.form === "login" || form.dataset.form === "signup") {
    await submitAuth(form);
  }

  if (form.dataset.form === "product") {
    await submitProduct(form);
  }

  if (form.dataset.form === "order") {
    await submitOrder(form);
  }
});

render();
bootstrap();
