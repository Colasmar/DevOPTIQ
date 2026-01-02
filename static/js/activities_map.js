/* ============================================================
   CARTOGRAPHIE DES ACTIVITÉS - WIZARD UNIFIÉ
   Gestion des entités + Import SVG/VSDX
============================================================ */

const SHAPE_ACTIVITY_MAP = window.CARTO_SHAPE_MAP || {};
const SVG_EXISTS = window.SVG_EXISTS || false;
const VSDX_EXISTS = window.VSDX_EXISTS || false;
const CURRENT_SVG = window.CURRENT_SVG || null;
const CURRENT_VSDX = window.CURRENT_VSDX || null;
const ACTIVE_ENTITY = window.ACTIVE_ENTITY || null;
const ALL_ENTITIES = window.ALL_ENTITIES || [];

const VISIO_NS = "http://schemas.microsoft.com/visio/2003/SVGExtensions/";

/* ============================================================
   ÉTAT GLOBAL PAN / ZOOM
============================================================ */
let svgElement = null;
let currentScale = 0.5;
let panX = 0;
let panY = 0;
let isPanning = false;
let startX = 0;
let startY = 0;
let hasMoved = false;
let svgWidth = 0;
let svgHeight = 0;
let clickableElements = new Set();
const ZOOM_MIN = 0.1;
const ZOOM_MAX = 10;

/* ============================================================
   ÉTAT DU WIZARD
============================================================ */
const wizardState = {
  // Entité sélectionnée dans le wizard
  selectedEntity: null,
  // Mode: 'new' | 'update'
  mode: null,
  // Étape courante
  currentStep: 0,
  // Fichiers
  vsdxFile: null,
  svgFile: null,
  keepVsdx: false,
  keepSvg: false,
  // Preview des connexions
  connectionsPreview: null,
  // Cache des entités
  entitiesCache: []
};

/* ============================================================
   UTILITAIRES
============================================================ */
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' octets';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' Ko';
  return (bytes / (1024 * 1024)).toFixed(1) + ' Mo';
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/* ============================================================
   PAN / ZOOM
============================================================ */
function centerCartography() {
  const wrapper = $("#carto-pan-wrapper");
  const panInner = $("#pan-inner");
  if (!wrapper || !panInner || !svgWidth || !svgHeight) return;

  const wrapperRect = wrapper.getBoundingClientRect();
  const scaledWidth = svgWidth * currentScale;
  const scaledHeight = svgHeight * currentScale;

  panX = (wrapperRect.width - scaledWidth) / 2;
  panY = (wrapperRect.height - scaledHeight) / 2;

  if (scaledWidth > wrapperRect.width) panX = 20;
  if (scaledHeight > wrapperRect.height) panY = 20;

  panInner.style.transform = `translate(${panX}px, ${panY}px) scale(${currentScale})`;
  updateZoomDisplay();
}

function updateZoomDisplay() {
  const btn = $("#carto-zoom-reset");
  if (btn) btn.textContent = `${Math.round(currentScale * 100)}%`;
}

function applyTransform() {
  const panInner = $("#pan-inner");
  if (!panInner) return;
  panInner.style.transform = `translate(${panX}px, ${panY}px) scale(${currentScale})`;
  updateZoomDisplay();
}

function zoomAtPoint(delta, mouseX, mouseY) {
  const oldScale = currentScale;
  const zoomStep = 0.15;

  if (delta > 0) {
    currentScale = Math.min(ZOOM_MAX, currentScale * (1 + zoomStep));
  } else {
    currentScale = Math.max(ZOOM_MIN, currentScale * (1 - zoomStep));
  }

  const scaleRatio = currentScale / oldScale;
  panX = mouseX - (mouseX - panX) * scaleRatio;
  panY = mouseY - (mouseY - panY) * scaleRatio;

  applyTransform();
}

function zoomAtCenter(delta) {
  const wrapper = $("#carto-pan-wrapper");
  if (!wrapper) return;
  const rect = wrapper.getBoundingClientRect();
  zoomAtPoint(delta, rect.width / 2, rect.height / 2);
}

function initZoomButtons() {
  const btnIn = $("#carto-zoom-in");
  const btnOut = $("#carto-zoom-out");
  const btnReset = $("#carto-zoom-reset");

  if (btnIn) btnIn.onclick = () => zoomAtCenter(1);
  if (btnOut) btnOut.onclick = () => zoomAtCenter(-1);
  if (btnReset) {
    btnReset.onclick = () => {
      const wrapper = $("#carto-pan-wrapper");
      if (wrapper && svgWidth && svgHeight) {
        const wrapperRect = wrapper.getBoundingClientRect();
        const scaleX = (wrapperRect.width - 40) / svgWidth;
        const scaleY = (wrapperRect.height - 40) / svgHeight;
        currentScale = Math.min(scaleX, scaleY, 1);
        currentScale = Math.max(currentScale, 0.1);
      } else {
        currentScale = 0.5;
      }
      centerCartography();
    };
  }
}

