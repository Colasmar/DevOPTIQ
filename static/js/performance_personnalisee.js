// Code/static/js/performance_perso.js
(function () {

  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function escapeHtml(s){return (s||'').replace(/[&<>"']/g,c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function toast(message, type="success"){
    const el = document.getElementById("toast-message") || (()=>{const d=document.createElement('div');d.id='toast-message';d.className='toast';document.body.appendChild(d);return d;})();
    el.textContent = message;
    el.classList.remove("hidden","error","success");
    el.classList.add(type==="error"?"error":"success","show");
    setTimeout(()=>{el.classList.remove("show")}, 2200);
  }
  function formatDateFR(raw){
    if(!raw) return '';
    try{ const d = new Date(raw); if(!isNaN(d)) return d.toLocaleDateString('fr-FR'); }catch(e){}
    if(/^\d{4}-\d{2}-\d{2}$/.test(raw)){ const [y,m,d]=raw.split('-'); return `${d}/${m}/${y}`; }
    return raw;
  }
  async function http(method, url, body) {
    const opt = { method, headers: {} };
    if (body) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
    const r = await fetch(url, opt);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const ct = r.headers.get('Content-Type') || '';
    return ct.includes('application/json') ? r.json() : r.text();
  }

  // Public : inséré en tête de .activity-content
  window.insertPerformanceBlock = async function(activityId, mountEl) {
    const userId = Number(globalThis.selectedUserId || 0);
    if (!mountEl) return;

    let wrapper = mountEl.querySelector('.perf-wrapper');
    if (!wrapper) {
      wrapper = document.createElement('div');
      wrapper.className = 'perf-wrapper perf-card';
      wrapper.innerHTML = `
        <div class="perf-header">
          <div class="perf-title">
            <svg class="perf-icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M3 13h2v-2H3v2zm4 0h14v-2H7v2zm0 6h14v-2H7v2zM7 5v2h14V5H7z"/></svg>
            <span>Performances</span>
          </div>
          <div class="perf-actions">
            <button class="perf-btn perf-btn-outline btn-history">Historique</button>
            <button class="perf-btn perf-btn-primary btn-add-perf">+ Ajouter</button>
          </div>
        </div>
        <div class="perf-content">
          <div class="perf-general-container"></div>
          <div class="perf-personal-container"></div>
        </div>
      `;
      mountEl.appendChild(wrapper);
    }

    // 1) Performance générale (si link_id dispo)
    try {
      const activitySection = mountEl.closest('.activity-section');
      const linkId = activitySection ? activitySection.dataset.linkId : null;
      const genCtn = $('.perf-general-container', wrapper);
      if (linkId) {
        const htmlFrag = await http('GET', `/performance/render/${linkId}`);
        genCtn.innerHTML = `
          <div class="perf-subtitle">Performance générale</div>
          <div class="perf-general-fragment perf-box">${htmlFrag}</div>
        `;
      } else {
        genCtn.innerHTML = '';
      }
    } catch {
      $('.perf-general-container', wrapper).innerHTML = '';
    }

    // 2) Performances personnalisées
    const persoCtn = $('.perf-personal-container', wrapper);
    if (!userId) {
      persoCtn.innerHTML = `<div class="perf-empty"><em>Sélectionnez un collaborateur pour voir ses performances personnalisées.</em></div>`;
    } else {
      try {
        const items = await http('GET', `/performance_perso/list?user_id=${userId}&activity_id=${activityId}`);
        renderPersonalList(persoCtn, items);
      } catch (e) {
        console.error(e);
        persoCtn.innerHTML = `<div class="perf-empty">Erreur de chargement des performances personnalisées.</div>`;
      }
    }

    // 3) Actions header
    $('.btn-add-perf', wrapper).onclick = () => openEditorCreate(persoCtn, userId, activityId);
    $('.btn-history', wrapper).onclick = () => openHistoryModal(userId, activityId);
  };

  function renderPersonalList(container, list) {
    if (!Array.isArray(list) || !list.length) {
      container.innerHTML = `
        <div class="perf-subtitle">Performances personnalisées</div>
        <div class="perf-empty"><em>Aucune performance personnalisée pour cette activité.</em></div>`;
      return;
    }
    container.innerHTML = `
      <div class="perf-subtitle">Performances personnalisées</div>
      <div class="perf-items"></div>
    `;
    const itemsEl = $('.perf-items', container);
    itemsEl.innerHTML = list.map(renderItem).join('');
    itemsEl.querySelectorAll('.btn-edit').forEach(btn => btn.addEventListener('click', () => openEditorUpdate(btn.closest('.perf-item'))));
    itemsEl.querySelectorAll('.btn-apply-status').forEach(btn => btn.addEventListener('click', () => applyStatus(btn.closest('.perf-item'))));
  }

  function renderItem(p) {
    const statusTxt = (p.validation_status === 'validee') ? 'Validée' : 'Non-validée';
    const statusCls = (p.validation_status === 'validee') ? 'perf-badge-success' : 'perf-badge-muted';
    const dateTxt = p.validation_date ? formatDateFR(p.validation_date) : '';

    return `
      <div class="perf-item perf-box" data-id="${p.id}">
        <div class="perf-item-top">
          <div class="perf-badges">
            <span class="perf-badge ${statusCls}" data-role="status-label">${statusTxt}</span>
            <span class="perf-badge perf-badge-date" data-role="status-date" style="${dateTxt ? '' : 'display:none;'}">${dateTxt}</span>
          </div>
          <button class="perf-btn perf-btn-ghost btn-edit">Modifier</button>
        </div>
        <div class="perf-content-read">${escapeHtml(p.content || '')}</div>
        <div class="perf-item-actions">
          <label class="perf-radio"><input type="radio" name="perf-status-${p.id}" value="validee" ${p.validation_status === 'validee' ? 'checked' : ''}> Validée</label>
          <label class="perf-radio"><input type="radio" name="perf-status-${p.id}" value="non-validee" ${p.validation_status !== 'validee' ? 'checked' : ''}> Non-validée</label>
          <input type="date" class="perf-status-date" value="${p.validation_date || ''}">
          <button class="perf-btn perf-btn-primary btn-apply-status">Appliquer</button>
        </div>
      </div>
    `;
  }

  function openEditorCreate(container, userId, activityId) {
    if (!userId) return toast("Sélectionnez un collaborateur.", "error");
    const editor = document.createElement('div');
    editor.className = 'perf-editor perf-box';
    editor.innerHTML = `
      <textarea class="perf-contenu" rows="3" placeholder="Décris la performance..."></textarea>
      <div class="perf-edit-row">
        <label>Validation :</label>
        <select class="perf-validation-status">
          <option value="validee">Validée</option>
          <option value="non-validee" selected>Non-validée</option>
        </select>
        <label>Date :</label>
        <input type="date" class="perf-validation-date" value="${new Date().toISOString().slice(0,10)}"/>
      </div>
      <div class="perf-edit-actions">
        <button class="perf-btn perf-btn-primary btn-save">Créer</button>
        <button class="perf-btn perf-btn-outline btn-cancel">Annuler</button>
      </div>
    `;
    container.prepend(editor);

    $('.btn-cancel', editor).onclick = () => editor.remove();
    $('.btn-save', editor).onclick = async () => {
      const content = $('.perf-contenu', editor).value.trim();
      const validation_status = $('.perf-validation-status', editor).value;
      const validation_date = $('.perf-validation-date', editor).value || null;
      if (!content) return toast("Le texte de la performance est vide.", "error");
      try {
        await http('POST', '/performance_perso/create', { user_id: userId, activity_id, content, validation_status, validation_date });
        const items = await http('GET', `/performance_perso/list?user_id=${userId}&activity_id=${activityId}`);
        renderPersonalList(container, items);
        toast("Performance créée.");
      } catch (e) {
        console.error(e); toast("Erreur création.", "error");
      } finally {
        editor.remove();
      }
    };
  }

  function openEditorUpdate(itemEl) {
    const id = Number(itemEl.dataset.id);
    const read = itemEl.querySelector('.perf-content-read');
    const oldText = read?.textContent || '';

    read.outerHTML = `
      <div class="perf-content-edit">
        <textarea class="perf-contenu" rows="3">${escapeHtml(oldText)}</textarea>
        <div class="perf-edit-actions">
          <button class="perf-btn perf-btn-primary btn-save-edit">Enregistrer</button>
          <button class="perf-btn perf-btn-outline btn-cancel-edit">Annuler</button>
        </div>
      </div>
    `;
    itemEl.querySelector('.btn-edit').disabled = true;

    itemEl.querySelector('.btn-cancel-edit').onclick = () => {
      itemEl.querySelector('.perf-content-edit').outerHTML = `<div class="perf-content-read">${escapeHtml(oldText)}</div>`;
      itemEl.querySelector('.btn-edit').disabled = false;
    };

    itemEl.querySelector('.btn-save-edit').onclick = async () => {
      const newText = itemEl.querySelector('.perf-contenu').value.trim();
      try {
        await http('PUT', `/performance_perso/update/${id}`, { content: newText });
        itemEl.querySelector('.perf-content-edit').outerHTML = `<div class="perf-content-read">${escapeHtml(newText)}</div>`;
        itemEl.querySelector('.btn-edit').disabled = false;
        toast("Performance mise à jour.");
      } catch(e){ console.error(e); toast("Erreur enregistrement.", "error"); }
    };
  }

  async function applyStatus(itemEl) {
    const id = Number(itemEl.dataset.id);
    const status = itemEl.querySelector(`input[name="perf-status-${id}"]:checked`)?.value === 'validee' ? 'validee' : 'non-validee';
    const dateIso = itemEl.querySelector('.perf-status-date')?.value || new Date().toISOString().slice(0,10);
    try {
      const res = await http('PUT', `/performance_perso/update/${id}`, { validation_status: status, validation_date: dateIso });
      if (res && res.item) {
        const label = itemEl.querySelector('[data-role="status-label"]');
        const date = itemEl.querySelector('[data-role="status-date"]');
        if (label) {
          label.textContent = (status === 'validee') ? 'Validée' : 'Non-validée';
          label.classList.toggle('perf-badge-success', status === 'validee');
          label.classList.toggle('perf-badge-muted', status !== 'validee');
        }
        if (date) {
          date.style.display = '';
          date.textContent = formatDateFR(dateIso);
        }
        toast("Validation enregistrée.");
      } else {
        toast("Erreur validation.", "error");
      }
    } catch(e){ console.error(e); toast("Erreur validation.", "error"); }
  }

  async function openHistoryModal(userId, activityId) {
    try {
      const resp = await http('GET', `/performance_perso/history?user_id=${userId}&activity_id=${activityId}`);
      const modal = document.getElementById('perf-history-modal');
      const closeBtn = modal.querySelector('.close-history');
      const list = document.getElementById('history-entries');

      if (!resp.ok && !resp.history) {
        list.innerHTML = `<p>Erreur de chargement.</p>`;
      } else {
        const items = resp.history || [];
        if (!items.length) list.innerHTML = `<p>Aucun historique pour cette activité.</p>`;
        else {
          list.innerHTML = items.map(row => {
            const st = (row.validation_status === 'validee') ? 'Validée' : (row.validation_status === 'non-validee' ? 'Non-validée' : '—');
            const dt = formatDateFR(row.validation_date) || '—';
            const changed = row.changed_at ? new Date(row.changed_at).toLocaleString('fr-FR') : '';
            return `
              <div class="hist-item perf-box">
                <div class="hist-head"><strong>${st}</strong> — ${dt}</div>
                <div class="hist-meta">Modifié le : ${changed}</div>
                <div class="hist-contenu">${escapeHtml(row.contenu || '')}</div>
              </div>
            `;
          }).join('');
        }
      }
      modal.classList.remove('hidden');
      closeBtn.onclick = () => modal.classList.add('hidden');
      modal.onclick = (e) => { if (e.target === modal) modal.classList.add('hidden'); };

    } catch(e){ console.error(e); toast("Erreur lors du chargement de l'historique.", "error"); }
  }

})();
