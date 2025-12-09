// Code/static/js/gestion_outils.js

// Références DOM
const toolsContainer = document.getElementById("toolsContainer");
const toast = document.getElementById("toast");

// Modale édition
const editModal = document.getElementById("editModal");
const editModalTitle = document.getElementById("editModalTitle");
const editLabel = document.getElementById("editLabel");
const editInput = document.getElementById("editInput");
const saveEditBtn = document.getElementById("saveEditBtn");
const cancelEditBtn = document.getElementById("cancelEditBtn");

// Modale suppression
const deleteModal = document.getElementById("deleteModal");
const deleteModalTitle = document.getElementById("deleteModalTitle");
const deleteModalUsages = document.getElementById("deleteModalUsages");
const replacementSelect = document.getElementById("replacementSelect");
const confirmReplaceBtn = document.getElementById("confirmReplaceBtn");
const forceDeleteBtn = document.getElementById("forceDeleteBtn");
const closeDeleteModal = document.getElementById("closeDeleteModal");

// Modale usages
const usageModal = document.getElementById("usageModal");
const usageModalTitle = document.getElementById("usageModalTitle");
const usageModalBody = document.getElementById("usageModalBody");
const closeUsageModal = document.getElementById("closeUsageModal");

// Création
const createToolBtn = document.getElementById("createToolBtn");
const newToolName = document.getElementById("newToolName");
const newToolDesc = document.getElementById("newToolDesc");

let toolsCache = [];
let toolToDelete = null;

// Contexte d’édition
let editContext = { toolId: null, field: null };

document.addEventListener("DOMContentLoaded", () => {
  loadTools();

  // Création
  createToolBtn.addEventListener("click", createTool);

  // Suppression
  closeDeleteModal.addEventListener("click", () => toggleModal(deleteModal, false));
  confirmReplaceBtn.addEventListener("click", doReplaceInDeleteFlow);
  forceDeleteBtn.addEventListener("click", doForceDelete);

  // Usages
  closeUsageModal.addEventListener("click", () => toggleModal(usageModal, false));

  // Édition
  cancelEditBtn.addEventListener("click", () => toggleModal(editModal, false));
  saveEditBtn.addEventListener("click", saveEdit);

  // Échappement (Esc) pour toutes modales
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      [editModal, deleteModal, usageModal].forEach(m => m.classList.contains("hidden") ? null : toggleModal(m, false));
    }
  });
});

function showToast(msg, type = "ok") {
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  setTimeout(() => (toast.className = "toast"), 2200);
}

async function loadTools() {
  toolsContainer.innerHTML = `<tr><td class="loading-row" colspan="5">Chargement…</td></tr>`;
  try {
    const res = await fetch("/gestion_outils/api/tools");
    if (!res.ok) throw new Error();
    toolsCache = await res.json();
    renderTools();
  } catch {
    toolsContainer.innerHTML = `<tr><td class="error-row" colspan="5">Impossible de charger la liste des outils.</td></tr>`;
  }
}

