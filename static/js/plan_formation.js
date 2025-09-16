// Code/static/js/plan_formation.js

/* ====== Utilitaires DOM & UI ====== */
function $(sel, ctx = document) { return ctx.querySelector(sel); }
function $all(sel, ctx = document) { return Array.from(ctx.querySelectorAll(sel)); }
function toast(msg, kind = "success") {
  const t = document.createElement("div");
  t.className = `toast ${kind}`;
  t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add("show"));
  setTimeout(() => { t.classList.remove("show"); t.addEventListener("transitionend", () => t.remove()); }, 2200);
}

/* ====== Overlay plein écran (chargement) ====== */
function showPageLoader(label = "Chargement…") {
  const el = document.getElementById("page-loader");
  if (!el) return;
  const l = el.querySelector(".label");
  if (l) l.textContent = label;
  el.classList.remove("hidden");
}
function hidePageLoader() {
  const el = document.getElementById("page-loader");
  if (!el) return;
  el.classList.add("hidden");
}

/* ====== Endpoints ====== */
const ACTIVITY_ITEMS_URL = "/your_api/activity_items/";
const SAVE_PREREQUIS_URL = "/competences_plan/save_prerequis";
const GENERATE_PLAN_URL  = "/competences_plan/generate_plan";
const GET_PREREQUIS_URL  = (userId, activityId) => `/competences_plan/get_prerequis/${userId}/${activityId}`;

/* ====== Helpers API ====== */
async function apiGet(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}
async function apiPost(url, payload) {
  const r = await fetch(url, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload) });
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try { const txt = await r.text(); if (txt) msg = txt; } catch {}
    throw new Error(msg);
  }
  return r.json();
}

/* ====== Contexte page ====== */
function getSelectedUserId() {
  const el = document.getElementById("collaborator-select");
  return el ? Number(el.value) : null;
}
function getRoleIdFromCard(card)     { return Number(card.dataset.roleId); }
function getActivityIdFromCard(card) { return Number(card.dataset.activityId); }

/* ====== Boutons : états (+ spinner intégré via .is-loading) ====== */
function setButtonsState(card, state /* "idle" | "loading" | "ready" */) {
  const btnLoad = card.querySelector('[data-action="load-prerequis"]');
  const btnSave = card.querySelector('[data-action="save-prerequis"]');
  const btnGen  = card.querySelector('[data-action="save-and-generate"]');

  const set = (b, dis, loading=false) => {
    if (!b) return;
    b.disabled = dis;
    b.classList.toggle("is-loading", !!loading);
  };

  if (state === "loading") {
    set(btnLoad, true,  true);
    set(btnSave, true,  true);
    set(btnGen,  true,  true);
  } else if (state === "ready") {
    set(btnLoad, false, false);
    set(btnSave, false, false);
    set(btnGen,  false, false);
  } else { // idle
    set(btnLoad, false, false);
    set(btnSave, true,  false);
    set(btnGen,  true,  false);
  }
}

function renderEmptyBody(bodyEl, message = "Clique sur « Afficher les items » pour charger la liste.") {
  bodyEl.innerHTML = `<tr><td colspan="3" class="muted">${message}</td></tr>`;
}

/* ====== Charger les items (S/SF/HSC) ====== */
async function ensurePrerequisRows(card, force = false) {
  const body = card.querySelector(".prerequis-body");
  const already = body.dataset.filled === "1";
  if (already && !force) { setButtonsState(card, "ready"); return; }

  const activityId = getActivityIdFromCard(card);
  if (!activityId) { toast("Activité introuvable.", "error"); return; }

  setButtonsState(card, "loading");
  try {
    const data = await apiGet(`${ACTIVITY_ITEMS_URL}${activityId}`);
    const rows = [];
    const pushRows = (list, typeLabel, typeKey) => {
      (list || []).forEach(it => {
        const display = it.name || it.description || `#${it.id}`;
        rows.push(`
          <tr data-item-type="${typeKey}" data-item-id="${it.id}">
            <td class="item-name">${display}</td>
            <td class="item-type">${typeLabel}</td>
            <td>
              <textarea class="prerequis-comment" placeholder="Ex.: prérequis manquants, autonomie, besoin de compagnonnage…"></textarea>
            </td>
          </tr>
        `);
      });
    };

    pushRows(data.savoirs, "Savoir", "savoir");
    pushRows(data.savoir_faire, "Savoir-faire", "savoir_faire");
    pushRows(data.hsc, "HSC", "hsc");

    if (rows.length === 0) {
      renderEmptyBody(body, "Aucun item lié à cette activité.");
      body.dataset.filled = "1";
      setButtonsState(card, "ready");
      return;
    }

    body.innerHTML = rows.join("");
    body.dataset.filled = "1";
    setButtonsState(card, "ready");

    // Pré-remplir avec les commentaires déjà enregistrés (si existants)
    await loadPrerequis(card);
    toast("Items chargés.");
  } catch (e) {
    renderEmptyBody(body, "Impossible de charger les items (vérifie la route /your_api/activity_items).");
    setButtonsState(card, "idle");
    toast(`Erreur chargement : ${e.message}`, "error");
  }
}

