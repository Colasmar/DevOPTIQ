/* ============================================================
   CARTOGRAPHIE DES ACTIVITÉS - JavaScript
   Gestion des entités + Pan/Zoom + Navigation
============================================================ */

// Données injectées par Flask
const SHAPE_ACTIVITY_MAP = window.CARTO_SHAPE_MAP || {};
const SVG_EXISTS = window.SVG_EXISTS || false;
let ACTIVE_ENTITY = window.ACTIVE_ENTITY || null;
let ALL_ENTITIES = window.ALL_ENTITIES || [];

// Namespace Visio
const VISIO_NS = "http://schemas.microsoft.com/visio/2003/SVGExtensions/";

// État global Pan/Zoom
let svgRoot = null;
let currentScale = 0.5;
let panX = 0;
let panY = 0;
let isPanning = false;
let startX = 0;
let startY = 0;
let isOverActivity = false;
let svgWidth = 0;
let svgHeight = 0;

// État du gestionnaire d'entités
let selectedEntityId = null;

/* ============================================================
   GESTIONNAIRE D'ENTITÉS
============================================================ */

function openEntityManager() {
  document.getElementById("entity-manager-popup").classList.remove("hidden");
  loadEntitiesList();
}

function closeEntityManager() {
  document.getElementById("entity-manager-popup").classList.add("hidden");
}