function renderTools() {
  if (!toolsCache.length) {
    toolsContainer.innerHTML = `<tr><td class="empty-row" colspan="5">Aucun outil pour le moment.</td></tr>`;
    return;
  }

  const allOptions = toolsCache
    .map((t) => `<option value="${t.id}">${escapeHTML(t.name)}</option>`)
    .join("");

  toolsContainer.innerHTML = "";
  toolsCache.forEach((tool) => {
    const tr = document.createElement("tr");
    tr.dataset.id = tool.id;

    // Col 1 — Outil (bouton édition ouvre modale)
    const tdName = document.createElement("td");
    tdName.innerHTML = `
      <div class="cell-display">
        <span class="cell-text" title="${escapeHTML(tool.name)}">${escapeHTML(tool.name)}</span>
        <button class="icon-btn" data-edit="name" title="Modifier">
          <i class="app-icon-edit activities-edit-icon icon-edit" aria-hidden="true"></i>
        </button>
      </div>
    `;

    // Col 2 — Description (bouton édition ouvre modale)
    const tdDesc = document.createElement("td");
    const desc = (tool.description || "").trim();
    tdDesc.className = "col-desc";
    tdDesc.innerHTML = `
      <div class="cell-display">
        <span class="cell-text ${desc ? "" : "placeholder"}" title="${escapeHTML(desc)}">${desc ? escapeHTML(desc) : "—"}</span>
        <button class="icon-btn" data-edit="description" title="Modifier">
          <i class="app-icon-edit activities-edit-icon icon-edit" aria-hidden="true"></i>
        </button>
      </div>
    `;

    // Col 3 — Usages
    const tdUsage = document.createElement("td");
    const count = tool.usages.length;
    tdUsage.innerHTML = `
      <span class="badge ${count ? "badge-blue" : "badge-gray"}">${count} usage${count > 1 ? "s" : ""}</span>
      <button class="btn btn-ghost btn-small" data-action="see-usage">Voir</button>
    `;

    // Col 4 — Remplacer
    const tdReplace = document.createElement("td");
    tdReplace.innerHTML = `
      <div class="replace-group">
        <select class="select replace-select">
          <option value="">— Sélectionner —</option>
          ${allOptions}
        </select>
        <button class="btn btn-violet btn-small" data-action="replace">Remplacer</button>
      </div>
    `;
    tdReplace.querySelector(`option[value="${tool.id}"]`)?.setAttribute("disabled", "disabled");

    // Col 5 — Supprimer
    const tdActions = document.createElement("td");
    tdActions.innerHTML = `<button class="btn btn-danger btn-small" data-action="delete">Supprimer</button>`;

    tr.append(tdName, tdDesc, tdUsage, tdReplace, tdActions);
    toolsContainer.appendChild(tr);
  });

  toolsContainer.onclick = onTableClick;
}

function onTableClick(e) {
  const btn = e.target.closest("button");
  if (!btn) return;

  const tr = btn.closest("tr");
  const id = parseInt(tr?.dataset?.id || "0", 10);
  if (!id) return;

  // Edition via icône
  if (btn.dataset.edit === "name" || btn.dataset.edit === "description") {
    const field = btn.dataset.edit;
    const tool = toolsCache.find(t => t.id === id);
    openEditModal(tool, field);
    return;
  }

  // Actions générales
  const action = btn.dataset.action;
  if (action === "replace") {
    const select = tr.querySelector(".replace-select");
    const target = parseInt(select.value || "0", 10);
    if (!target || target === id) return showToast("Choisis un autre outil de remplacement.", "warn");
    return replaceTool(id, target);
  }
  if (action === "delete") {
    const tool = toolsCache.find((t) => t.id === id);
    return openDelete(tool);
  }
  if (action === "see-usage") {
    const tool = toolsCache.find((t) => t.id === id);
    return openUsage(tool);
  }
}

/* ---------- ÉDITION (modale) ---------- */
function openEditModal(tool, field) {
  editContext = { toolId: tool.id, field };
  const isName = field === "name";
  editModalTitle.textContent = isName ? `Modifier le nom` : `Modifier la description`;
  editLabel.textContent = isName ? "Nom" : "Description";
  editInput.value = (tool[field] || "").trim();
  toggleModal(editModal, true);
  setTimeout(() => editInput.focus(), 0);
}

async function saveEdit() {
  const { toolId, field } = editContext;
  if (!toolId || !field) return toggleModal(editModal, false);
  const newVal = editInput.value.trim();
  if (field === "name" && !newVal) return showToast("Le nom ne peut pas être vide.", "warn");

  const ok = await updateTool(toolId, field, newVal);
  if (ok) {
    // Mettre à jour cache & réafficher
    const tool = toolsCache.find(t => t.id === toolId);
    if (tool) tool[field] = newVal;
    toggleModal(editModal, false);
    // Si renommage, recharger pour tri stable.
    if (field === "name") await loadTools(); else renderTools();
  }
}