/* ====== Lecture/Sauvegarde des commentaires ====== */
async function loadPrerequis(card) {
  const userId = getSelectedUserId();
  if (!userId) { return; } // silencieux (on peut d'abord choisir un collaborateur)

  const activityId = getActivityIdFromCard(card);
  const r = await fetch(GET_PREREQUIS_URL(userId, activityId));
  if (!r.ok) return; // pas encore de données
  const data = await r.json(); // [{item_type,item_id,comment}]
  const map = new Map(data.map(d => [`${d.item_type}:${d.item_id}`, d.comment || ""]));

  $all("tbody.prerequis-body tr", card).forEach(tr => {
    const key = `${tr.dataset.itemType}:${tr.dataset.itemId}`;
    const ta = tr.querySelector("textarea.prerequis-comment");
    if (map.has(key)) ta.value = map.get(key);
  });
}

async function savePrerequis(card) {
  const userId = getSelectedUserId();
  if (!userId) { toast("Sélectionne d’abord un collaborateur.", "error"); return; }

  const body = card.querySelector(".prerequis-body");
  if (!body || !body.children.length) { toast("Charge d’abord les items.", "error"); return; }

  const activityId = getActivityIdFromCard(card);
  const comments = $all("tbody.prerequis-body tr", card).map(tr => ({
    item_type: tr.dataset.itemType,
    item_id: Number(tr.dataset.itemId),
    comment: tr.querySelector("textarea.prerequis-comment").value.trim()
  }));

  setButtonsState(card, "loading");
  try {
    await apiPost(SAVE_PREREQUIS_URL, { user_id: userId, activity_id: activityId, comments });
    // IMPORTANT : ne re-écrase pas le DOM (on ne rappelle pas ensurePrerequisRows ici)
    // Recharge uniquement les valeurs (si le serveur les a bien enregistrées)
    await loadPrerequis(card);
    toast("Commentaires enregistrés.");
  } catch (e) {
    toast(`Erreur enregistrement : ${e.message}`, "error");
  } finally {
    setButtonsState(card, "ready");
  }
}

/* ====== Générer le plan ====== */
function getEvaluationsForActivity(activityId) {
  return (window.__evalByActivity && window.__evalByActivity[activityId]) || {};
}
function collectPrerequisComments(card) {
  return $all("tbody.prerequis-body tr", card).map(tr => ({
    item_type: tr.dataset.itemType,
    item_id: Number(tr.dataset.itemId),
    comment: tr.querySelector("textarea.prerequis-comment").value.trim()
  }));
}

async function saveAndGenerate(card) {
  const userId = getSelectedUserId();
  if (!userId) { toast("Sélectionne d’abord un collaborateur.", "error"); return; }

  // S'assurer que les items sont chargés une fois
  await ensurePrerequisRows(card);

  // 1) Sauvegarder (sans vider)
  await savePrerequis(card);

  // 2) Construire le contexte
  const roleId = getRoleIdFromCard(card);
  const activityId = getActivityIdFromCard(card);
  const payload_contexte = {
    role: window.__roleContext?.[roleId] || { id: roleId },
    activity: window.__activityContext?.[activityId] || { id: activityId },
    evaluations: getEvaluationsForActivity(activityId),
    prerequis_comments: collectPrerequisComments(card)
  };

  // 3) UI : spinner local (bouton) + overlay plein écran
  const btnGen = card.querySelector('[data-action="save-and-generate"]');
  if (btnGen) { btnGen.classList.add("is-loading"); btnGen.disabled = true; }
  showPageLoader("Génération du plan…");

  try {
    const res = await apiPost(GENERATE_PLAN_URL, {
      user_id: userId, role_id: roleId, activity_id: activityId, payload_contexte
    });
    if (!res.ok) throw new Error(res.error || "Réponse invalide.");
    renderPlanModal(res.plan);
  } catch (e) {
    toast(`Erreur génération du plan : ${e.message}`, "error");
  } finally {
    hidePageLoader();
    if (btnGen) { btnGen.classList.remove("is-loading"); btnGen.disabled = false; }
  }
}

