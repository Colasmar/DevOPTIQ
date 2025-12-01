/* ============================================================
   CARTOGRAPHIE DES ACTIVITÉS - VERSION SVG INLINE
   
   Cette version charge le SVG inline dans le DOM, ce qui permet
   un contrôle total sur les événements (pan + clic activités)
============================================================ */

const SHAPE_ACTIVITY_MAP = window.CARTO_SHAPE_MAP || {};
const CARTO_HISTORY = window.CARTO_HISTORY || [];
const SVG_EXISTS = window.SVG_EXISTS || false;

const VISIO_NS = "http://schemas.microsoft.com/visio/2003/SVGExtensions/";

/* ============================================================
   ÉTAT GLOBAL PAN / ZOOM
============================================================ */
let svgElement = null;
let currentScale = 0.5; // Zoom initial plus petit pour voir toute la carto

let panX = 0;
let panY = 0;

// Pour le pan (drag)
let isPanning = false;
let startX = 0;
let startY = 0;
let hasMoved = false; // Pour distinguer clic vs drag

// Dimensions du SVG
let svgWidth = 0;
let svgHeight = 0;

// Éléments cliquables (activités)
let clickableElements = new Set();

// Limites de zoom
const ZOOM_MIN = 0.1;
const ZOOM_MAX = 10; // 1000%

/* ============================================================
   PAS DE CONTRAINTES DE PAN - Liberté totale de navigation
============================================================ */
function constrainPan() {
  // Ne rien contraindre - l'utilisateur peut naviguer librement
  // On pourrait ajouter des limites douces si nécessaire plus tard
}

/* ============================================================
   CENTRER LA CARTOGRAPHIE AU CHARGEMENT
============================================================ */
function centerCartography() {
  const wrapper = document.getElementById("carto-pan-wrapper");
  const panInner = document.getElementById("pan-inner");
  if (!wrapper || !panInner || !svgWidth || !svgHeight) return;

  const wrapperRect = wrapper.getBoundingClientRect();
  const scaledWidth = svgWidth * currentScale;
  const scaledHeight = svgHeight * currentScale;

  // Calculer pour centrer le SVG dans le wrapper
  panX = (wrapperRect.width - scaledWidth) / 2;
  panY = (wrapperRect.height - scaledHeight) / 2;

  // Si le SVG scalé est plus grand que le wrapper, positionner en haut à gauche avec marge
  if (scaledWidth > wrapperRect.width) {
    panX = 20; // Petite marge à gauche
  }
  if (scaledHeight > wrapperRect.height) {
    panY = 20; // Petite marge en haut pour voir la légende
  }

  // Appliquer la transformation
  panInner.style.transform = `translate(${panX}px, ${panY}px) scale(${currentScale})`;
  updateZoomDisplay();
  
  console.log(`Centrage: wrapper=${wrapperRect.width}x${wrapperRect.height}, svg=${scaledWidth}x${scaledHeight}, pan=${panX},${panY}`);
}

/* ============================================================
   ZOOM
============================================================ */
function updateZoomDisplay() {
  const btn = document.getElementById("carto-zoom-reset");
  if (btn) {
    btn.textContent = `${Math.round(currentScale * 100)}%`;
  }
}

function applyTransform() {
  const panInner = document.getElementById("pan-inner");
  if (!panInner) return;

  // Pas de contrainte de pan - navigation libre
  panInner.style.transform = `translate(${panX}px, ${panY}px) scale(${currentScale})`;
  updateZoomDisplay();
}

function zoomAtPoint(delta, mouseX, mouseY) {
  const wrapper = document.getElementById("carto-pan-wrapper");
  if (!wrapper) return;

  const oldScale = currentScale;

  // Pas de zoom proportionnel pour plus de contrôle
  const zoomStep = 0.15;

  if (delta > 0) {
    currentScale = Math.min(ZOOM_MAX, currentScale * (1 + zoomStep));
  } else {
    currentScale = Math.max(ZOOM_MIN, currentScale * (1 - zoomStep));
  }

  // Zoom centré sur la position de la souris
  const scaleRatio = currentScale / oldScale;
  panX = mouseX - (mouseX - panX) * scaleRatio;
  panY = mouseY - (mouseY - panY) * scaleRatio;

  applyTransform();
}

