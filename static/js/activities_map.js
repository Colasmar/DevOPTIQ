/* ============================================================
   CARTOGRAPHIE DES ACTIVITÉS - VERSION SVG INLINE + ENTITÉS
   + WIZARD CARTOGRAPHIE (SVG + VSDX)
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

// Entité sélectionnée dans le gestionnaire
let selectedEntityId = null;

/* ============================================================
   ÉTAT DU WIZARD
============================================================ */
const wizardState = {
  mode: null, // 'new' | 'update'
  currentStep: 0, // 0=home, 1, 2, 3
  vsdxFile: null,
  svgFile: null,
  keepVsdx: false,
  keepSvg: false,
  connectionsPreview: null
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

  const allElements = svgElement.querySelectorAll("*");

  allElements.forEach((el) => {
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
    el.dataset.mid = mid;
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

/* ============================================================
   LISTE DES ACTIVITÉS
============================================================ */
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

  // Boutons écran d'accueil
  $("#wizard-new-btn")?.addEventListener("click", () => startWizard("new"));
  $("#wizard-update-btn")?.addEventListener("click", () => startWizard("update"));

  // Navigation étape 1
  $("#step1-back")?.addEventListener("click", () => goToScreen("home"));
  $("#step1-next")?.addEventListener("click", () => goToStep(2));

  // Navigation étape 2
  $("#step2-back")?.addEventListener("click", () => goToStep(1));
  $("#step2-next")?.addEventListener("click", () => goToStep(3));

  // Navigation étape 3
  $("#step3-back")?.addEventListener("click", () => goToStep(2));
  $("#step3-submit")?.addEventListener("click", submitWizard);

  // Écran succès
  $("#success-close")?.addEventListener("click", () => window.location.reload());

  // Écran erreur
  $("#error-retry")?.addEventListener("click", () => goToStep(3));
  $("#error-close")?.addEventListener("click", () => {
    $("#carto-wizard-popup")?.classList.add("hidden");
  });

  // Checkboxes "garder l'actuel"
  $("#keep-vsdx-checkbox")?.addEventListener("change", (e) => {
    wizardState.keepVsdx = e.target.checked;
    updateDropzoneState("vsdx");
  });

  $("#keep-svg-checkbox")?.addEventListener("change", (e) => {
    wizardState.keepSvg = e.target.checked;
    updateDropzoneState("svg");
  });

  // Initialiser les dropzones
  initWizardDropzone("vsdx");
  initWizardDropzone("svg");
}

function resetWizard() {
  wizardState.mode = null;
  wizardState.currentStep = 0;
  wizardState.vsdxFile = null;
  wizardState.svgFile = null;
  wizardState.keepVsdx = false;
  wizardState.keepSvg = false;
  wizardState.connectionsPreview = null;

  // Reset checkboxes
  const keepVsdxCb = $("#keep-vsdx-checkbox");
  const keepSvgCb = $("#keep-svg-checkbox");
  if (keepVsdxCb) keepVsdxCb.checked = false;
  if (keepSvgCb) keepSvgCb.checked = false;

  // Reset previews
  $("#vsdx-preview")?.classList.add("hidden");
  $("#svg-preview")?.classList.add("hidden");
  $("#vsdx-dropzone")?.classList.remove("hidden");
  $("#svg-dropzone")?.classList.remove("hidden");

  // Reset file inputs
  const vsdxInput = $("#vsdx-file-input");
  const svgInput = $("#svg-file-input");
  if (vsdxInput) vsdxInput.value = "";
  if (svgInput) svgInput.value = "";

  // Afficher écran d'accueil
  goToScreen("home");
  updateProgress(0);
}

function startWizard(mode) {
  wizardState.mode = mode;

  // Configurer les options "garder l'actuel"
  const keepVsdxOption = $("#keep-vsdx-option");
  const keepSvgOption = $("#keep-svg-option");

  if (mode === "update") {
    // Mode modification : afficher les options si fichiers existants
    if (VSDX_EXISTS && keepVsdxOption) {
      keepVsdxOption.classList.remove("hidden");
      $("#current-vsdx-name").textContent = CURRENT_VSDX || "Fichier actuel";
    }
    if (SVG_EXISTS && keepSvgOption) {
      keepSvgOption.classList.remove("hidden");
      $("#current-svg-name").textContent = CURRENT_SVG || "Fichier actuel";
    }
  } else {
    // Mode création : cacher les options
    keepVsdxOption?.classList.add("hidden");
    keepSvgOption?.classList.add("hidden");
  }

  goToStep(1);
}

function goToScreen(screenId) {
  // Cacher tous les écrans
  $$(".wizard-screen").forEach(s => s.classList.remove("active"));

  // Afficher l'écran demandé
  $(`#wizard-screen-${screenId}`)?.classList.add("active");

  // Cacher/afficher la progression
  const progressEl = $("#wizard-progress");
  if (progressEl) {
    progressEl.style.display = screenId === "home" ? "none" : "flex";
  }
}

function goToStep(step) {
  wizardState.currentStep = step;

  // Mettre à jour la progression
  updateProgress(step);

  // Afficher l'écran correspondant
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

  // Afficher la barre de progression
  progressEl.style.display = step > 0 ? "flex" : "none";

  // Mettre à jour les cercles
  for (let i = 1; i <= 3; i++) {
    const stepEl = $(`.progress-step[data-step="${i}"]`);
    if (!stepEl) continue;

    stepEl.classList.remove("active", "completed");

    if (i < step) {
      stepEl.classList.add("completed");
    } else if (i === step) {
      stepEl.classList.add("active");
    }
  }

  // Mettre à jour les lignes
  for (let i = 1; i <= 2; i++) {
    const lineEl = $(`.progress-line[data-line="${i}"]`);
    if (!lineEl) continue;

    if (i < step) {
      lineEl.classList.add("filled");
    } else {
      lineEl.classList.remove("filled");
    }
  }
}

function updateDropzoneState(type) {
  const isKeeping = type === "vsdx" ? wizardState.keepVsdx : wizardState.keepSvg;
  const dropzoneWrapper = $(`#${type}-dropzone-wrapper`);

  if (dropzoneWrapper) {
    const dropzone = $(`#${type}-dropzone`);
    if (dropzone) {
      if (isKeeping) {
        dropzone.classList.add("disabled");
      } else {
        dropzone.classList.remove("disabled");
      }
    }
  }
}

/* ============================================================
   WIZARD - DROPZONES
============================================================ */
function initWizardDropzone(type) {
  const dropzone = $(`#${type}-dropzone`);
  const fileInput = $(`#${type}-file-input`);
  const preview = $(`#${type}-preview`);
  const removeBtn = $(`#${type}-remove`);

  if (!dropzone || !fileInput) return;

  // Clic sur la dropzone
  dropzone.addEventListener("click", () => {
    if (dropzone.classList.contains("disabled")) return;
    fileInput.click();
  });

  // Drag & drop
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    if (!dropzone.classList.contains("disabled")) {
      dropzone.classList.add("dragover");
    }
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");

    if (dropzone.classList.contains("disabled")) return;

    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(type, file);
  });

  // Sélection via input
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file) handleFileSelect(type, file);
  });

  // Bouton supprimer
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

  // Stocker le fichier
  if (type === "vsdx") {
    wizardState.vsdxFile = file;
  } else {
    wizardState.svgFile = file;
  }

  // Afficher l'aperçu
  const dropzone = $(`#${type}-dropzone`);
  const preview = $(`#${type}-preview`);
  const filenameEl = $(`#${type}-filename`);
  const filesizeEl = $(`#${type}-filesize`);

  if (dropzone) dropzone.classList.add("hidden");
  if (preview) preview.classList.remove("hidden");
  if (filenameEl) filenameEl.textContent = file.name;
  if (filesizeEl) filesizeEl.textContent = formatFileSize(file.size);

  // Si VSDX, lancer l'analyse des connexions
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
  const formData = new FormData();
  formData.append("file", file);

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
  // Récap VSDX
  const recapVsdxName = $("#recap-vsdx-name");
  const recapVsdxStatus = $("#recap-vsdx-status");
  const recapVsdxCard = $("#recap-vsdx");

  if (recapVsdxCard) {
    recapVsdxCard.classList.remove("new-file", "kept-file");
  }

  if (wizardState.vsdxFile) {
    if (recapVsdxName) recapVsdxName.textContent = wizardState.vsdxFile.name;
    if (recapVsdxStatus) {
      recapVsdxStatus.textContent = "Nouveau";
      recapVsdxStatus.className = "recap-file-status new";
    }
    if (recapVsdxCard) recapVsdxCard.classList.add("new-file");
  } else if (wizardState.keepVsdx && VSDX_EXISTS) {
    if (recapVsdxName) recapVsdxName.textContent = CURRENT_VSDX || "Fichier actuel";
    if (recapVsdxStatus) {
      recapVsdxStatus.textContent = "Conservé";
      recapVsdxStatus.className = "recap-file-status kept";
    }
    if (recapVsdxCard) recapVsdxCard.classList.add("kept-file");
  } else {
    if (recapVsdxName) recapVsdxName.textContent = "Aucun fichier";
    if (recapVsdxStatus) {
      recapVsdxStatus.textContent = "-";
      recapVsdxStatus.className = "recap-file-status none";
    }
  }

  // Récap SVG
  const recapSvgName = $("#recap-svg-name");
  const recapSvgStatus = $("#recap-svg-status");
  const recapSvgCard = $("#recap-svg");

  if (recapSvgCard) {
    recapSvgCard.classList.remove("new-file", "kept-file");
  }

  if (wizardState.svgFile) {
    if (recapSvgName) recapSvgName.textContent = wizardState.svgFile.name;
    if (recapSvgStatus) {
      recapSvgStatus.textContent = "Nouveau";
      recapSvgStatus.className = "recap-file-status new";
    }
    if (recapSvgCard) recapSvgCard.classList.add("new-file");
  } else if (wizardState.keepSvg && SVG_EXISTS) {
    if (recapSvgName) recapSvgName.textContent = CURRENT_SVG || "Fichier actuel";
    if (recapSvgStatus) {
      recapSvgStatus.textContent = "Conservé";
      recapSvgStatus.className = "recap-file-status kept";
    }
    if (recapSvgCard) recapSvgCard.classList.add("kept-file");
  } else {
    if (recapSvgName) recapSvgName.textContent = "Aucun fichier";
    if (recapSvgStatus) {
      recapSvgStatus.textContent = "-";
      recapSvgStatus.className = "recap-file-status none";
    }
  }

  // Afficher ou cacher la section connexions
  const connectionsSection = $("#connections-preview-section");
  const noVsdxMessage = $("#no-vsdx-message");

  if (wizardState.vsdxFile && wizardState.connectionsPreview) {
    if (connectionsSection) connectionsSection.classList.remove("hidden");
    if (noVsdxMessage) noVsdxMessage.classList.add("hidden");
    displayConnectionsTable(wizardState.connectionsPreview);
  } else if (wizardState.keepVsdx && VSDX_EXISTS) {
    if (connectionsSection) connectionsSection.classList.add("hidden");
    if (noVsdxMessage) {
      noVsdxMessage.classList.remove("hidden");
      noVsdxMessage.querySelector("p").textContent =
        "Le fichier VSDX actuel sera conservé — les connexions ne seront pas modifiées.";
    }
  } else {
    if (connectionsSection) connectionsSection.classList.add("hidden");
    if (noVsdxMessage) {
      noVsdxMessage.classList.remove("hidden");
      noVsdxMessage.querySelector("p").textContent =
        "Aucun fichier VSDX fourni — les connexions existantes seront conservées.";
    }
  }
}

