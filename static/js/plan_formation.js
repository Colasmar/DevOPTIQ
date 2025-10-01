// Code/static/js/plan_formation.js

/* ====== Utilitaires DOM & UI ====== */
function $(sel, ctx = document) { return ctx.querySelector(sel); }
function $all(sel, ctx = document) { return Array.from(ctx.querySelectorAll(sel)); }
function normText(n) { return (n?.textContent || "").trim().toLowerCase(); }
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
const ACTIVITY_ITEMS_URL = "/your_api/activity_items/";              // renvoie {savoirs:[], savoir_faire:[], hsc:[]}
const SAVE_PREREQUIS_URL = "/competences_plan/save_prerequis";
const GENERATE_PLAN_URL  = "/competences_plan/generate_plan";
const GET_PREREQUIS_URL  = (userId, activityId) => `/competences_plan/get_prerequis/${userId}/${activityId}`;

// -> Endpoints Plan
const SAVE_PLAN_URL = "/competences_plan/save_plan";
const GET_PLAN_URL  = (userId, activityId) => `/competences_plan/get_plan/${userId}/${activityId}`;

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
  const btnLoad = card.querySelector('[data-action="load-prerequis"]'); // supprimé si présent
  const btnSave = card.querySelector('[data-action="save-prerequis"]');
  const btnGen  = card.querySelector('[data-action="save-and-generate"]');
  const btnView = card.querySelector('[data-action="view-saved-plan"]');

  const set = (b, dis, loading=false) => {
    if (!b) return;
    b.disabled = dis;
    b.classList.toggle("is-loading", !!loading);
  };

  if (state === "loading") {
    set(btnLoad, true,  true);
    set(btnSave, true,  true);
    set(btnGen,  true,  true);
    set(btnView, true,  true);
  } else if (state === "ready") {
    set(btnLoad, false, false);
    set(btnSave, false, false);
    set(btnGen,  false, false);
    set(btnView, false, false);
  } else { // idle
    set(btnLoad, false, false);
    set(btnSave, true,  false);
    set(btnGen,  true,  false);
    set(btnView, false, false);
  }
}

function renderEmptyBody(bodyEl, message = "Aucun item à afficher pour cette activité.") {
  bodyEl.innerHTML = `<tr><td colspan="3" class="muted">${message}</td></tr>`;
}

/* ====== Loader d’items (S/SF/HSC) ====== */
async function ensurePrerequisRows(card, { force = false, silent = false } = {}) {
  const body = card.querySelector(".prerequis-body");
  if (!body) return;

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

    // Pré-remplir les commentaires existants
    await loadPrerequis(card);
    if (!silent) toast("Items chargés.");
  } catch (e) {
    renderEmptyBody(body, "Impossible de charger les items (vérifie la route /your_api/activity_items).");
    setButtonsState(card, "idle");
    toast(`Erreur chargement : ${e.message}`, "error");
  }
}

/* ====== Lecture/Sauvegarde des commentaires ====== */
async function loadPrerequis(card) {
  const userId = getSelectedUserId();
  if (!userId) { return; } // silencieux

  const body = card.querySelector(".prerequis-body");
  if (!body) return;

  const activityId = getActivityIdFromCard(card);
  const r = await fetch(GET_PREREQUIS_URL(userId, activityId));
  if (!r.ok) return;
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
  if (!body || !body.children.length) { toast("Les items ne sont pas encore chargés.", "error"); return; }

  const activityId = getActivityIdFromCard(card);
  const comments = $all("tbody.prerequis-body tr", card).map(tr => ({
    item_type: tr.dataset.itemType,
    item_id: Number(tr.dataset.itemId),
    comment: tr.querySelector("textarea.prerequis-comment").value.trim()
  }));

  setButtonsState(card, "loading");
  try {
    await apiPost(SAVE_PREREQUIS_URL, { user_id: userId, activity_id: activityId, comments });
    await loadPrerequis(card);
    toast("Commentaires enregistrés.");
  } catch (e) {
    toast(`Erreur enregistrement : ${e.message}`, "error");
  } finally {
    setButtonsState(card, "ready");
  }
}