function initPan() {
  const wrapper = $("#carto-pan-wrapper");
  const panInner = $("#pan-inner");
  if (!wrapper || !panInner) return;

  const MOVE_THRESHOLD = 5;
  let startPanX = 0;
  let startPanY = 0;

  wrapper.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    isPanning = true;
    hasMoved = false;
    startX = e.clientX;
    startY = e.clientY;
    startPanX = panX;
    startPanY = panY;
    wrapper.classList.add("panning");
    panInner.classList.add("no-transition");
  });

  window.addEventListener("mousemove", (e) => {
    if (!isPanning) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance > MOVE_THRESHOLD && !hasMoved) hasMoved = true;
    panX = startPanX + dx;
    panY = startPanY + dy;
    applyTransform();
  });

  window.addEventListener("mouseup", () => {
    if (!isPanning) return;
    isPanning = false;
    wrapper.classList.remove("panning");
    panInner.classList.remove("no-transition");
    setTimeout(() => { hasMoved = false; }, 10);
  });

  wrapper.addEventListener("dragstart", (e) => e.preventDefault());
}

function initWheelZoom() {
  const wrapper = $("#carto-pan-wrapper");
  if (!wrapper) return;
  wrapper.addEventListener("wheel", (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -1 : 1;
    const rect = wrapper.getBoundingClientRect();
    zoomAtPoint(delta, e.clientX - rect.left, e.clientY - rect.top);
  }, { passive: false });
}

/* ============================================================
   CHARGEMENT DU SVG INLINE
============================================================ */
async function loadSvgInline() {
  const container = $("#svg-container");
  if (!container) return;

  if (!SVG_EXISTS) {
    container.innerHTML = `
      <div class="svg-placeholder">
        <p>🗺️ Aucune cartographie disponible</p>
        <p>Utilisez "📦 Gérer la cartographie" pour importer vos fichiers</p>
      </div>
    `;
    return;
  }

  try {
    const svgUrl = "/activities/svg?t=" + Date.now();
    const response = await fetch(svgUrl);
    if (!response.ok) throw new Error(`SVG introuvable (${response.status})`);
    const svgText = await response.text();
    container.innerHTML = svgText;
    svgElement = container.querySelector("svg");
    if (!svgElement) throw new Error("Pas d'élément <svg> trouvé");
    setupSvg();
  } catch (error) {
    console.error("[CARTO] Erreur:", error);
    container.innerHTML = `
      <div class="svg-error">
        <p>❌ Erreur de chargement</p>
        <p>${error.message}</p>
      </div>
    `;
  }
}

function setupSvg() {
  if (!svgElement) return;

  const vb = svgElement.viewBox && svgElement.viewBox.baseVal;
  if (vb && vb.width > 0 && vb.height > 0) {
    svgWidth = vb.width;
    svgHeight = vb.height;
  } else {
    const widthAttr = svgElement.getAttribute("width");
    const heightAttr = svgElement.getAttribute("height");
    if (widthAttr && heightAttr) {
      svgWidth = parseFloat(widthAttr) || 1000;
      svgHeight = parseFloat(heightAttr) || 800;
    } else {
      const rect = svgElement.getBoundingClientRect();
      svgWidth = rect.width || 1000;
      svgHeight = rect.height || 800;
    }
  }

  svgElement.style.width = svgWidth + "px";
  svgElement.style.height = svgHeight + "px";
  svgElement.style.display = "block";
  svgElement.style.overflow = "visible";

  activateSvgClicks();
  initZoomButtons();

  const wrapper = $("#carto-pan-wrapper");
  if (wrapper) {
    const wrapperRect = wrapper.getBoundingClientRect();
    const scaleX = (wrapperRect.width - 40) / svgWidth;
    const scaleY = (wrapperRect.height - 40) / svgHeight;
    currentScale = Math.min(scaleX, scaleY, 1);
    currentScale = Math.max(currentScale, 0.1);
  }

  setTimeout(centerCartography, 50);
}