function displayConnectionsTable(data) {
  // Stats
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

  // Activités manquantes
  const missingWarning = $("#wizard-missing-warning");
  const missingList = $("#wizard-missing-list");

  if (data.missing_activities && data.missing_activities.length > 0) {
    if (missingWarning) missingWarning.classList.remove("hidden");
    if (missingList) {
      missingList.innerHTML = data.missing_activities
        .map(name => `<li>${name}</li>`)
        .join("");
    }
  } else {
    if (missingWarning) missingWarning.classList.add("hidden");
  }

  // Tableau
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
  // Vérifier qu'on a au moins un fichier
  const hasSvg = wizardState.svgFile || (wizardState.keepSvg && SVG_EXISTS);
  const hasVsdx = wizardState.vsdxFile || (wizardState.keepVsdx && VSDX_EXISTS);

  if (!hasSvg && wizardState.mode === "new") {
    alert("Veuillez fournir au moins un fichier SVG pour créer une cartographie.");
    return;
  }

  // Afficher l'écran de traitement
  goToScreen("processing");
  updateProcessingStep("svg", "active");

  const formData = new FormData();
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
    // Simuler une progression visuelle
    await sleep(500);
    updateProcessingStep("svg", "done");
    updateProcessingStep("vsdx", "active");

    // Envoyer la requête
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

    // Succès
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
   GESTIONNAIRE D'ENTITÉS
============================================================ */
function initEntityManager() {
  const popup = $("#entity-manager-popup");
  const btnOpen = $("#entity-manager-btn");
  const btnClose = $("#close-entity-manager");

  if (!popup || !btnOpen) return;

  btnOpen.onclick = () => {
    loadEntitiesList();
    popup.classList.remove("hidden");
  };

  if (btnClose) {
    btnClose.onclick = () => popup.classList.add("hidden");
  }

  popup.addEventListener("click", (e) => {
    if (e.target === popup) popup.classList.add("hidden");
  });

  // Création d'entité
  $("#create-entity-btn")?.addEventListener("click", createEntity);
  $("#new-entity-name")?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") createEntity();
  });

  // Actions entité
  $("#activate-entity-btn")?.addEventListener("click", activateEntity);
  $("#rename-entity-btn")?.addEventListener("click", showRenameModal);
  $("#delete-entity-btn")?.addEventListener("click", showDeleteModal);

  // Modal suppression
  $("#cancel-delete-btn")?.addEventListener("click", hideDeleteModal);
  $("#confirm-delete-btn")?.addEventListener("click", confirmDelete);

  // Modal renommage
  $("#cancel-rename-btn")?.addEventListener("click", hideRenameModal);
  $("#confirm-rename-btn")?.addEventListener("click", confirmRename);
}