/* ====== Générer / Voir / Enregistrer un plan ====== */
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

  await ensurePrerequisRows(card, { force: false, silent: true });
  await savePrerequis(card);

  const roleId = getRoleIdFromCard(card);
  const activityId = getActivityIdFromCard(card);
  const payload_contexte = {
    role: window.__roleContext?.[roleId] || { id: roleId },
    activity: window.__activityContext?.[activityId] || { id: activityId },
    evaluations: getEvaluationsForActivity(activityId),
    prerequis_comments: collectPrerequisComments(card)
  };

  const btnGen = card.querySelector('[data-action="save-and-generate"]');
  if (btnGen) { btnGen.classList.add("is-loading"); btnGen.disabled = true; }
  showPageLoader("Génération du plan…");

  try {
    const res = await apiPost(GENERATE_PLAN_URL, {
      user_id: userId, role_id: roleId, activity_id: activityId, payload_contexte
    });
    const plan = res.plan || res; // tolérant
    renderPlanModal(plan, { mode: "generated", userId, roleId, activityId });
  } catch (e) {
    toast(`Erreur génération du plan : ${e.message}`, "error");
  } finally {
    hidePageLoader();
    if (btnGen) { btnGen.classList.remove("is-loading"); btnGen.disabled = false; }
  }
}

async function viewSavedPlan(card) {
  const userId = getSelectedUserId();
  if (!userId) { toast("Sélectionne d’abord un collaborateur.", "error"); return; }
  const activityId = getActivityIdFromCard(card);

  try {
    const res = await apiGet(GET_PLAN_URL(userId, activityId));
    if (!res.ok) throw new Error(res.error || "Réponse invalide");
    renderPlanModal(res.plan, { mode: "saved", userId, roleId: res.meta?.role_id, activityId });
  } catch (e) {
    toast("Aucun plan enregistré pour cette activité.", "error");
  }
}

/* ====== Modales : plan & confirmation remplacement ====== */
function ensurePlanModalShell() {
  let modal = document.getElementById('plan-modal');

  const templateInner = `
    <div class="modal__panel">
      <div class="modal__head">
        <h3>Plan de formation</h3>
        <button class="modal__close" data-modal-close>&times;</button>
      </div>
      <div id="plan-modal-content" class="modal__body"></div>
      <div id="plan-modal-foot" class="modal__foot"></div>
    </div>
  `;

  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'plan-modal';
    modal.className = 'modal hidden';
    modal.innerHTML = templateInner;
    document.body.appendChild(modal);
    return modal;
  }

  modal.classList.add('modal');
  const content = modal.querySelector('#plan-modal-content');
  const foot    = modal.querySelector('#plan-modal-foot');
  if (!content || !foot) {
    modal.innerHTML = templateInner;
  }
  return modal;
}

function ensureReplaceConfirmModal() {
  let modal = document.getElementById('plan-replace-modal');
  const inner = `
    <div class="modal__panel modal__panel--sm">
      <div class="modal__head">
        <h3>Remplacer le plan ?</h3>
        <button class="modal__close" data-modal-close>&times;</button>
      </div>
      <div id="plan-replace-content" class="modal__body">
        <p class="muted">Vous avez déjà un plan défini pour cette activité. Souhaitez-vous le remplacer par le nouveau ?</p>
      </div>
      <div id="plan-replace-foot" class="modal__foot" style="justify-content:flex-end; gap:10px;">
        <button class="btn btn-light" data-confirm-replace="no">Non</button>
        <button class="btn btn-emerald" data-confirm-replace="yes">Oui, remplacer</button>
      </div>
    </div>
  `;
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'plan-replace-modal';
    modal.className = 'modal modal--sm hidden';
    modal.innerHTML = inner;
    document.body.appendChild(modal);
  } else {
    // s’assurer que la structure est correcte
    if (!modal.querySelector('#plan-replace-foot')) modal.innerHTML = inner;
  }
  return modal;
}

function openReplaceConfirm(onYes, onNo) {
  const modal = ensureReplaceConfirmModal();
  const foot  = modal.querySelector('#plan-replace-foot');
  const btnYes = foot.querySelector('[data-confirm-replace="yes"]');
  const btnNo  = foot.querySelector('[data-confirm-replace="no"]');

  // Nettoyage handlers précédents
  btnYes.onclick = null;
  btnNo.onclick  = null;

  btnYes.onclick = () => { try { onYes?.(); } finally { modal.classList.add('hidden'); } };
  btnNo.onclick  = () => { try { onNo?.();  } finally { modal.classList.add('hidden'); } };

  modal.classList.remove('hidden');
}

/* ====== Construction HTML plan & rendu ====== */
function escapeHtml(s){return String(s||"").replace(/[&<>"']/g,m=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;" }[m]));}