function activateSvgClicks() {
  if (!svgElement) return;

  svgElement.querySelectorAll("*").forEach((el) => {
    let mid = el.getAttributeNS(VISIO_NS, "mID");
    if (!mid) mid = el.getAttribute("v:mID");
    if (!mid) mid = el.getAttribute("data-mid");
    if (!mid) {
      for (let attr of el.attributes || []) {
        if (attr.name.toLowerCase().includes("mid") || attr.name.toLowerCase().includes("shapeid")) {
          mid = attr.value;
          break;
        }
      }
    }
    if (!mid) return;

    const activityId = SHAPE_ACTIVITY_MAP[mid];
    if (!activityId) return;

    clickableElements.add(el);
    el.dataset.activityId = activityId;
    el.style.cursor = "pointer";
    el.classList.add("carto-activity");

    el.addEventListener("mouseenter", () => {
      el.style.filter = "drop-shadow(0 0 8px #22c55e)";
      el.style.opacity = "0.85";
    });

    el.addEventListener("mouseleave", () => {
      el.style.filter = "";
      el.style.opacity = "1";
    });

    el.addEventListener("click", (e) => {
      if (!hasMoved) {
        e.stopPropagation();
        e.preventDefault();
        window.location.href = `/activities/view?activity_id=${activityId}`;
      }
    });
  });
}

function initListClicks() {
  $$(".activity-item").forEach((li) => {
    li.addEventListener("click", () => {
      const id = li.dataset.id;
      if (id) window.location.href = `/activities/view?activity_id=${id}`;
    });
  });
}

/* ============================================================
   WIZARD - INITIALISATION
============================================================ */
function initWizard() {
  const popup = $("#carto-wizard-popup");
  const btnOpen = $("#carto-wizard-btn");
  const btnClose = $("#close-wizard");

  if (!popup || !btnOpen) return;

  // Ouvrir le wizard
  btnOpen.onclick = () => {
    resetWizard();
    loadEntitiesList();
    popup.classList.remove("hidden");
  };

  // Fermer le wizard
  if (btnClose) {
    btnClose.onclick = () => popup.classList.add("hidden");
  }

  // Fermer en cliquant sur l'overlay
  popup.addEventListener("click", (e) => {
    if (e.target.classList.contains("wizard-overlay")) {
      popup.classList.add("hidden");
    }
  });

  // Création d'entité
  $("#wizard-create-entity-btn")?.addEventListener("click", createEntityFromWizard);
  $("#wizard-new-entity-name")?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") createEntityFromWizard();
  });

  // Écran action
  $("#action-back")?.addEventListener("click", () => goToScreen("entities"));
  $("#wizard-new-btn")?.addEventListener("click", () => startWizardSteps("new"));
  $("#wizard-update-btn")?.addEventListener("click", () => startWizardSteps("update"));

  // Actions entité
  $("#wizard-activate-btn")?.addEventListener("click", activateSelectedEntity);
  $("#wizard-rename-btn")?.addEventListener("click", showRenameModal);
  $("#wizard-delete-btn")?.addEventListener("click", showDeleteModal);

  // Navigation étapes
  $("#step1-back")?.addEventListener("click", () => goToScreen("action"));
  $("#step1-next")?.addEventListener("click", () => goToStep(2));
  $("#step2-back")?.addEventListener("click", () => goToStep(1));
  $("#step2-next")?.addEventListener("click", () => goToStep(3));
  $("#step3-back")?.addEventListener("click", () => goToStep(2));
  $("#step3-submit")?.addEventListener("click", submitWizard);

  // Écrans finaux
  $("#success-close")?.addEventListener("click", () => window.location.reload());
  $("#error-retry")?.addEventListener("click", () => goToStep(3));
  $("#error-close")?.addEventListener("click", () => {
    $("#carto-wizard-popup")?.classList.add("hidden");
  });

  // Checkboxes
  $("#keep-vsdx-checkbox")?.addEventListener("change", (e) => {
    wizardState.keepVsdx = e.target.checked;
    updateDropzoneState("vsdx");
  });
  $("#keep-svg-checkbox")?.addEventListener("change", (e) => {
    wizardState.keepSvg = e.target.checked;
    updateDropzoneState("svg");
  });

  // Dropzones
  initWizardDropzone("vsdx");
  initWizardDropzone("svg");

  // Modals
  $("#cancel-delete-btn")?.addEventListener("click", hideDeleteModal);
  $("#confirm-delete-btn")?.addEventListener("click", confirmDeleteEntity);
  $("#cancel-rename-btn")?.addEventListener("click", hideRenameModal);
  $("#confirm-rename-btn")?.addEventListener("click", confirmRenameEntity);
}

