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

function renderPaginationHtml(page, pageSize, total) {
  const numPages = Math.max(1, Math.ceil((total || 0) / pageSize));
  if (!total) return "";
  const hasPrev = page > 1;
  const hasNext = page < numPages;
  const btn = (label, p, current = false) =>
    `<button type="button" class="list-pagination__link${current ? " list-pagination__current" : ""}" data-page="${p}">${label}</button>`;

  let html = '<div class="list-pagination">';
  html += btn("首页", 1);
  if (hasPrev) {
    html += btn("上一页", page - 1);
    if (page - 1 > 1) {
      html += btn(String(page - 2), page - 2);
      html += btn(String(page - 1), page - 1);
    } else {
      html += btn(String(page - 1), page - 1);
    }
  }
  html += btn(String(page), page, true);
  if (hasNext) {
    if (page + 1 < numPages) {
      html += btn(String(page + 1), page + 1);
      html += btn(String(page + 2), page + 2);
    } else {
      html += btn(String(page + 1), page + 1);
    }
    html += btn("下一页", page + 1);
  }
  html += btn("尾页", numPages);
  html += `
    <form class="list-pagination__jump">
      <input type="number" name="page" min="1" max="${numPages}" placeholder="页码" required />
      <button class="list-pagination__link" type="submit">GO</button>
    </form>`;
  html += "</div>";
  return html;
}

function wirePagination(container, onPage) {
  if (!container) return;
  container.querySelectorAll("[data-page]").forEach((a) => {
    a.onclick = (e) => {
      e.preventDefault();
      const p = Number(a.getAttribute("data-page"));
      if (p >= 1) onPage(p);
    };
  });
  const form = container.querySelector(".list-pagination__jump");
  if (form) {
    form.onsubmit = (e) => {
      e.preventDefault();
      const input = form.querySelector('input[name="page"]');
      const p = Number(input && input.value);
      if (p >= 1) onPage(p);
    };
  }
}
