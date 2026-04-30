const API_BASE = "/api/admin";
const cacheStore = new Map();
const CACHE_TTL_MS = 30000;
const RETRY_LIMIT = 2;
const REQUEST_TIMEOUT_MS = 12000;

const resources = {
  university: {
    key: "university",
    short: "uni",
    endpoint: "/universities",
    bulkEndpoint: "/universities/bulk-delete",
    listId: "uniList",
    formId: "uniForm",
    filterId: "uniTypeFilter",
    mapForm: () => ({
      name: valueOf("uniName"),
      location: valueOf("uniLocation"),
      type: valueOf("uniType"),
      min_tuition_fees: valueOf("uniMinFees"),
      max_tuition_fees: valueOf("uniMaxFees"),
      description: valueOf("uniDesc")
    })
  },
  faculty: {
    key: "faculty",
    short: "fac",
    endpoint: "/faculties",
    bulkEndpoint: "/faculties/bulk-delete",
    listId: "facList",
    formId: "facForm",
    filterId: "facUniFilter",
    mapForm: () => ({
      uni_id: valueOf("facUniId"),
      name: valueOf("facName"),
      fees: valueOf("facFees"),
      duration: valueOf("facDuration")
    })
  },
  program: {
    key: "program",
    short: "prog",
    endpoint: "/programs",
    bulkEndpoint: "/programs/bulk-delete",
    listId: "progList",
    formId: "progForm",
    filterId: "progFacFilter",
    mapForm: () => ({
      faculty_id: valueOf("progFacId"),
      name: valueOf("progName"),
      degree: valueOf("progDegree"),
      duration_years: valueOf("progDuration"),
      min_grade_required: valueOf("progMinGrade"),
      language: valueOf("progLanguage")
    })
  }
};

const state = {
  currentTab: "university",
  editMode: { university: null, faculty: null, program: null },
  lists: { university: [], faculty: [], program: [] },
  selected: { university: new Set(), faculty: new Set(), program: new Set() },
  loadedTabs: new Set(),
  query: {
    university: { page: 1, per_page: 10, search: "", sort_by: "name", sort_dir: "asc", type: "" },
    faculty: { page: 1, per_page: 10, search: "", sort_by: "name", sort_dir: "asc", uni_id: "" },
    program: { page: 1, per_page: 10, search: "", sort_by: "name", sort_dir: "asc", faculty_id: "" }
  },
  meta: {
    university: { page: 1, per_page: 10, total: 0, pages: 1 },
    faculty: { page: 1, per_page: 10, total: 0, pages: 1 },
    program: { page: 1, per_page: 10, total: 0, pages: 1 }
  }
};

function valueOf(id) {
  const el = document.getElementById(id);
  return (el?.value || "").trim();
}

function getToken() {
  const token = localStorage.getItem("token");
  if (!token) {
    throw new Error("Please login to continue.");
  }
  return token;
}

function safeRedirectToLogin() {
  localStorage.removeItem("token");
  window.location.href = "/admin-login";
}

function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

function setSectionLoading(resourceKey, isLoading) {
  const cfg = resources[resourceKey];
  const section = document.getElementById(cfg.listId);
  if (!section) return;
  section.classList.toggle("is-loading", isLoading);
}

function toFriendlyError(error, fallback = "Something went wrong.") {
  if (!error) return fallback;
  if (error.name === "AbortError") return "Request timed out. Please try again.";
  return error.message || fallback;
}

function buildQueryString(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      query.set(key, value);
    }
  });
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

function clearRequestCache(prefix = "") {
  [...cacheStore.keys()].forEach((key) => {
    if (!prefix || key.includes(prefix)) {
      cacheStore.delete(key);
    }
  });
}

function getCached(key) {
  const value = cacheStore.get(key);
  if (!value) return null;
  if (Date.now() - value.ts > CACHE_TTL_MS) {
    cacheStore.delete(key);
    return null;
  }
  return value.payload;
}

function setCached(key, payload) {
  cacheStore.set(key, { payload, ts: Date.now() });
}