function resetWizard() {
  wizardState.selectedEntity = null;
  wizardState.mode = null;
  wizardState.currentStep = 0;
  wizardState.vsdxFile = null;
  wizardState.svgFile = null;
  wizardState.keepVsdx = false;
  wizardState.keepSvg = false;
  wizardState.connectionsPreview = null;

  // Reset UI
  const keepVsdxCb = $("#keep-vsdx-checkbox");
  const keepSvgCb = $("#keep-svg-checkbox");
  if (keepVsdxCb) keepVsdxCb.checked = false;
  if (keepSvgCb) keepSvgCb.checked = false;

  $("#vsdx-preview")?.classList.add("hidden");
  $("#svg-preview")?.classList.add("hidden");
  $("#vsdx-dropzone")?.classList.remove("hidden", "disabled");
  $("#svg-dropzone")?.classList.remove("hidden", "disabled");

  const vsdxInput = $("#vsdx-file-input");
  const svgInput = $("#svg-file-input");
  if (vsdxInput) vsdxInput.value = "";
  if (svgInput) svgInput.value = "";

  goToScreen("entities");
  $("#wizard-progress")?.classList.add("hidden");
}

/* ============================================================
   WIZARD - LISTE DES ENTITÉS
============================================================ */
async function loadEntitiesList() {
  const listEl = $("#wizard-entities-list");
  const emptyEl = $("#wizard-entities-empty");
  if (!listEl) return;

  try {
    const response = await fetch("/activities/api/entities");
    const entities = await response.json();
    wizardState.entitiesCache = entities;

    if (entities.length === 0) {
      listEl.innerHTML = "";
      emptyEl?.classList.remove("hidden");
      return;
    }

    emptyEl?.classList.add("hidden");

    listEl.innerHTML = entities.map(e => `
      <div class="entity-grid-item ${e.is_active ? 'active' : ''}" data-id="${e.id}">
        <div class="entity-grid-icon">🏢</div>
        <div class="entity-grid-info">
          <span class="entity-grid-name">${e.name}</span>
          <span class="entity-grid-stats">${e.activities_count || 0} activités</span>
        </div>
        ${e.is_active ? '<span class="entity-grid-badge">Active</span>' : ''}
        ${e.svg_filename ? '<span class="entity-grid-svg">🖼️</span>' : ''}
      </div>
    `).join("");

    // Ajouter les handlers
    listEl.querySelectorAll(".entity-grid-item").forEach(item => {
      item.addEventListener("click", () => selectEntityForAction(parseInt(item.dataset.id)));
    });

  } catch (err) {
    console.error("Erreur chargement entités:", err);
    listEl.innerHTML = '<p class="error">Erreur de chargement</p>';
  }
}

async function createEntityFromWizard() {
  const nameInput = $("#wizard-new-entity-name");
  const name = nameInput?.value.trim();

  if (!name) {
    alert("Veuillez entrer un nom pour l'entité");
    return;
  }

  try {
    const response = await fetch("/activities/api/entities", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name })
    });

    const data = await response.json();

    if (data.error) {
      alert("Erreur: " + data.error);
      return;
    }

    nameInput.value = "";
    await loadEntitiesList();
    
    // Sélectionner la nouvelle entité
    setTimeout(() => selectEntityForAction(data.entity.id), 100);

  } catch (err) {
    alert("Erreur réseau");
  }
}