function zoomAtCenter(delta) {
  const wrapper = document.getElementById("carto-pan-wrapper");
  if (!wrapper) return;

  const rect = wrapper.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  zoomAtPoint(delta, centerX, centerY);
}

function initZoomButtons() {
  const btnIn = document.getElementById("carto-zoom-in");
  const btnOut = document.getElementById("carto-zoom-out");
  const btnReset = document.getElementById("carto-zoom-reset");

  if (btnIn) {
    btnIn.onclick = () => zoomAtCenter(1);
  }
  if (btnOut) {
    btnOut.onclick = () => zoomAtCenter(-1);
  }
  if (btnReset) {
    btnReset.onclick = () => {
      // Recalculer le scale optimal pour voir toute la carto
      const wrapper = document.getElementById("carto-pan-wrapper");
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

/* ============================================================
   PAN (DÉPLACEMENT À LA SOURIS)
   
   Stratégie: Le pan commence toujours au mousedown.
   Si l'utilisateur bouge la souris, c'est un pan.
   Si l'utilisateur ne bouge pas (ou très peu) et relâche sur
   une activité, c'est un clic.
============================================================ */
function initPan() {
  const wrapper = document.getElementById("carto-pan-wrapper");
  const panInner = document.getElementById("pan-inner");
  if (!wrapper || !panInner) return;

  // Seuil de mouvement pour distinguer clic vs drag (en pixels)
  const MOVE_THRESHOLD = 5;
  let startPanX = 0;
  let startPanY = 0;

  wrapper.addEventListener("mousedown", (e) => {
    // Uniquement bouton gauche
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
    
    console.log(`[PAN] mousedown at (${e.clientX}, ${e.clientY}), hasMoved reset to false`);
  });

  window.addEventListener("mousemove", (e) => {
    if (!isPanning) return;

    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    const distance = Math.sqrt(dx * dx + dy * dy);

    // Vérifier si on a bougé significativement
    if (distance > MOVE_THRESHOLD && !hasMoved) {
      hasMoved = true;
      console.log(`[PAN] hasMoved = true (distance: ${distance.toFixed(1)}px)`);
    }

    panX = startPanX + dx;
    panY = startPanY + dy;
    applyTransform();
  });

  window.addEventListener("mouseup", (e) => {
    if (!isPanning) return;

    console.log(`[PAN] mouseup, hasMoved=${hasMoved}`);

    isPanning = false;
    wrapper.classList.remove("panning");
    panInner.classList.remove("no-transition");

    // Si on n'a pas bougé, le clic sera géré par les event listeners des activités
    if (!hasMoved) {
      console.log("[PAN] Pas de mouvement détecté, clic potentiel sur activité");
    }
    
    // IMPORTANT: Reset hasMoved après un court délai pour permettre au click de se propager
    setTimeout(() => {
      hasMoved = false;
    }, 10);
  });

  // Empêcher le drag natif des images/SVG
  wrapper.addEventListener("dragstart", (e) => e.preventDefault());
}

/* ============================================================
   ZOOM À LA MOLETTE
============================================================ */
function initWheelZoom() {
  const wrapper = document.getElementById("carto-pan-wrapper");
  if (!wrapper) return;

  wrapper.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();

      const delta = e.deltaY > 0 ? -1 : 1;

      const rect = wrapper.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      zoomAtPoint(delta, mouseX, mouseY);
    },
    { passive: false }
  );
}

/* ============================================================
   CHARGEMENT DU SVG INLINE
============================================================ */
async function loadSvgInline() {
  const container = document.getElementById("svg-container");
  if (!container) {
    console.error("[CARTO] Container svg-container non trouvé !");
    return;
  }

  console.log("[CARTO] SVG_EXISTS =", SVG_EXISTS);

  if (!SVG_EXISTS) {
    container.innerHTML = `
      <div class="svg-error">
        <p>🗺️ Aucune cartographie disponible</p>
        <p>Utilisez le bouton "Actions cartographie" pour importer un fichier SVG ou VSDX</p>
      </div>
    `;
    return;
  }

  try {
    // Charger le SVG depuis l'URL statique
    const svgUrl = "/static/img/carto_activities.svg";
    console.log("[CARTO] Chargement du SVG depuis:", svgUrl);
    
    const response = await fetch(svgUrl + "?t=" + Date.now()); // Cache bust
    
    if (!response.ok) {
      throw new Error(`Fichier SVG introuvable (${response.status})`);
    }

    const svgText = await response.text();
    console.log("[CARTO] SVG chargé, taille:", svgText.length, "caractères");
    
    container.innerHTML = svgText;

    // Récupérer l'élément SVG
    svgElement = container.querySelector("svg");
    if (!svgElement) {
      throw new Error("Pas d'élément <svg> trouvé dans le fichier");
    }

    console.log("[CARTO] Élément SVG trouvé:", svgElement);

    // Configurer le SVG
    setupSvg();

  } catch (error) {
    console.error("[CARTO] Erreur chargement SVG:", error);
    container.innerHTML = `
      <div class="svg-error">
        <p>❌ Erreur de chargement de la cartographie</p>
        <p>${error.message}</p>
      </div>
    `;
  }
}

/* ============================================================
   CONFIGURATION DU SVG APRÈS CHARGEMENT
============================================================ */
function setupSvg() {
  if (!svgElement) return;

  // Récupérer les dimensions via viewBox en priorité
  const vb = svgElement.viewBox && svgElement.viewBox.baseVal;
  if (vb && vb.width > 0 && vb.height > 0) {
    svgWidth = vb.width;
    svgHeight = vb.height;
  } else {
    // Fallback: utiliser width/height attributs
    const widthAttr = svgElement.getAttribute("width");
    const heightAttr = svgElement.getAttribute("height");
    
    if (widthAttr && heightAttr) {
      svgWidth = parseFloat(widthAttr) || 1000;
      svgHeight = parseFloat(heightAttr) || 800;
    } else {
      // Dernier fallback: getBoundingClientRect
      const rect = svgElement.getBoundingClientRect();
      svgWidth = rect.width || 1000;
      svgHeight = rect.height || 800;
    }
  }

  console.log(`Dimensions SVG détectées: ${svgWidth} x ${svgHeight}`);

  // Appliquer les dimensions au SVG
  svgElement.style.width = svgWidth + "px";
  svgElement.style.height = svgHeight + "px";
  svgElement.style.display = "block";
  svgElement.style.overflow = "visible";

  // Activer les clics sur les activités
  activateSvgClicks();

  // Initialiser zoom
  initZoomButtons();
  
  // Calculer le scale initial pour que la carto tienne dans la vue
  const wrapper = document.getElementById("carto-pan-wrapper");
  if (wrapper) {
    const wrapperRect = wrapper.getBoundingClientRect();
    const scaleX = (wrapperRect.width - 40) / svgWidth;  // 40px de marge
    const scaleY = (wrapperRect.height - 40) / svgHeight;
    currentScale = Math.min(scaleX, scaleY, 1); // Ne pas dépasser 100%
    currentScale = Math.max(currentScale, 0.1); // Minimum 10%
  }
  
  // Centrer après un court délai pour s'assurer que le DOM est prêt
  setTimeout(() => {
    centerCartography();
  }, 50);

  console.log(`SVG configuré: ${svgWidth}x${svgHeight}, scale initial: ${Math.round(currentScale * 100)}%, ${clickableElements.size} activités`);
}

/* ============================================================
   ACTIVATION DES CLICS SUR LES ACTIVITÉS
============================================================ */
function activateSvgClicks() {
  if (!svgElement) {
    console.error("[CARTO] svgElement est null, impossible d'activer les clics");
    return;
  }

  console.log("[CARTO] === DÉBUT ACTIVATION DES CLICS ===");
  console.log("[CARTO] SHAPE_ACTIVITY_MAP reçu:", SHAPE_ACTIVITY_MAP);
  console.log("[CARTO] Nombre d'entrées dans le map:", Object.keys(SHAPE_ACTIVITY_MAP).length);

  const allElements = svgElement.querySelectorAll("*");
  console.log("[CARTO] Nombre total d'éléments dans le SVG:", allElements.length);

  // Chercher tous les attributs qui pourraient contenir un ID
  let foundMids = [];
  let elementsWithVisioAttr = 0;

  allElements.forEach((el) => {
    // Méthode 1: Namespace Visio standard
    let mid = el.getAttributeNS(VISIO_NS, "mID");
    
    // Méthode 2: Attribut direct sans namespace
    if (!mid) {
      mid = el.getAttribute("v:mID");
    }
    
    // Méthode 3: Attribut data-mid
    if (!mid) {
      mid = el.getAttribute("data-mid");
    }
    
    // Méthode 4: Chercher dans tous les attributs
    if (!mid) {
      for (let attr of el.attributes || []) {
        if (attr.name.toLowerCase().includes("mid") || attr.name.toLowerCase().includes("shapeid")) {
          mid = attr.value;
          console.log(`[CARTO] Trouvé attribut alternatif: ${attr.name}=${attr.value} sur`, el.tagName);
          break;
        }
      }
    }

    if (mid) {
      foundMids.push(mid);
      elementsWithVisioAttr++;
    }

    if (!mid) return;

    const activityId = SHAPE_ACTIVITY_MAP[mid];
    
    if (!activityId) {
      // Log uniquement les premiers pour ne pas spammer
      if (foundMids.length <= 10) {
        console.log(`[CARTO] mID="${mid}" trouvé mais pas dans SHAPE_ACTIVITY_MAP`);
      }
      return;
    }

    console.log(`[CARTO] ✓ Activité trouvée: mID="${mid}" → activityId=${activityId}`, el.tagName);

    // Marquer comme cliquable
    clickableElements.add(el);
    el.dataset.activityId = activityId;
    el.dataset.mid = mid;

    // Style
    el.style.cursor = "pointer";
    el.classList.add("carto-activity");

    // Effets au survol
    el.addEventListener("mouseenter", () => {
      console.log(`[CARTO] Survol activité ${activityId}`);
      el.style.filter = "drop-shadow(0 0 8px #22c55e)";
      el.style.opacity = "0.85";
    });

    el.addEventListener("mouseleave", () => {
      el.style.filter = "";
      el.style.opacity = "1";
    });

    // Clic sur l'activité
    el.addEventListener("click", (e) => {
      console.log(`[CARTO] CLICK sur activité ${activityId}, hasMoved=${hasMoved}`);
      
      // Ne naviguer que si on n'a pas fait de pan
      if (!hasMoved) {
        e.stopPropagation();
        e.preventDefault();
        const url = `/activities/view?activity_id=${activityId}`;
        console.log(`[CARTO] Navigation vers: ${url}`);
        window.location.href = url;
      } else {
        console.log(`[CARTO] Navigation annulée car hasMoved=true`);
      }
    });
  });

  console.log("[CARTO] === RÉSUMÉ ===");
  console.log(`[CARTO] Éléments avec attribut mID trouvés: ${elementsWithVisioAttr}`);
  console.log(`[CARTO] mIDs uniques trouvés:`, [...new Set(foundMids)].slice(0, 20));
  console.log(`[CARTO] Activités cliquables configurées: ${clickableElements.size}`);
  
  if (clickableElements.size === 0) {
    console.warn("[CARTO] ⚠️ AUCUNE ACTIVITÉ CLIQUABLE ! Vérifiez:");
    console.warn("[CARTO] 1. Le SVG contient-il des attributs v:mID ou similaires ?");
    console.warn("[CARTO] 2. SHAPE_ACTIVITY_MAP contient-il les bons mID ?");
    console.warn("[CARTO] mIDs dans le SVG:", foundMids.slice(0, 30));
    console.warn("[CARTO] mIDs attendus:", Object.keys(SHAPE_ACTIVITY_MAP));
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
   POPUP & OUTILS
============================================================ */
function initPopup() {
  const popup = document.getElementById("carto-actions-popup");
  const btnOpen = document.getElementById("carto-actions-btn");
  const btnClose = document.getElementById("close-popup");

  if (!popup || !btnOpen || !btnClose) return;

  btnOpen.onclick = () => popup.classList.remove("hidden");
  btnClose.onclick = () => popup.classList.add("hidden");

  // Fermer en cliquant sur le fond
  popup.addEventListener("click", (e) => {
    if (e.target === popup) {
      popup.classList.add("hidden");
    }
  });
}

function initReloadButton() {
  const btn = document.getElementById("reload-carto-btn");
  if (!btn) return;

  btn.onclick = () => {
    btn.textContent = "⏳ Mise à jour…";
    btn.disabled = true;
    fetch("/activities/update-cartography").then(() =>
      window.location.reload()
    );
  };
}

function initDropzone() {
  const zone = document.getElementById("dropzone");
  const status = document.getElementById("dropzone-status");
  if (!zone || !status) return;

  // Clic pour ouvrir le sélecteur de fichiers
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = ".svg,.vsdx";
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  zone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (file) {
      await uploadFile(file, status);
    }
  });

  // Drag & drop
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
    if (file) {
      await uploadFile(file, status);
    }
  });
}