async function loadEntitiesList() {
  const container = document.getElementById("entities-list");
  container.innerHTML = '<div class="entities-loading">Chargement...</div>';

  try {
    const res = await fetch("/activities/api/entities");
    const data = await res.json();
    ALL_ENTITIES = data.entities;

    if (ALL_ENTITIES.length === 0) {
      container.innerHTML = `
        <div class="no-entities">
          <p>Aucune entité créée.</p>
          <p class="hint">Créez votre première organisation ci-dessus.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = ALL_ENTITIES.map(e => `
      <div class="entity-card ${e.is_active ? 'active' : ''} ${selectedEntityId === e.id ? 'selected' : ''}" 
           data-id="${e.id}">
        <div class="entity-card-header">
          <span class="entity-icon">${e.is_active ? '✅' : '🏢'}</span>
          <span class="entity-name">${escapeHtml(e.name)}</span>
          ${e.is_active ? '<span class="active-tag">Active</span>' : ''}
        </div>
        <div class="entity-card-meta">
          <span class="meta-item">${e.activities_count} activités</span>
          <span class="meta-item">${e.has_svg ? '📄 SVG' : '❌ Pas de SVG'}</span>
        </div>
      </div>
    `).join('');

    container.querySelectorAll(".entity-card").forEach(card => {
      card.addEventListener("click", () => {
        selectEntity(parseInt(card.dataset.id));
      });
    });

  } catch (err) {
    console.error("Erreur chargement entités:", err);
    container.innerHTML = '<div class="error-message">Erreur de chargement</div>';
  }
}

function selectEntity(entityId) {
  selectedEntityId = entityId;
  const entity = ALL_ENTITIES.find(e => e.id === entityId);

  if (!entity) return;

  document.querySelectorAll(".entity-card").forEach(card => {
    card.classList.toggle("selected", parseInt(card.dataset.id) === entityId);
  });

  const detailsSection = document.getElementById("entity-details");
  detailsSection.classList.remove("hidden");

  document.getElementById("selected-entity-name").textContent = entity.name;
  document.getElementById("stat-activities").textContent = entity.activities_count;
  document.getElementById("stat-svg").textContent = entity.has_svg ? "✅ Présent" : "❌ Absent";
  document.getElementById("stat-updated").textContent = entity.updated_at 
    ? new Date(entity.updated_at).toLocaleDateString('fr-FR')
    : "—";

  const activateBtn = document.getElementById("activate-entity-btn");
  if (entity.is_active) {
    activateBtn.textContent = "✅ Entité active";
    activateBtn.disabled = true;
    activateBtn.classList.add("btn-disabled");
  } else {
    activateBtn.textContent = "✅ Activer cette entité";
    activateBtn.disabled = false;
    activateBtn.classList.remove("btn-disabled");
  }
}

async function createEntity() {
  const nameInput = document.getElementById("new-entity-name");
  const descInput = document.getElementById("new-entity-description");
  const statusDiv = document.getElementById("create-entity-status");

  const name = nameInput.value.trim();
  if (!name) {
    showStatus(statusDiv, "error", "Veuillez entrer un nom");
    return;
  }

  showStatus(statusDiv, "loading", "Création en cours...");

  try {
    const res = await fetch("/activities/api/entities", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        description: descInput.value.trim()
      })
    });

    const data = await res.json();

    if (!res.ok) {
      showStatus(statusDiv, "error", data.error || "Erreur lors de la création");
      return;
    }

    showStatus(statusDiv, "success", `Entité "${name}" créée avec succès !`);
    nameInput.value = "";
    descInput.value = "";

    await loadEntitiesList();
    selectEntity(data.entity.id);

  } catch (err) {
    console.error("Erreur création:", err);
    showStatus(statusDiv, "error", "Erreur de connexion");
  }
}

async function activateEntity() {
  if (!selectedEntityId) return;

  try {
    const res = await fetch(`/activities/api/entities/${selectedEntityId}/activate`, {
      method: "POST"
    });

    if (res.ok) {
      window.location.reload();
    } else {
      const data = await res.json();
      alert(data.error || "Erreur lors de l'activation");
    }
  } catch (err) {
    console.error("Erreur activation:", err);
    alert("Erreur de connexion");
  }
}

function showDeleteModal() {
  if (!selectedEntityId) return;

  const entity = ALL_ENTITIES.find(e => e.id === selectedEntityId);
  if (!entity) return;

  document.getElementById("delete-entity-name").textContent = entity.name;
  document.getElementById("delete-confirm-modal").classList.remove("hidden");
}

async function confirmDeleteEntity() {
  if (!selectedEntityId) return;

  try {
    const res = await fetch(`/activities/api/entities/${selectedEntityId}`, {
      method: "DELETE"
    });

    if (res.ok) {
      document.getElementById("delete-confirm-modal").classList.add("hidden");
      
      const entity = ALL_ENTITIES.find(e => e.id === selectedEntityId);
      if (entity && entity.is_active) {
        window.location.reload();
      } else {
        selectedEntityId = null;
        document.getElementById("entity-details").classList.add("hidden");
        await loadEntitiesList();
      }
    } else {
      const data = await res.json();
      alert(data.error || "Erreur lors de la suppression");
    }
  } catch (err) {
    console.error("Erreur suppression:", err);
    alert("Erreur de connexion");
  }
}

function showRenameModal() {
  if (!selectedEntityId) return;

  const entity = ALL_ENTITIES.find(e => e.id === selectedEntityId);
  if (!entity) return;

  document.getElementById("rename-entity-input").value = entity.name;
  document.getElementById("rename-modal").classList.remove("hidden");
}

async function confirmRenameEntity() {
  if (!selectedEntityId) return;

  const newName = document.getElementById("rename-entity-input").value.trim();
  if (!newName) {
    alert("Veuillez entrer un nom");
    return;
  }

  try {
    const res = await fetch(`/activities/api/entities/${selectedEntityId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName })
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Erreur lors du renommage");
      return;
    }

    document.getElementById("rename-modal").classList.add("hidden");

    const entity = ALL_ENTITIES.find(e => e.id === selectedEntityId);
    if (entity && entity.is_active) {
      window.location.reload();
    } else {
      await loadEntitiesList();
      selectEntity(selectedEntityId);
    }
  } catch (err) {
    console.error("Erreur renommage:", err);
    alert("Erreur de connexion");
  }
}