/* ============================================================
   WIZARD - SÉLECTION D'ENTITÉ
============================================================ */
async function selectEntityForAction(entityId) {
  // Récupérer les infos de l'entité
  const entity = wizardState.entitiesCache.find(e => e.id === entityId);
  if (!entity) return;

  // Charger les infos détaillées (connexions)
  let connectionsCount = 0;
  try {
    const response = await fetch(`/activities/api/entities/${entityId}/details`);
    if (response.ok) {
      const details = await response.json();
      connectionsCount = details.connections_count || 0;
      entity.svg_exists = details.svg_exists;
      entity.vsdx_exists = details.vsdx_exists;
      entity.current_svg = details.current_svg;
      entity.current_vsdx = details.current_vsdx;
    }
  } catch (err) {
    console.log("Pas de détails supplémentaires");
  }

  wizardState.selectedEntity = entity;

  // Mettre à jour l'affichage
  $("#selected-entity-name").textContent = entity.name;
  $("#selected-entity-activities").textContent = entity.activities_count || 0;
  $("#selected-entity-connections").textContent = connectionsCount;

  // Badge actif
  const activeBadge = $("#selected-entity-active-badge");
  if (activeBadge) {
    activeBadge.classList.toggle("hidden", !entity.is_active);
  }

  // Bouton activer
  const activateBtn = $("#wizard-activate-btn");
  if (activateBtn) {
    activateBtn.style.display = entity.is_active ? "none" : "";
  }

  // Status fichiers
  const svgStatus = $("#selected-entity-svg-status .file-value");
  const vsdxStatus = $("#selected-entity-vsdx-status .file-value");
  
  if (svgStatus) {
    svgStatus.textContent = entity.svg_filename || entity.svg_exists ? "✓ Présent" : "—";
    svgStatus.className = "file-value " + (entity.svg_filename || entity.svg_exists ? "present" : "missing");
  }
  if (vsdxStatus) {
    vsdxStatus.textContent = entity.vsdx_exists ? "✓ Présent" : "—";
    vsdxStatus.className = "file-value " + (entity.vsdx_exists ? "present" : "missing");
  }

  // Bouton modifier (actif seulement si des fichiers existent)
  const updateBtn = $("#wizard-update-btn");
  if (updateBtn) {
    const hasFiles = entity.svg_filename || entity.svg_exists || entity.vsdx_exists;
    updateBtn.disabled = !hasFiles;
  }

  // Passer à l'écran action
  goToScreen("action");
}

/* ============================================================
   WIZARD - ACTIONS ENTITÉ
============================================================ */
async function activateSelectedEntity() {
  if (!wizardState.selectedEntity) return;

  try {
    const response = await fetch(`/activities/api/entities/${wizardState.selectedEntity.id}/activate`, {
      method: "POST"
    });

    const data = await response.json();

    if (data.error) {
      alert("Erreur: " + data.error);
      return;
    }

    // Recharger la page pour mettre à jour le contexte
    window.location.reload();

  } catch (err) {
    alert("Erreur réseau");
  }
}

function showRenameModal() {
  if (!wizardState.selectedEntity) return;
  
  const input = $("#rename-input");
  if (input) input.value = wizardState.selectedEntity.name;
  
  $("#rename-modal")?.classList.remove("hidden");
}

function hideRenameModal() {
  $("#rename-modal")?.classList.add("hidden");
}