async function uploadFile(file, status) {
  const fileName = file.name.toLowerCase();
  const isVsdx = fileName.endsWith(".vsdx");
  const isSvg = fileName.endsWith(".svg");
  
  if (!isVsdx && !isSvg) {
    status.innerHTML = "❌ Format invalide — fichiers .SVG ou .VSDX acceptés";
    status.className = "dropzone-status error";
    return;
  }

  if (isVsdx) {
    status.innerHTML = "⏳ Upload et conversion en cours...<br><small>(La conversion VSDX peut échouer, préférez SVG)</small>";
  } else {
    status.innerHTML = "⏳ Upload en cours...";
  }
  status.className = "dropzone-status loading";

  const form = new FormData();
  form.append("file", file);

  try {
    const res = await fetch("/activities/upload-carto", {
      method: "POST",
      body: form,
    });

    const data = await res.json();

    if (data.error) {
      status.innerHTML = "❌ " + data.error;
      status.className = "dropzone-status error";
      return;
    }

    status.innerHTML = "✓ Cartographie installée — rechargement...";
    status.className = "dropzone-status success";
    setTimeout(() => window.location.reload(), 1200);

  } catch (error) {
    status.innerHTML = "❌ Erreur réseau";
    status.className = "dropzone-status error";
  }
}