async function apiFetch(endpoint, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const url = `${API_BASE}${endpoint}`;
  const cacheKey = `${method}:${url}`;
  const isCacheable = method === "GET";

  if (isCacheable) {
    const cached = getCached(cacheKey);
    if (cached) return cached;
  }

  let attempt = 0;
  while (attempt <= RETRY_LIMIT) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${await ensureAdminToken()}`,
          ...(options.headers || {})
        },
        signal: controller.signal
      });
      clearTimeout(timeout);

      if (response.status === 401) {
        safeRedirectToLogin();
        throw new Error("Session expired. Please login again.");
      }

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.message || `Request failed with ${response.status}.`);
      }

      if (isCacheable) setCached(cacheKey, payload);
      return payload;
    } catch (error) {
      clearTimeout(timeout);
      const retryable = error.name === "AbortError" || /network/i.test(error.message);
      if (attempt < RETRY_LIMIT && retryable) {
        await new Promise((resolve) => setTimeout(resolve, 350 * (attempt + 1)));
        attempt += 1;
        continue;
      }
      throw error;
    }
  }
}

async function ensureAdminToken() {
  const existing = localStorage.getItem("token");
  if (existing) return existing;
  const response = await fetch("/admin-token", { credentials: "same-origin" });
  if (!response.ok) {
    safeRedirectToLogin();
    throw new Error("Please login to continue.");
  }
  const data = await response.json().catch(() => ({}));
  if (!data.token) {
    safeRedirectToLogin();
    throw new Error("Could not establish admin session.");
  }
  localStorage.setItem("token", data.token);
  return data.token;
}

function renderFallback(resourceKey, message) {
  const cfg = resources[resourceKey];
  const list = document.getElementById(cfg.listId);
  list.innerHTML = `<div class="error-card"><p>${message}</p><button data-action="retry" data-resource="${resourceKey}">Retry</button></div>`;
}

function renderList(resourceKey) {
  const cfg = resources[resourceKey];
  const list = document.getElementById(cfg.listId);
  const items = state.lists[resourceKey];
  const selected = state.selected[resourceKey];
  if (!items.length) {
    list.innerHTML = "<p>No records found.</p>";
    return;
  }
  list.innerHTML = items
    .map((item) => {
      const subtitle = buildSubtitle(resourceKey, item);
      return `
      <div class="list-item">
        <div class="item-header">
          <label class="selection">
            <input type="checkbox" data-action="select-item" data-resource="${resourceKey}" data-id="${item.id}" ${selected.has(item.id) ? "checked" : ""} />
            <strong>${escapeHtml(item.name || "Unnamed")}</strong>
          </label>
          <div class="actions">
            <button data-action="edit" data-resource="${resourceKey}" data-id="${item.id}">Edit</button>
            <button class="delete-btn" data-action="delete" data-resource="${resourceKey}" data-id="${item.id}">Delete</button>
          </div>
        </div>
        <small>${subtitle}</small>
      </div>`;
    })
    .join("");
}

function buildSubtitle(resourceKey, item) {
  if (resourceKey === "university") {
    return `${escapeHtml(item.location || "N/A")} (${escapeHtml(item.type || "N/A")}) | Fees: ${item.min_tuition_fees ?? "N/A"} - ${item.max_tuition_fees ?? "N/A"}`;
  }
  if (resourceKey === "faculty") {
    const uni = state.lists.university.find((u) => u.id === item.uni_id);
    return `${escapeHtml(uni?.name || "No university")} | Fees: ${item.fees ?? "N/A"} | Duration: ${escapeHtml(item.duration || "N/A")}`;
  }
  const faculty = state.lists.faculty.find((f) => f.id === item.faculty_id);
  return `${escapeHtml(faculty?.name || "No faculty")} | Degree: ${escapeHtml(item.degree || "N/A")} | Min grade: ${item.min_grade_required ?? "N/A"}`;
}

function renderPagination(resourceKey) {
  const meta = state.meta[resourceKey];
  const holder = document.getElementById(`${resources[resourceKey].short}Pagination`);
  holder.innerHTML = `
    <button data-action="page" data-resource="${resourceKey}" data-page="${Math.max(1, meta.page - 1)}" ${meta.page <= 1 ? "disabled" : ""}>Prev</button>
    <span>Page ${meta.page} / ${Math.max(meta.pages || 1, 1)} (${meta.total} total)</span>
    <button data-action="page" data-resource="${resourceKey}" data-page="${Math.min(meta.pages || 1, meta.page + 1)}" ${meta.page >= (meta.pages || 1) ? "disabled" : ""}>Next</button>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function debounce(fn, delay = 300) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

async function loadResource(resourceKey, force = false) {
  const cfg = resources[resourceKey];
  const query = state.query[resourceKey];
  const endpoint = `${cfg.endpoint}${buildQueryString(query)}`;
  try {
    setSectionLoading(resourceKey, true);
    if (force) clearRequestCache(cfg.endpoint);
    const data = await apiFetch(endpoint);
    state.lists[resourceKey] = Array.isArray(data.items) ? data.items : [];
    state.meta[resourceKey] = data.meta || state.meta[resourceKey];
    renderList(resourceKey);
    renderPagination(resourceKey);
    if (resourceKey === "university") populateUniversitySelects();
    if (resourceKey === "faculty") populateFacultySelects();
  } catch (error) {
    renderFallback(resourceKey, toFriendlyError(error, "Could not load records."));
    showToast(toFriendlyError(error), "error");
  } finally {
    setSectionLoading(resourceKey, false);
  }
}

async function handleSubmit(resourceKey) {
  const cfg = resources[resourceKey];
  const form = document.getElementById(cfg.formId);
  const payload = cfg.mapForm();
  const editingId = state.editMode[resourceKey];
  const endpoint = editingId ? `${cfg.endpoint}/${editingId}` : cfg.endpoint;
  const method = editingId ? "PUT" : "POST";
  try {
    await apiFetch(endpoint, { method, body: JSON.stringify(payload) });
    clearRequestCache(cfg.endpoint);
    showToast(`${resourceKey} ${editingId ? "updated" : "created"} successfully.`);
    state.editMode[resourceKey] = null;
    form.reset();
    resetFormButton(resourceKey);
    await loadResource(resourceKey, true);
  } catch (error) {
    showToast(toFriendlyError(error), "error");
  }
}

function resetFormButton(resourceKey) {
  const btn = document.querySelector(`#${resources[resourceKey].formId} button[type="submit"]`);
  btn.textContent = `Add ${resourceKey}`;
}

function setEditForm(resourceKey, id) {
  const item = state.lists[resourceKey].find((entry) => entry.id === id);
  if (!item) return;
  state.editMode[resourceKey] = id;
  if (resourceKey === "university") {
    document.getElementById("uniName").value = item.name || "";
    document.getElementById("uniLocation").value = item.location || "";
    document.getElementById("uniType").value = item.type || "";
    document.getElementById("uniMinFees").value = item.min_tuition_fees || "";
    document.getElementById("uniMaxFees").value = item.max_tuition_fees || "";
    document.getElementById("uniDesc").value = item.description || "";
  } else if (resourceKey === "faculty") {
    document.getElementById("facUniId").value = item.uni_id || "";
    document.getElementById("facName").value = item.name || "";
    document.getElementById("facFees").value = item.fees || "";
    document.getElementById("facDuration").value = item.duration || "";
  } else {
    document.getElementById("progFacId").value = item.faculty_id || "";
    document.getElementById("progName").value = item.name || "";
    document.getElementById("progDegree").value = item.degree || "";
    document.getElementById("progDuration").value = item.duration_years || "";
    document.getElementById("progMinGrade").value = item.min_grade_required || "";
    document.getElementById("progLanguage").value = item.language || "";
  }
  const btn = document.querySelector(`#${resources[resourceKey].formId} button[type="submit"]`);
  btn.textContent = `Update ${resourceKey}`;
}

async function deleteItem(resourceKey, id) {
  if (!window.confirm("Are you sure you want to delete this item?")) return;
  const cfg = resources[resourceKey];
  try {
    await apiFetch(`${cfg.endpoint}/${id}`, { method: "DELETE" });
    clearRequestCache(cfg.endpoint);
    state.selected[resourceKey].delete(id);
    showToast("Deleted successfully.");
    await loadResource(resourceKey, true);
  } catch (error) {
    showToast(toFriendlyError(error), "error");
  }
}

async function bulkDelete(resourceKey) {
  const ids = [...state.selected[resourceKey]];
  if (!ids.length) {
    showToast("Select one or more items first.", "error");
    return;
  }
  if (!window.confirm(`Delete ${ids.length} selected items?`)) return;
  try {
    await apiFetch(resources[resourceKey].bulkEndpoint, {
      method: "POST",
      body: JSON.stringify({ ids })
    });
    state.selected[resourceKey].clear();
    clearRequestCache(resources[resourceKey].endpoint);
    showToast("Bulk delete completed.");
    await loadResource(resourceKey, true);
  } catch (error) {
    showToast(toFriendlyError(error), "error");
  }
}

function populateUniversitySelects() {
  const options = state.lists.university.map((u) => `<option value="${u.id}">${escapeHtml(u.name)}</option>`).join("");
  const source = document.getElementById("facUniId");
  const filter = document.getElementById("facUniFilter");
  if (source) source.innerHTML = `<option value="">Select University</option>${options}`;
  if (filter) filter.innerHTML = `<option value="">All Universities</option>${options}`;
}

function populateFacultySelects() {
  const options = state.lists.faculty.map((f) => `<option value="${f.id}">${escapeHtml(f.name)}</option>`).join("");
  const source = document.getElementById("progFacId");
  const filter = document.getElementById("progFacFilter");
  if (source) source.innerHTML = `<option value="">Select Faculty</option>${options}`;
  if (filter) filter.innerHTML = `<option value="">All Faculties</option>${options}`;
}

function createControlBar(resourceKey) {
  const cfg = resources[resourceKey];
  const list = document.getElementById(cfg.listId);
  if (!list || document.getElementById(`${cfg.short}Controls`)) return;

  const sortOptions =
    resourceKey === "program"
      ? `<option value="name">Sort by name</option><option value="min_grade_required">Sort by grade</option><option value="id">Sort by id</option>`
      : `<option value="name">Sort by name</option><option value="id">Sort by id</option>`;
  const filterOptions =
    resourceKey === "university"
      ? `<option value="">All Types</option><option value="public">Public</option><option value="private">Private</option>`
      : `<option value="">All</option>`;

  const html = `
    <div id="${cfg.short}Controls" class="control-bar">
      <input type="text" id="${cfg.short}Search" placeholder="Search..." />
      <select id="${cfg.short}SortBy">
        ${sortOptions}
      </select>
      <select id="${cfg.short}SortDir">
        <option value="asc">Asc</option>
        <option value="desc">Desc</option>
      </select>
      <select id="${cfg.filterId}">${filterOptions}</select>
      <button data-action="refresh" data-resource="${resourceKey}">Refresh</button>
      <button class="delete-btn" data-action="bulk-delete" data-resource="${resourceKey}">Bulk Delete</button>
      <div id="${cfg.short}Pagination" class="pagination"></div>
    </div>
  `;
  list.insertAdjacentHTML("beforebegin", html);
}

function setupControls() {
  Object.keys(resources).forEach(createControlBar);

  const debouncedSearch = debounce((resourceKey, value) => {
    state.query[resourceKey].search = value;
    state.query[resourceKey].page = 1;
    loadResource(resourceKey, true);
  }, 350);

  document.body.addEventListener("input", (event) => {
    const target = event.target;
    Object.values(resources).forEach((cfg) => {
      if (target.id === `${cfg.short}Search`) {
        debouncedSearch(cfg.key, target.value.trim());
      }
    });
  });

  document.body.addEventListener("change", (event) => {
    const target = event.target;
    for (const cfg of Object.values(resources)) {
      if (target.id === `${cfg.short}SortBy`) state.query[cfg.key].sort_by = target.value;
      if (target.id === `${cfg.short}SortDir`) state.query[cfg.key].sort_dir = target.value;
      if (target.id === cfg.filterId) {
        if (cfg.key === "university") state.query[cfg.key].type = target.value;
        if (cfg.key === "faculty") state.query[cfg.key].uni_id = target.value;
        if (cfg.key === "program") state.query[cfg.key].faculty_id = target.value;
      }
    }

    if (["uniSortBy", "uniSortDir", "uniTypeFilter"].includes(target.id)) loadResource("university", true);
    if (["facSortBy", "facSortDir", "facUniFilter"].includes(target.id)) loadResource("faculty", true);
    if (["progSortBy", "progSortDir", "progFacFilter"].includes(target.id)) loadResource("program", true);
  });
}

function wireGlobalEvents() {
  document.body.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const action = button.dataset.action;
    const resourceKey = button.dataset.resource;
    const id = Number(button.dataset.id);

    if (action === "retry" || action === "refresh") return loadResource(resourceKey, true);
    if (action === "edit") return setEditForm(resourceKey, id);
    if (action === "delete") return deleteItem(resourceKey, id);
    if (action === "bulk-delete") return bulkDelete(resourceKey);
    if (action === "page") {
      state.query[resourceKey].page = Number(button.dataset.page) || 1;
      return loadResource(resourceKey);
    }
  });

  document.body.addEventListener("change", (event) => {
    const input = event.target;
    if (input.dataset.action !== "select-item") return;
    const resourceKey = input.dataset.resource;
    const id = Number(input.dataset.id);
    if (input.checked) state.selected[resourceKey].add(id);
    else state.selected[resourceKey].delete(id);
  });

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", async (event) => {
      const tab = event.currentTarget.dataset.tab;
      document.querySelectorAll(".tab-btn").forEach((el) => el.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((el) => el.classList.remove("active"));
      event.currentTarget.classList.add("active");
      document.getElementById(tab).classList.add("active");
      state.currentTab = tab;
      const resourceKey = tab;
      if (resourceKey === "program" && !state.loadedTabs.has("faculty")) {
        await loadResource("faculty");
        state.loadedTabs.add("faculty");
      }
      if (!state.loadedTabs.has(resourceKey)) {
        state.loadedTabs.add(resourceKey);
        await loadResource(resourceKey);
      }
    });
  });

  document.getElementById("logoutBtn")?.addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "/";
  });
}