async function syncCartography() {
  if (!selectedEntityId) return;

  const btn = document.getElementById("sync-carto-btn");
  btn.textContent = "⏳ Synchronisation...";
  btn.disabled = true;

  try {
    const res = await fetch(`/activities/api/entities/${selectedEntityId}/sync`, {
      method: "POST"
    });

    const data = await res.json();

    if (res.ok) {
      const stats = data.stats;
      alert(`Synchronisation terminée !\n\n` +
            `- Activités dans le SVG: ${stats.total_in_svg}\n` +
            `- Nouvelles ajoutées: ${stats.added}\n` +
            `- Inchangées: ${stats.unchanged}`);
      
      const entity = ALL_ENTITIES.find(e => e.id === selectedEntityId);
      if (entity && entity.is_active) {
        window.location.reload();
      } else {
        await loadEntitiesList();
        selectEntity(selectedEntityId);
      }
    } else {
      alert(data.error || "Erreur lors de la synchronisation");
    }
  } catch (err) {
    console.error("Erreur sync:", err);
    alert("Erreur de connexion");
  } finally {
    btn.textContent = "🔄 Synchroniser les activités";
    btn.disabled = false;
  }
}

/* ============================================================
   UPLOAD CARTOGRAPHIE (DROPZONE)
============================================================ */

function initDropzone() {
  const zone = document.getElementById("dropzone");
  const status = document.getElementById("dropzone-status");
  if (!zone || !status) return;

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("dragover");
  });

  zone.addEventListener("dragleave", () => {
    zone.classList.remove("dragover");
  });

  zone.addEventListener("drop", async (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");

    const file = e.dataTransfer.files[0];
    if (!file) return;

    await uploadFile(file, status);
  });

  zone.addEventListener("click", () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".svg,.vsdx";
    input.onchange = async (e) => {
      if (e.target.files[0]) {
        await uploadFile(e.target.files[0], status);
      }
    };
    input.click();
  });
}

async function uploadFile(file, statusElement) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['svg', 'vsdx'].includes(ext)) {
    showStatus(statusElement, "error", "Format invalide — fichier .SVG ou .VSDX requis");
    return;
  }

  // Vérifier qu'une entité est sélectionnée
  if (!selectedEntityId) {
    showStatus(statusElement, "error", "Veuillez d'abord sélectionner une entité");
    return;
  }

  // Activer l'entité si elle ne l'est pas
  const entity = ALL_ENTITIES.find(e => e.id === selectedEntityId);
  if (entity && !entity.is_active) {
    showStatus(statusElement, "loading", "Activation de l'entité...");
    try {
      await fetch(`/activities/api/entities/${selectedEntityId}/activate`, {
        method: "POST"
      });
    } catch (err) {
      showStatus(statusElement, "error", "Erreur lors de l'activation");
      return;
    }
  }

  showStatus(statusElement, "loading", "Upload en cours...");

  const form = new FormData();
  form.append("file", file);

  try {
    const res = await fetch("/activities/upload-carto", {
      method: "POST",
      body: form
    });

    const data = await res.json();

    if (!res.ok) {
      showStatus(statusElement, "error", data.error || "Erreur lors de l'upload");
      return;
    }

    const stats = data.sync_stats || {};
    showStatus(statusElement, "success", 
      `Cartographie installée ! ${stats.added || 0} nouvelles activités ajoutées.`);

    setTimeout(() => window.location.reload(), 1500);

  } catch (err) {
    console.error("Erreur upload:", err);
    showStatus(statusElement, "error", "Erreur de connexion ou du serveur");
  }
}

/* ============================================================
   UTILITAIRES
============================================================ */