function buildPlanHtml(plan) {
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

  return `
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
}

function renderPlanModal(plan, { mode = "generated", userId, roleId, activityId } = {}) {
  const modal = ensurePlanModalShell();
  let box  = modal.querySelector('#plan-modal-content');
  let foot = modal.querySelector('#plan-modal-foot');

  if (!box || !foot) {
    modal.innerHTML = `
      <div class="modal__panel">
        <div class="modal__head">
          <h3>Plan de formation</h3>
          <button class="modal__close" data-modal-close>&times;</button>
        </div>
        <div id="plan-modal-content" class="modal__body"></div>
        <div id="plan-modal-foot" class="modal__foot"></div>
      </div>
    `;
    box  = modal.querySelector('#plan-modal-content');
    foot = modal.querySelector('#plan-modal-foot');
  }

  box.innerHTML = buildPlanHtml(plan);

  foot.innerHTML = "";
  if (mode === "generated") {
    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-primary';
    saveBtn.textContent = 'Enregistrer ce plan';
    saveBtn.addEventListener('click', () => savePlanFlow(plan, { userId, roleId, activityId }));

    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-light';
    closeBtn.textContent = 'Fermer';
    closeBtn.setAttribute('data-modal-close', '1');

    foot.appendChild(saveBtn);
    foot.appendChild(closeBtn);
  } else {
    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-light';
    closeBtn.textContent = 'Fermer';
    closeBtn.setAttribute('data-modal-close', '1');
    foot.appendChild(closeBtn);
  }

  modal.classList.remove("hidden");
}

function enableViewPlanButton(activityId){
  const card = document.querySelector(`.prerequis-card[data-activity-id="${activityId}"]`);
  const viewBtn = card ? card.querySelector('[data-action="view-saved-plan"]') : null;
  if (viewBtn) viewBtn.disabled = false;
}

async function savePlanFlow(plan, { userId, roleId, activityId }) {
  try {
    const r = await fetch(SAVE_PLAN_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, activity_id: activityId, role_id: roleId, plan })
    });
    if (r.status === 409) {
      // Ouvrir la petite modale de confirmation (séparée)
      openReplaceConfirm(async () => {
        try {
          const res = await apiPost(SAVE_PLAN_URL, { user_id: userId, activity_id: activityId, role_id: roleId, plan, force: true });
          if (res.ok) {
            toast("Plan enregistré (remplacé).");
            enableViewPlanButton(activityId);
          } else {
            throw new Error(res.error || "Échec remplacement");
          }
        } catch (err) {
          toast(`Erreur: ${err.message}`, "error");
        }
      }, () => {
        // Annulé : rien à faire
      });
      return;
    }
    if (!r.ok) {
      const txt = await r.text();
      throw new Error(txt || `${r.status} ${r.statusText}`);
    }
    const data = await r.json();
    if (data.ok) {
      toast("Plan enregistré.");
      enableViewPlanButton(activityId);
    } else {
      throw new Error(data.error || "Réponse invalide.");
    }
  } catch (e) {
    toast(`Erreur enregistrement du plan : ${e.message}`, "error");
  }
}

/* ====== Délégation (modales & actions) ====== */
document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-action]");
  if (btn) {
    const card = e.target.closest(".prerequis-card");
    const action = btn.dataset.action;

    if (action === "load-prerequis") {
      ensurePrerequisRows(card, { force: true, silent: false }).catch(err => toast(err.message, "error"));
      return;
    }
    if (action === "save-prerequis") {
      ensurePrerequisRows(card, { force: false, silent: true }).then(()=>savePrerequis(card)).catch(err => toast(err.message, "error"));
      return;
    }
    if (action === "save-and-generate") {
      ensurePrerequisRows(card, { force: false, silent: true }).then(()=>saveAndGenerate(card)).catch(err => toast(err.message, "error"));
      return;
    }
    if (action === "view-saved-plan") {
      viewSavedPlan(card).catch(err => toast(err.message, "error"));
      return;
    }
  }

  if (e.target.matches("[data-modal-close]") || e.target.closest("[data-modal-close]")) {
    e.preventDefault();
    const m = e.target.closest(".modal");
    if (m) m.classList.add("hidden");
  }
});

/* ====== Amélioration progressive + Observer ======
   - Auto-charge les items (4 visibles par défaut) + toggle "Tout afficher / Réduire"
   - Retire "Afficher items" du header, descend "Enregistrer ..." en bas à droite
   - Ajoute un bouton "Voir le plan"
*/
(function(){
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));
  const MAX_INIT = 4;

  async function enhanceCard(card){
    if (!card || card.classList.contains('prerequis--enhanced')) return;

    const wrapper = $('.prerequis-table-wrapper', card) || card;
    const table   = $('.prerequis-table', card);
    const tbody   = table ? (table.tBodies[0] || $('.prerequis-body', card)) : $('.prerequis-body', card);
    if (!tbody) return;

    // 0) Charger immédiatement les items (puis pré-remplir)
    await ensurePrerequisRows(card, { force: true, silent: true });

    // 1) Zone scrollable + clamp 4 lignes
    card.classList.add('prerequis--enhanced');
    card.classList.add('prerequis-enhanced'); // compat CSS
    wrapper.classList.add('prerequis-scrollable');

    const rows = Array.from(tbody.querySelectorAll('tr'));
    let expanded = false;
    const applyRowClamp = () => {
      rows.forEach((tr, idx) => {
        tr.style.display = (!expanded && idx >= MAX_INIT) ? 'none' : '';
      });
    };
    applyRowClamp();

    // 2) Barre d’outils "Tout afficher / Réduire"
    let topbar = $('.prerequis-topbar', card);
    if (!topbar) {
      topbar = document.createElement('div');
      topbar.className = 'prerequis-topbar';

      const btnToggle = document.createElement('button');
      btnToggle.type = 'button';
      btnToggle.className = 'btn btn-light btn-toggle-all';
      btnToggle.textContent = 'Tout afficher';
      btnToggle.addEventListener('click', () => {
        expanded = !expanded;
        applyRowClamp();
        btnToggle.textContent = expanded ? 'Réduire' : 'Tout afficher';
      });

      topbar.appendChild(btnToggle);
      wrapper.parentNode.insertBefore(topbar, wrapper);
    }

    // 3) Déplacer boutons "Enregistrer ..." en bas + ajouter "Voir le plan"
    const header = $('.prerequis-card__header', card);
    const headerActions = $('.prerequis-card__actions', card) || (header ? header : card);
    if (headerActions) {
      let bottom = $('.prerequis-actions-bottom', card);
      if (!bottom) {
        bottom = document.createElement('div');
        bottom.className = 'prerequis-actions-bottom';
      }

      const children = Array.from(headerActions.querySelectorAll('button, a'));
      children.forEach(node => {
        const txt = normText(node);
        const isLoad  = node.matches('[data-action="load-prerequis"]') || txt.includes('afficher');
        const isSave  = node.matches('[data-action="save-prerequis"]') || txt.includes('enregistrer');
        const isGen   = node.matches('[data-action="save-and-generate"]') || txt.includes('générer');

        if (isLoad) {
          node.remove(); // supprimer "Afficher items"
        } else if (isSave || isGen) {
          bottom.appendChild(node);
        }
      });

      // Ajouter le bouton "Voir le plan" s'il n'existe pas
      if (!bottom.querySelector('[data-action="view-saved-plan"]')) {
        const viewBtn = document.createElement('button');
        viewBtn.type = 'button';
        viewBtn.className = 'btn btn-light';
        viewBtn.dataset.action = 'view-saved-plan';
        viewBtn.textContent = 'Voir le plan';
        bottom.appendChild(viewBtn);
      }

      if (bottom.children.length && !bottom.parentNode) {
        if (wrapper.nextSibling) {
          wrapper.parentNode.insertBefore(bottom, wrapper.nextSibling);
        } else {
          wrapper.parentNode.appendChild(bottom);
        }
      }

      // Masquer les actions du header
      if (headerActions.classList.contains('prerequis-card__actions')) {
        headerActions.style.display = 'none';
        headerActions.setAttribute('aria-hidden', 'true');
      }
    }
  }

  function enhanceAllExisting(){
    $$('.prerequis-card').forEach(card => { enhanceCard(card); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', enhanceAllExisting);
  } else {
    enhanceAllExisting();
  }

  const obs = new MutationObserver(muts => {
    for (const m of muts) {
      for (const n of m.addedNodes) {
        if (!(n instanceof HTMLElement)) continue;
        if (n.matches && n.matches('.prerequis-card')) {
          enhanceCard(n);
        } else {
          $all('.prerequis-card', n).forEach(enhanceCard);
        }
      }
    }
  });
  obs.observe(document.body, { childList: true, subtree: true });
})();