async function confirmRenameEntity() {
  if (!wizardState.selectedEntity) return;

  const newName = $("#rename-input")?.value.trim();
  if (!newName) {
    alert("Veuillez entrer un nom");
    return;
  }

  try {
    const response = await fetch(`/activities/api/entities/${wizardState.selectedEntity.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName })
    });

    const data = await response.json();

    if (data.error) {
      alert("Erreur: " + data.error);
      return;
    }

    hideRenameModal();
    
    // Mettre à jour et recharger
    wizardState.selectedEntity.name = newName;
    $("#selected-entity-name").textContent = newName;
    await loadEntitiesList();

  } catch (err) {
    alert("Erreur réseau");
  }
}

function showDeleteModal() {
  if (!wizardState.selectedEntity) return;
  $("#confirm-delete-modal")?.classList.remove("hidden");
}

function hideDeleteModal() {
  $("#confirm-delete-modal")?.classList.add("hidden");
}

async function confirmDeleteEntity() {
  if (!wizardState.selectedEntity) return;

  try {
    const response = await fetch(`/activities/api/entities/${wizardState.selectedEntity.id}`, {
      method: "DELETE"
    });

    const data = await response.json();

    if (data.error) {
      alert("Erreur: " + data.error);
      return;
    }

    hideDeleteModal();
    window.location.reload();

  } catch (err) {
    alert("Erreur réseau");
  }
}

/* ============================================================
   WIZARD - ÉTAPES D'IMPORT
============================================================ */
function startWizardSteps(mode) {
  wizardState.mode = mode;

  // Configurer les options "garder l'actuel"
  const keepVsdxOption = $("#keep-vsdx-option");
  const keepSvgOption = $("#keep-svg-option");
  const entity = wizardState.selectedEntity;

  if (mode === "update" && entity) {
    if (entity.vsdx_exists && keepVsdxOption) {
      keepVsdxOption.classList.remove("hidden");
      $("#current-vsdx-name").textContent = entity.current_vsdx || "Fichier actuel";
    } else {
      keepVsdxOption?.classList.add("hidden");
    }

    if ((entity.svg_filename || entity.svg_exists) && keepSvgOption) {
      keepSvgOption.classList.remove("hidden");
      $("#current-svg-name").textContent = entity.current_svg || "Fichier actuel";
    } else {
      keepSvgOption?.classList.add("hidden");
    }
  } else {
    keepVsdxOption?.classList.add("hidden");
    keepSvgOption?.classList.add("hidden");
  }

  goToStep(1);
}

function goToScreen(screenId) {
  $$(".wizard-screen").forEach(s => s.classList.remove("active"));
  $(`#wizard-screen-${screenId}`)?.classList.add("active");

  // Afficher/cacher la progression
  const progressEl = $("#wizard-progress");
  if (progressEl) {
    const showProgress = ["step1", "step2", "step3"].includes(screenId);
    progressEl.classList.toggle("hidden", !showProgress);
  }

  // Titre
  const titleEl = $("#wizard-title");
  if (titleEl) {
    if (screenId === "entities") {
      titleEl.textContent = "📦 Gestion de la cartographie";
    } else if (screenId === "action") {
      titleEl.textContent = "📦 " + (wizardState.selectedEntity?.name || "Entité");
    } else {
      titleEl.textContent = "📦 Import cartographie";
    }
  }
}

function goToStep(step) {
  wizardState.currentStep = step;
  updateProgress(step);

  if (step === 1) {
    goToScreen("step1");
    updateDropzoneState("vsdx");
  } else if (step === 2) {
    goToScreen("step2");
    updateDropzoneState("svg");
  } else if (step === 3) {
    prepareRecap();
    goToScreen("step3");
  }
}

function updateProgress(step) {
  const progressEl = $("#wizard-progress");
  if (!progressEl) return;

  progressEl.classList.remove("hidden");

  for (let i = 1; i <= 3; i++) {
    const stepEl = $(`.progress-step[data-step="${i}"]`);
    if (!stepEl) continue;

    stepEl.classList.remove("active", "completed");
    if (i < step) stepEl.classList.add("completed");
    else if (i === step) stepEl.classList.add("active");
  }

  for (let i = 1; i <= 2; i++) {
    const lineEl = $(`.progress-line[data-line="${i}"]`);
    if (lineEl) {
      lineEl.classList.toggle("filled", i < step);
    }
  }
}

function updateDropzoneState(type) {
  const isKeeping = type === "vsdx" ? wizardState.keepVsdx : wizardState.keepSvg;
  const dropzone = $(`#${type}-dropzone`);
  
  if (dropzone) {
    dropzone.classList.toggle("disabled", isKeeping);
  }
}

/* ============================================================
   WIZARD - DROPZONES
============================================================ */
function initWizardDropzone(type) {
  const dropzone = $(`#${type}-dropzone`);
  const fileInput = $(`#${type}-file-input`);
  const removeBtn = $(`#${type}-remove`);

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => {
    if (!dropzone.classList.contains("disabled")) fileInput.click();
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    if (!dropzone.classList.contains("disabled")) dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (dropzone.classList.contains("disabled")) return;
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(type, file);
  });

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file) handleFileSelect(type, file);
  });

  if (removeBtn) {
    removeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      clearFile(type);
    });
  }
}

function handleFileSelect(type, file) {
  const expectedExt = type === "vsdx" ? ".vsdx" : ".svg";

  if (!file.name.toLowerCase().endsWith(expectedExt)) {
    alert(`Format invalide. Fichier ${expectedExt.toUpperCase()} requis.`);
    return;
  }

  if (type === "vsdx") {
    wizardState.vsdxFile = file;
  } else {
    wizardState.svgFile = file;
  }

  const dropzone = $(`#${type}-dropzone`);
  const preview = $(`#${type}-preview`);
  const filenameEl = $(`#${type}-filename`);
  const filesizeEl = $(`#${type}-filesize`);

  if (dropzone) dropzone.classList.add("hidden");
  if (preview) preview.classList.remove("hidden");
  if (filenameEl) filenameEl.textContent = file.name;
  if (filesizeEl) filesizeEl.textContent = formatFileSize(file.size);

  if (type === "vsdx") {
    analyzeVsdxConnections(file);
  }
}

function clearFile(type) {
  if (type === "vsdx") {
    wizardState.vsdxFile = null;
    wizardState.connectionsPreview = null;
  } else {
    wizardState.svgFile = null;
  }

  const dropzone = $(`#${type}-dropzone`);
  const preview = $(`#${type}-preview`);
  const fileInput = $(`#${type}-file-input`);

  if (dropzone) dropzone.classList.remove("hidden");
  if (preview) preview.classList.add("hidden");
  if (fileInput) fileInput.value = "";
}