function showStatus(element, type, message) {
  element.className = `status-message status-${type}`;
  element.textContent = message;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/* ============================================================
   PAN / ZOOM DU SVG
============================================================ */

function getPanLimits() {
  const wrapper = document.getElementById("carto-pan-wrapper");
  if (!wrapper) return { minX: 0, maxX: 0, minY: 0, maxY: 0 };

  const wrapperRect = wrapper.getBoundingClientRect();
  const scaledWidth = svgWidth * currentScale;
  const scaledHeight = svgHeight * currentScale;

  return {
    minX: wrapperRect.width - scaledWidth,
    maxX: 0,
    minY: wrapperRect.height - scaledHeight,
    maxY: 0
  };
}

function constrainPan() {
  const limits = getPanLimits();

  if (limits.minX > limits.maxX) {
    panX = (limits.minX + limits.maxX) / 2;
  } else {
    panX = Math.max(limits.minX, Math.min(limits.maxX, panX));
  }

  if (limits.minY > limits.maxY) {
    panY = (limits.minY + limits.maxY) / 2;
  } else {
    panY = Math.max(limits.minY, Math.min(limits.maxY, panY));
  }
}

function centerCartography() {
  const wrapper = document.getElementById("carto-pan-wrapper");
  if (!wrapper) return;

  const wrapperRect = wrapper.getBoundingClientRect();
  const scaledWidth = svgWidth * currentScale;
  const scaledHeight = svgHeight * currentScale;

  panX = (wrapperRect.width - scaledWidth) / 2;
  panY = (wrapperRect.height - scaledHeight) / 2;

  applyTransform();
}

function updateZoomDisplay() {
  const btn = document.getElementById("carto-zoom-reset");
  if (btn) {
    btn.textContent = `${Math.round(currentScale * 100)}%`;
  }
}

function applyTransform() {
  const panInner = document.getElementById("pan-inner");
  if (!panInner) return;

  constrainPan();
  panInner.style.transform = `translate(${panX}px, ${panY}px) scale(${currentScale})`;
  updateZoomDisplay();
}

function zoomAtCenter(delta) {
  const wrapper = document.getElementById("carto-pan-wrapper");
  const panInner = document.getElementById("pan-inner");
  if (!wrapper || !panInner) return;

  const oldScale = currentScale;

  if (delta > 0) {
    currentScale = Math.min(3, currentScale + 0.2);
  } else {
    currentScale = Math.max(0.2, currentScale - 0.2);
  }

  const rect = wrapper.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  const scaleRatio = currentScale / oldScale;
  panX = centerX - (centerX - panX) * scaleRatio;
  panY = centerY - (centerY - panY) * scaleRatio;

  applyTransform();
}

function initZoomButtons() {
  const btnIn = document.getElementById("carto-zoom-in");
  const btnOut = document.getElementById("carto-zoom-out");
  const btnReset = document.getElementById("carto-zoom-reset");

  if (btnIn) btnIn.onclick = () => zoomAtCenter(1);
  if (btnOut) btnOut.onclick = () => zoomAtCenter(-1);
  if (btnReset) {
    btnReset.onclick = () => {
      currentScale = 0.5;
      centerCartography();
    };
  }
}

function initPan() {
  const wrapper = document.getElementById("carto-pan-wrapper");
  const panInner = document.getElementById("pan-inner");
  if (!wrapper || !panInner) return;

  wrapper.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    if (isOverActivity) return;

    isPanning = true;
    startX = e.clientX - panX;
    startY = e.clientY - panY;
    wrapper.classList.add("panning");
    panInner.classList.add("no-transition");
  });

  window.addEventListener("mousemove", (e) => {
    if (!isPanning) return;
    panX = e.clientX - startX;
    panY = e.clientY - startY;
    applyTransform();
  });

  window.addEventListener("mouseup", () => {
    if (!isPanning) return;
    isPanning = false;
    const wrapper = document.getElementById("carto-pan-wrapper");
    const panInner = document.getElementById("pan-inner");
    if (wrapper) wrapper.classList.remove("panning");
    if (panInner) panInner.classList.remove("no-transition");
  });

  wrapper.addEventListener("dragstart", (e) => e.preventDefault());
}