async function loadEntitiesList() {
  try {
    const response = await fetch("/activities/api/entities");
    const entities = await response.json();

    const list = $("#entities-list");
    if (!list) return;

    if (entities.length === 0) {
      list.innerHTML = '<li class="no-entity">Aucune entité créée</li>';
      return;
    }

    list.innerHTML = entities.map(e => `
      <li class="entity-item ${e.is_active ? 'active' : ''}" data-id="${e.id}">
        <span class="entity-name">${e.name}</span>
        ${e.is_active ? '<span class="entity-active-badge">Active</span>' : ''}
      </li>
    `).join("");

    // Ajouter les handlers de clic
    list.querySelectorAll(".entity-item").forEach(item => {
      item.addEventListener("click", () => selectEntity(item.dataset.id));
    });

  } catch (err) {
    console.error("Erreur chargement entités:", err);
  }
}

async function selectEntity(id) {
  selectedEntityId = id;

  // Highlight dans la liste
  $$(".entity-item").forEach(item => {
    item.classList.toggle("selected", item.dataset.id === id);
  });

  // Charger les détails
  try {
    const response = await fetch("/activities/api/entities");
    const entities = await response.json();
    const entity = entities.find(e => e.id == id);

    if (!entity) return;

    $("#entity-details-placeholder")?.classList.add("hidden");
    $("#entity-details")?.classList.remove("hidden");

    $("#entity-detail-name").textContent = entity.name;
    $("#entity-detail-description").textContent = entity.description || "Aucune description";
    $("#entity-activities-count").textContent = entity.activities_count || 0;
    $("#entity-svg-status").textContent = entity.svg_filename ? "✓" : "—";

    // Cacher le bouton activer si déjà active
    const activateBtn = $("#activate-entity-btn");
    if (activateBtn) {
      activateBtn.style.display = entity.is_active ? "none" : "inline-block";
    }

  } catch (err) {
    console.error("Erreur sélection entité:", err);
  }
}

