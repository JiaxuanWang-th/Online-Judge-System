async function api(path, options = {}) {
  const opts = {
    credentials: "include",  /*携带cookie*/
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  };
  if (opts.body && typeof opts.body !== "string") {
    opts.body = JSON.stringify(opts.body); /*对象->json字符*/
  }
  let res;
  try {
    res = await fetch(path, opts);
  } catch {
    return { code: 0, message: "network request failed", data: null };
  }
  try {
    return await res.json();
  } catch {
    return { code: res.status, message: "invalid JSON response", data: null };
  }
}

function showAlert(el, message, type = "error") {
  if (!el) return;
  el.className = `alert ${type}`;
  el.textContent = message || "";
  el.hidden = !message;
}

function escapeHtml(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function resultBadge(result) {
  if (!result) return '<span class="badge">-</span>';
  return `<span class="badge ${escapeHtml(result)}">${escapeHtml(result)}</span>`;
}

function statusBadge(status) {
  if (!status) return "";
  return `<span class="badge ${escapeHtml(status)}">${escapeHtml(status)}</span>`;
}

async function requireLogin() {
  const me = await api("/api/auth/me");
  if (me.code !== 200) {
    window.location.href = "/";
    return null;
  }
  return me.data;
}

function fillNavUser(user) {
  const el = document.getElementById("current-user");
  if (el && user) {
    el.textContent = `${user.username} · ${user.role}`;
  }
  document.querySelectorAll("[data-role-teacher]").forEach((node) => {
    node.style.display =
      user && (user.role === "teacher" || user.role === "admin") ? "" : "none";
  });
  document.querySelectorAll("[data-role-admin]").forEach((node) => {
    node.style.display = user && user.role === "admin" ? "" : "none";
  });
}

async function logout() {
  await api("/api/auth/logout", { method: "POST", body: {} });
  window.location.href = "/";
}

function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}