function initWheelZoom() {
  const wrapper = document.getElementById("carto-pan-wrapper");
  if (!wrapper) return;

  wrapper.addEventListener("wheel", (e) => {
    e.preventDefault();

    const delta = e.deltaY > 0 ? -1 : 1;
    const oldScale = currentScale;

    if (delta > 0) {
      currentScale = Math.min(3, currentScale + 0.1);
    } else {
      currentScale = Math.max(0.2, currentScale - 0.1);
    }

    const rect = wrapper.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const scaleRatio = currentScale / oldScale;
    panX = mouseX - (mouseX - panX) * scaleRatio;
    panY = mouseY - (mouseY - panY) * scaleRatio;

    applyTransform();
  }, { passive: false });
}

/* ============================================================
   ACTIVATION DES CLICS SUR LE SVG - CORRIGÉ
============================================================ */

function activateSvgClicks(svgElement) {
  console.log("[SVG] Activation des clics sur le SVG...");
  console.log("[SVG] SHAPE_ACTIVITY_MAP:", SHAPE_ACTIVITY_MAP);
  
  // Parcourir TOUS les éléments du SVG
  const allElements = svgElement.querySelectorAll("*");
  let activatedCount = 0;
  
  allElements.forEach((el) => {
    // Chercher l'attribut mID dans le namespace Visio
    const mid = el.getAttributeNS(VISIO_NS, "mID");
    if (!mid) return;

    const activityId = SHAPE_ACTIVITY_MAP[mid];
    if (!activityId) {
      // console.log(`[SVG] mID ${mid} trouvé mais pas d'activité associée`);
      return;
    }

    console.log(`[SVG] Activité trouvée: mID=${mid} -> activityId=${activityId}`);
    activatedCount++;

    // Forcer les événements sur cet élément
    el.style.pointerEvents = "all";
    el.style.cursor = "pointer";

    // Hover - signaler qu'on est sur une activité
    el.addEventListener("mouseenter", () => {
      isOverActivity = true;
      el.style.filter = "drop-shadow(0 0 8px #22c55e)";
      el.style.opacity = "0.85";

      const wrapper = document.getElementById("carto-pan-wrapper");
      if (wrapper && !wrapper.classList.contains("panning")) {
        wrapper.style.cursor = "pointer";
      }
    });

    el.addEventListener("mouseleave", () => {
      isOverActivity = false;
      el.style.filter = "";
      el.style.opacity = "1";

      const wrapper = document.getElementById("carto-pan-wrapper");
      if (wrapper && !wrapper.classList.contains("panning")) {
        wrapper.style.cursor = "grab";
      }
    });

    // Clic - naviguer vers l'activité
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
      console.log(`[SVG] Clic sur activité ${activityId}`);
      window.location.href = `/activities/view?activity_id=${activityId}`;
    });
  });
  
  console.log(`[SVG] ${activatedCount} activités activées sur ${allElements.length} éléments`);
}

/* ============================================================
   CHARGEMENT DU SVG
============================================================ */

async function loadSvg() {
  if (!SVG_EXISTS || !ACTIVE_ENTITY) {
    console.log("[SVG] Pas de SVG ou pas d'entité active");
    return;
  }

  const container = document.getElementById("svg-container");
  if (!container) return;

  console.log("[SVG] Chargement du SVG...");

  try {
    const response = await fetch("/activities/svg");
    if (!response.ok) throw new Error("SVG non disponible");

    const svgText = await response.text();
    container.innerHTML = svgText;

    const svgElement = container.querySelector("svg");
    if (svgElement) {
      svgRoot = svgElement;

      // Récupérer les dimensions
      const vb = svgElement.viewBox && svgElement.viewBox.baseVal;
      if (vb && vb.width && vb.height) {
        svgWidth = vb.width;
        svgHeight = vb.height;
      } else {
        // Fallback: essayer width/height ou getBoundingClientRect
        svgWidth = parseFloat(svgElement.getAttribute("width")) || 1000;
        svgHeight = parseFloat(svgElement.getAttribute("height")) || 800;
      }

      console.log(`[SVG] Dimensions: ${svgWidth} x ${svgHeight}`);

      initZoomButtons();
      centerCartography();
      
      // Activer les clics sur les activités
      activateSvgClicks(svgElement);
    }
  } catch (err) {
    console.error("Erreur chargement SVG:", err);
    container.innerHTML = `
      <div class="svg-error">
        <p>📄</p>
        <p>Impossible de charger la cartographie</p>
        <p>${err.message}</p>
      </div>
    `;
  }
}