/* ====== Modale ====== */
function escapeHtml(s){return String(s||"").replace(/[&<>"']/g,m=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;" }[m]));}
function renderPlanModal(plan) {
  const modal = document.getElementById("plan-modal");
  const box = document.getElementById("plan-modal-content");

  const axesHtml = (plan.axes || []).map(ax => {
    const parcours = (ax.parcours || []).map(p => `
      <li>
        <strong>Option :</strong> ${escapeHtml(p.option||"")} —
        <strong>Méthodes :</strong> ${(p.methodes||[]).map(escapeHtml).join(", ")} —
        <strong>Durée :</strong> ${p.duree_estimee_heures ?? "?"} h<br/>
        <strong>Livrables :</strong> ${(p.livrables_attendus||[]).map(escapeHtml).join(", ")}<br/>
        <strong>Critères :</strong> ${(p.criteres_de_validation||[]).map(escapeHtml).join(", ")}
      </li>
    `).join("");

    const jalons = (ax.jalons || []).map(j => `<li>S${j.semaine} — ${escapeHtml(j.verif||"")}</li>`).join("");

    return `
      <section class="plan-axe">
        <h4>${escapeHtml(ax.intitule||"Axe")}</h4>
        <p class="muted">${escapeHtml(ax.justification||"")}</p>
        <h5>Objectifs pédagogiques</h5>
        <ul>${(ax.objectifs_pedagogiques||[]).map(o=>`<li>${escapeHtml(o)}</li>`).join("")}</ul>
        <h5>Parcours</h5>
        <ul>${parcours || "<li>—</li>"}</ul>
        <h5>Jalons</h5>
        <ul>${jalons || "<li>—</li>"}</ul>
      </section>
    `;
  }).join("");

  box.innerHTML = `
    <div class="plan-head" style="display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;">
      <span class="badge">${escapeHtml(plan.type||"PLAN")}</span>
      <div class="muted">
        <strong>Activité :</strong> ${escapeHtml(plan.contexte_synthetique?.activite || "")}<br/>
        <strong>Perf. cibles :</strong> ${(plan.contexte_synthetique?.performances_cibles||[]).map(escapeHtml).join(", ")}
      </div>
    </div>
    ${axesHtml || '<p class="muted">Aucun axe détaillé.</p>'}
    <div class="plan-synthese" style="margin-top:10px;">
      <strong>Charge estimée :</strong> ${(plan.synthese_charge?.duree_totale_estimee_heures ?? "?")} h –
      <strong>Impact :</strong> ${escapeHtml(plan.synthese_charge?.impact_organisation || "?")}<br/>
      <em>${escapeHtml(plan.synthese_charge?.recommandation_globale || "")}</em>
    </div>
  `;

  modal.classList.remove("hidden");
}

/* ====== Delegation clics ====== */
document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-action]");
  if (btn) {
    const card = e.target.closest(".prerequis-card");
    const action = btn.dataset.action;

    if (action === "load-prerequis") {
      ensurePrerequisRows(card).catch(err => toast(err.message, "error"));
      return;
    }
    if (action === "save-prerequis") {
      ensurePrerequisRows(card).then(()=>savePrerequis(card)).catch(err => toast(err.message, "error"));
      return;
    }
    if (action === "save-and-generate") {
      ensurePrerequisRows(card).then(()=>saveAndGenerate(card)).catch(err => toast(err.message, "error"));
      return;
    }
  }

  if (e.target.matches("[data-modal-close]") || e.target.closest("[data-modal-close]")) {
    e.preventDefault();
    const m = e.target.closest(".modal");
    if (m) m.classList.add("hidden");
  }
});