async function updateTool(id, field, value) {
  try {
    const body = {}; body[field] = value;
    const res = await fetch(`/gestion_outils/api/tools/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showToast(data.error || "Échec de la mise à jour.", "error");
      return false;
    }
    showToast("Modifié.");
    return true;
  } catch {
    showToast("Erreur réseau.", "error");
    return false;
  }
}

/* ---------- CRÉATION ---------- */
async function createTool() {
  const name = newToolName.value.trim();
  const desc = newToolDesc.value.trim();
  if (!name) {
    showToast("Renseigne un nom d’outil.", "warn");
    newToolName.focus();
    return;
  }
  try {
    const res = await fetch("/gestion_outils/api/tools", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description: desc }),
    });
    const data = await res.json();
    if (!res.ok) return showToast(data.error || "Échec de création.", "error");
    newToolName.value = ""; newToolDesc.value = "";
    showToast("Outil ajouté.");
    await loadTools();
  } catch {
    showToast("Erreur réseau.", "error");
  }
}

/* ---------- REMPLACEMENT ---------- */
async function replaceTool(srcId, dstId) {
  try {
    const res = await fetch(`/gestion_outils/api/tools/${srcId}/replace`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ replacement_id: parseInt(dstId, 10) }),
    });
    const data = await res.json();
    if (!res.ok) return showToast(data.error || "Échec du remplacement.", "error");
    showToast("Remplacement effectué.");
    await loadTools();
  } catch {
    showToast("Erreur réseau.", "error");
  }
}

/* ---------- SUPPRESSION ---------- */
function openDelete(tool) {
  toolToDelete = tool;
  deleteModalTitle.textContent = `Supprimer l’outil « ${tool.name} »`;
  replacementSelect.innerHTML =
    `<option value="">— Choisir un outil —</option>` +
    toolsCache.filter(t => t.id !== tool.id).map(t => `<option value="${t.id}">${escapeHTML(t.name)}</option>`).join("");
  deleteModalUsages.innerHTML = `<div class="loading-soft">Recherche des usages…</div>`;
  toggleModal(deleteModal, true);

  fetch(`/gestion_outils/api/tools/${tool.id}/usages`)
    .then(r => r.json())
    .then(data => {
      const usages = data.usages || [];
      if (!usages.length) deleteModalUsages.innerHTML = `<div class="empty-soft">Aucun usage détecté.</div>`;
      else deleteModalUsages.innerHTML = `<ul class="usage-ul">${
        usages.map(u => `<li><strong>${escapeHTML(u.activity_name)}</strong> → ${escapeHTML(u.task_name)}</li>`).join("")
      }</ul>`;
    })
    .catch(() => deleteModalUsages.innerHTML = `<div class="error-soft">Impossible d’obtenir les usages.</div>`);
}

async function doReplaceInDeleteFlow() {
  if (!toolToDelete) return;
  const dst = replacementSelect.value;
  if (!dst) return showToast("Choisis un outil de remplacement.", "warn");
  await replaceTool(toolToDelete.id, dst);
  toggleModal(deleteModal, false);
}

async function doForceDelete() {
  if (!toolToDelete) return;
  try {
    const res = await fetch(`/gestion_outils/api/tools/${toolToDelete.id}?force_detach=true`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) return showToast(data.error || "Échec suppression.", "error");
    showToast("Outil supprimé.");
    toggleModal(deleteModal, false);
    await loadTools();
  } catch {
    showToast("Erreur réseau.", "error");
  }
}

/* ---------- USAGES ---------- */
function openUsage(tool) {
  usageModalTitle.textContent = `Usages de « ${tool.name} »`;
  usageModalBody.innerHTML = `<div class="loading-soft">Chargement…</div>`;
  toggleModal(usageModal, true);

  fetch(`/gestion_outils/api/tools/${tool.id}/usages`)
    .then(r => r.json())
    .then(data => {
      const usages = data.usages || [];
      if (!usages.length) usageModalBody.innerHTML = `<div class="empty-soft">Aucun usage.</div>`;
      else usageModalBody.innerHTML = `<ul class="usage-ul">${
        usages.map(u => `<li><strong>${escapeHTML(u.activity_name)}</strong> → ${escapeHTML(u.task_name)}</li>`).join("")
      }</ul>`;
    })
    .catch(() => usageModalBody.innerHTML = `<div class="error-soft">Erreur de chargement des usages.</div>`);
}

/* ---------- Utils ---------- */
function toggleModal(modal, show = true) {
  if (show) {
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  } else {
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }
}
function escapeHTML(s) {
  return (s ?? "").toString().replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