/* ============================================================
   LISTE DES ACTIVITÉS (colonne de droite)
============================================================ */

function initListClicks() {
  document.querySelectorAll(".activity-item").forEach((li) => {
    li.addEventListener("click", () => {
      const id = li.dataset.id;
      if (!id) return;
      window.location.href = `/activities/view?activity_id=${id}`;
    });
  });
}

/* ============================================================
   INITIALISATION
============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  console.log("[INIT] Démarrage...");
  console.log("[INIT] SVG_EXISTS:", SVG_EXISTS);
  console.log("[INIT] ACTIVE_ENTITY:", ACTIVE_ENTITY);
  console.log("[INIT] SHAPE_ACTIVITY_MAP:", SHAPE_ACTIVITY_MAP);

  // Gestionnaire d'entités
  const managerBtn = document.getElementById("entity-manager-btn");
  const closeBtn = document.getElementById("close-popup");
  const createBtn = document.getElementById("create-entity-btn");
  const activateBtn = document.getElementById("activate-entity-btn");
  const deleteBtn = document.getElementById("delete-entity-btn");
  const renameBtn = document.getElementById("rename-entity-btn");
  const syncBtn = document.getElementById("sync-carto-btn");

  if (managerBtn) managerBtn.onclick = openEntityManager;
  if (closeBtn) closeBtn.onclick = closeEntityManager;
  if (createBtn) createBtn.onclick = createEntity;
  if (activateBtn) activateBtn.onclick = activateEntity;
  if (deleteBtn) deleteBtn.onclick = showDeleteModal;
  if (renameBtn) renameBtn.onclick = showRenameModal;
  if (syncBtn) syncBtn.onclick = syncCartography;

  // Modals
  const cancelDeleteBtn = document.getElementById("cancel-delete-btn");
  const confirmDeleteBtn = document.getElementById("confirm-delete-btn");
  const cancelRenameBtn = document.getElementById("cancel-rename-btn");
  const confirmRenameBtn = document.getElementById("confirm-rename-btn");

  if (cancelDeleteBtn) {
    cancelDeleteBtn.onclick = () => {
      document.getElementById("delete-confirm-modal").classList.add("hidden");
    };
  }
  if (confirmDeleteBtn) confirmDeleteBtn.onclick = confirmDeleteEntity;
  if (cancelRenameBtn) {
    cancelRenameBtn.onclick = () => {
      document.getElementById("rename-modal").classList.add("hidden");
    };
  }
  if (confirmRenameBtn) confirmRenameBtn.onclick = confirmRenameEntity;

  // Fermer popup avec Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.getElementById("entity-manager-popup")?.classList.add("hidden");
      document.getElementById("delete-confirm-modal")?.classList.add("hidden");
      document.getElementById("rename-modal")?.classList.add("hidden");
    }
  });

  // Création avec Enter
  const nameInput = document.getElementById("new-entity-name");
  if (nameInput) {
    nameInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") createEntity();
    });
  }

  // Dropzone
  initDropzone();

  // Pan/Zoom
  initPan();
  initWheelZoom();

  // Liste des activités (clics sur la liste)
  initListClicks();

  // Charger le SVG si disponible
  loadSvg();
});