function setupForms() {
  Object.keys(resources).forEach((key) => {
    const cfg = resources[key];
    const form = document.getElementById(cfg.formId);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      handleSubmit(key);
    });
  });
}

function injectStyles() {
  const style = document.createElement("style");
  style.textContent = `
    .toast { position: fixed; top: 20px; right: 20px; z-index: 9999; padding: 12px 16px; color: #fff; border-radius: 8px; background: #198754; }
    .toast.error { background: #dc3545; }
    .control-bar { display: grid; grid-template-columns: 1fr auto auto auto auto auto; gap: 8px; margin: 0 0 12px; align-items: center; }
    .control-bar input, .control-bar select { padding: 8px; border: 1px solid #ddd; border-radius: 6px; }
    .pagination { display: flex; gap: 8px; align-items: center; }
    .item-header { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
    .selection { display: flex; gap: 8px; align-items: center; }
    .actions { display: flex; gap: 8px; }
    .error-card { border: 1px solid #f3b5b5; background: #fff0f0; border-radius: 8px; padding: 12px; }
    .is-loading { opacity: 0.65; pointer-events: none; }
  `;
  document.head.appendChild(style);
}

function installCrashGuards() {
  window.addEventListener("error", (event) => {
    console.error("Unhandled error:", event.error || event.message);
    showToast("Unexpected error occurred. Please retry.", "error");
  });
  window.addEventListener("unhandledrejection", (event) => {
    console.error("Unhandled promise rejection:", event.reason);
    showToast("A request failed unexpectedly. Please retry.", "error");
  });
}

async function bootstrap() {
  try {
    await ensureAdminToken();
    await apiFetch("/profile");
    injectStyles();
    installCrashGuards();
    setupControls();
    setupForms();
    wireGlobalEvents();
    state.loadedTabs.add("university");
    await loadResource("university");
  } catch (error) {
    showToast(toFriendlyError(error), "error");
  }
}

document.addEventListener("DOMContentLoaded", bootstrap);