/* ============================================================
   WIZARD - ANALYSE VSDX
============================================================ */
async function analyzeVsdxConnections(file) {
  if (!wizardState.selectedEntity) return;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("entity_id", wizardState.selectedEntity.id);

  try {
    const response = await fetch("/activities/preview-connections", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    if (data.error) {
      console.error("Erreur analyse VSDX:", data.error);
      wizardState.connectionsPreview = null;
      return;
    }

    wizardState.connectionsPreview = data;
  } catch (err) {
    console.error("Erreur analyse VSDX:", err);
    wizardState.connectionsPreview = null;
  }
}

/* ============================================================
   WIZARD - RÉCAPITULATIF
============================================================ */
function prepareRecap() {
  const entity = wizardState.selectedEntity;
  
  // Nom de l'entité
  $("#recap-entity-name").textContent = entity?.name || "-";

  // Récap VSDX
  const recapVsdxCard = $("#recap-vsdx");
  const recapVsdxName = $("#recap-vsdx-name");
  const recapVsdxStatus = $("#recap-vsdx-status");

  recapVsdxCard?.classList.remove("new-file", "kept-file");

  if (wizardState.vsdxFile) {
    recapVsdxName.textContent = wizardState.vsdxFile.name;
    recapVsdxStatus.textContent = "Nouveau";
    recapVsdxStatus.className = "recap-file-status new";
    recapVsdxCard?.classList.add("new-file");
  } else if (wizardState.keepVsdx && entity?.vsdx_exists) {
    recapVsdxName.textContent = entity.current_vsdx || "Fichier actuel";
    recapVsdxStatus.textContent = "Conservé";
    recapVsdxStatus.className = "recap-file-status kept";
    recapVsdxCard?.classList.add("kept-file");
  } else {
    recapVsdxName.textContent = "Aucun fichier";
    recapVsdxStatus.textContent = "-";
    recapVsdxStatus.className = "recap-file-status none";
  }

  // Récap SVG
  const recapSvgCard = $("#recap-svg");
  const recapSvgName = $("#recap-svg-name");
  const recapSvgStatus = $("#recap-svg-status");

  recapSvgCard?.classList.remove("new-file", "kept-file");

  if (wizardState.svgFile) {
    recapSvgName.textContent = wizardState.svgFile.name;
    recapSvgStatus.textContent = "Nouveau";
    recapSvgStatus.className = "recap-file-status new";
    recapSvgCard?.classList.add("new-file");
  } else if (wizardState.keepSvg && (entity?.svg_filename || entity?.svg_exists)) {
    recapSvgName.textContent = entity.current_svg || "Fichier actuel";
    recapSvgStatus.textContent = "Conservé";
    recapSvgStatus.className = "recap-file-status kept";
    recapSvgCard?.classList.add("kept-file");
  } else {
    recapSvgName.textContent = "Aucun fichier";
    recapSvgStatus.textContent = "-";
    recapSvgStatus.className = "recap-file-status none";
  }

  // Section connexions
  const connectionsSection = $("#connections-preview-section");
  const noVsdxMessage = $("#no-vsdx-message");

  if (wizardState.vsdxFile && wizardState.connectionsPreview) {
    connectionsSection?.classList.remove("hidden");
    noVsdxMessage?.classList.add("hidden");
    displayConnectionsTable(wizardState.connectionsPreview);
  } else if (wizardState.keepVsdx && entity?.vsdx_exists) {
    connectionsSection?.classList.add("hidden");
    if (noVsdxMessage) {
      noVsdxMessage.classList.remove("hidden");
      noVsdxMessage.querySelector("p").textContent =
        "Le fichier VSDX actuel sera conservé — les connexions ne seront pas modifiées.";
    }
  } else {
    connectionsSection?.classList.add("hidden");
    if (noVsdxMessage) {
      noVsdxMessage.classList.remove("hidden");
      noVsdxMessage.querySelector("p").textContent =
        "Aucun fichier VSDX fourni — les connexions existantes seront conservées.";
    }
  }
}

function displayConnectionsTable(data) {
  const statsEl = $("#wizard-connections-stats");
  if (statsEl) {
    statsEl.innerHTML = `
      <div class="stat-box">
        <div class="stat-value">${data.total_connections || 0}</div>
        <div class="stat-label">Total</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">${data.valid_connections || 0}</div>
        <div class="stat-label">Valides</div>
      </div>
      <div class="stat-box ${(data.invalid_connections || 0) > 0 ? 'warning' : ''}">
        <div class="stat-value">${data.invalid_connections || 0}</div>
        <div class="stat-label">Invalides</div>
      </div>
    `;
  }

  const missingWarning = $("#wizard-missing-warning");
  const missingList = $("#wizard-missing-list");

  if (data.missing_activities && data.missing_activities.length > 0) {
    missingWarning?.classList.remove("hidden");
    if (missingList) {
      missingList.innerHTML = data.missing_activities.map(name => `<li>${name}</li>`).join("");
    }
  } else {
    missingWarning?.classList.add("hidden");
  }

  const tbody = $("#wizard-connections-tbody");
  if (tbody && data.connections) {
    tbody.innerHTML = data.connections.map(conn => {
      const typeClass = conn.data_type
        ? (conn.data_type === "déclenchante" ? "declenchante" : "nourrissante")
        : "";
      const statusClass = conn.valid ? "status-valid" : "status-invalid";
      const statusText = conn.valid ? "✓ OK" : "✗ Manquante";

      return `
        <tr>
          <td>${conn.source || "-"}</td>
          <td class="arrow-cell">→</td>
          <td>${conn.target || "-"}</td>
          <td>${conn.data_name || "-"}</td>
          <td>${conn.data_type ? `<span class="data-type ${typeClass}">${conn.data_type}</span>` : "-"}</td>
          <td class="${statusClass}">${statusText}</td>
        </tr>
      `;
    }).join("");
  }
}

/* ============================================================
   WIZARD - SOUMISSION
============================================================ */
async function submitWizard() {
  const entity = wizardState.selectedEntity;
  if (!entity) {
    alert("Aucune entité sélectionnée");
    return;
  }

  const hasSvg = wizardState.svgFile || (wizardState.keepSvg && (entity.svg_filename || entity.svg_exists));

  if (!hasSvg && wizardState.mode === "new") {
    alert("Veuillez fournir au moins un fichier SVG pour créer une cartographie.");
    return;
  }

  goToScreen("processing");
  updateProcessingStep("svg", "active");

  const formData = new FormData();
  formData.append("entity_id", entity.id);
  formData.append("mode", wizardState.mode);

  if (wizardState.svgFile) {
    formData.append("svg_file", wizardState.svgFile);
  }
  formData.append("keep_svg", wizardState.keepSvg.toString());

  if (wizardState.vsdxFile) {
    formData.append("vsdx_file", wizardState.vsdxFile);
  }
  formData.append("keep_vsdx", wizardState.keepVsdx.toString());

  const clearConnections = $("#clear-connections-checkbox")?.checked || false;
  formData.append("clear_connections", clearConnections.toString());

  try {
    await sleep(500);
    updateProcessingStep("svg", "done");
    updateProcessingStep("vsdx", "active");

    const response = await fetch("/activities/upload-cartography", {
      method: "POST",
      body: formData
    });

    await sleep(500);
    updateProcessingStep("vsdx", "done");
    updateProcessingStep("save", "active");

    const data = await response.json();

    await sleep(400);
    updateProcessingStep("save", "done");

    if (data.error) {
      showError(data.error);
      return;
    }

    showSuccess(data);

  } catch (err) {
    console.error("Erreur soumission:", err);
    showError("Erreur réseau. Veuillez réessayer.");
  }
}

function updateProcessingStep(stepId, status) {
  const stepEl = $(`#proc-step-${stepId}`);
  if (!stepEl) return;

  stepEl.classList.remove("active", "done");
  stepEl.classList.add(status);

  const iconEl = stepEl.querySelector(".proc-icon");
  if (iconEl) {
    if (status === "active") iconEl.textContent = "⏳";
    else if (status === "done") iconEl.textContent = "✓";
    else iconEl.textContent = "○";
  }
}

function showSuccess(data) {
  goToScreen("success");

  const messageEl = $("#success-message");
  const statsEl = $("#success-stats");

  if (messageEl) {
    messageEl.textContent = "Votre cartographie a été mise à jour avec succès.";
  }

  if (statsEl && data.stats) {
    statsEl.innerHTML = `
      <div class="stat-item">
        <span class="stat-value">${data.stats.activities || 0}</span>
        <span class="stat-label">Activités</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">${data.stats.connections || 0}</span>
        <span class="stat-label">Connexions</span>
      </div>
    `;
  }
}

function showError(message) {
  goToScreen("error");
  const messageEl = $("#error-message");
  if (messageEl) messageEl.textContent = message;
}

/* ============================================================
   INITIALISATION GLOBALE
============================================================ */
document.addEventListener("DOMContentLoaded", async () => {
  console.log("[CARTO] Initialisation...");

  initListClicks();
  initWizard();
  initPan();
  initWheelZoom();

  await loadSvgInline();

  console.log("[CARTO] Initialisation terminée");
});