function initHistoryLoad() {
  document.querySelectorAll(".history-item").forEach((item) => {
    item.addEventListener("click", () => {
      const filename = item.dataset.file;
      if (!filename) return;
      
      item.textContent = "⏳ Chargement...";
      window.location.href = `/activities/use-carto/${filename}`;
    });
  });
}

/* ============================================================
   INITIALISATION GLOBALE
============================================================ */
document.addEventListener("DOMContentLoaded", async () => {
  console.log("[CARTO] ========================================");
  console.log("[CARTO] Initialisation de la cartographie");
  console.log("[CARTO] SHAPE_ACTIVITY_MAP:", SHAPE_ACTIVITY_MAP);
  console.log("[CARTO] SVG_EXISTS:", SVG_EXISTS);
  console.log("[CARTO] ========================================");

  // Initialiser les contrôles UI
  initListClicks();
  initPopup();
  initReloadButton();
  initDropzone();
  initHistoryLoad();

  // Initialiser pan et zoom
  initPan();
  initWheelZoom();

  // Charger le SVG inline
  await loadSvgInline();
  
  console.log("[CARTO] Initialisation terminée");
});


/* ============================================================
   FORMATAGE DES DATES DE L’HISTORIQUE
============================================================ */
function formatHistoryDates() {
  document.querySelectorAll(".history-date").forEach(span => {
    const raw = span.textContent.trim(); // ex: 20251201_124734

    if (/^\d{8}_\d{6}$/.test(raw)) {
      const year = raw.substring(0, 4);
      const month = raw.substring(4, 6);
      const day = raw.substring(6, 8);
      const hour = raw.substring(9, 11);
      const min = raw.substring(11, 13);

      const formatted = `${day}/${month}/${year} • ${hour}h${min}`;
      span.textContent = formatted;
    }
  });
}

document.addEventListener("DOMContentLoaded", formatHistoryDates);