async function createEntity() {
  const nameInput = $("#new-entity-name");
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
    loadEntitiesList();
    setTimeout(() => selectEntity(data.entity.id), 100);

  } catch (err) {
    alert("Erreur réseau");
  }
}

async function activateEntity() {
  if (!selectedEntityId) return;

  try {
    const response = await fetch(`/activities/api/entities/${selectedEntityId}/activate`, {
      method: "POST"
    });

    const data = await response.json();

    if (data.error) {
      alert("Erreur: " + data.error);
      return;
    }

    window.location.reload();

  } catch (err) {
    alert("Erreur réseau");
  }
}

function showDeleteModal() {
  if (!selectedEntityId) return;
  $("#confirm-delete-modal")?.classList.remove("hidden");
}

function hideDeleteModal() {
  $("#confirm-delete-modal")?.classList.add("hidden");
}

async function confirmDelete() {
  if (!selectedEntityId) return;

  try {
    const response = await fetch(`/activities/api/entities/${selectedEntityId}`, {
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

function showRenameModal() {
  if (!selectedEntityId) return;

  const currentName = $("#entity-detail-name")?.textContent || "";
  const input = $("#rename-input");
  if (input) input.value = currentName;

  $("#rename-modal")?.classList.remove("hidden");
}

function hideRenameModal() {
  $("#rename-modal")?.classList.add("hidden");
}

async function confirmRename() {
  if (!selectedEntityId) return;

  const newName = $("#rename-input")?.value.trim();
  if (!newName) {
    alert("Veuillez entrer un nom");
    return;
  }

  try {
    const response = await fetch(`/activities/api/entities/${selectedEntityId}`, {
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
    loadEntitiesList();
    selectEntity(selectedEntityId);

  } catch (err) {
    alert("Erreur réseau");
  }
}

/* ============================================================
   INITIALISATION GLOBALE
============================================================ */
document.addEventListener("DOMContentLoaded", async () => {
  console.log("[CARTO] Initialisation...");
  console.log("[CARTO] SVG_EXISTS:", SVG_EXISTS);
  console.log("[CARTO] VSDX_EXISTS:", VSDX_EXISTS);
  console.log("[CARTO] ACTIVE_ENTITY:", ACTIVE_ENTITY);

  // Initialiser les composants
  initListClicks();
  initEntityManager();
  initWizard();

  // Initialiser pan et zoom
  initPan();
  initWheelZoom();

  // Charger le SVG
  await loadSvgInline();

  console.log("[CARTO] Initialisation terminée");
});