// Code/static/js/performance_perso.js
(function () {
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function escapeHtml(s){
    return (s||'').replace(/[&<>"']/g, c => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    }[c]));
  }
  function toast(message, type="success"){
    let el = document.getElementById("toast-message");
    if (!el) {
      el = document.createElement('div');
      el.id = 'toast-message';
      el.className = 'toast';
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.classList.remove("hidden","error","success");
    el.classList.add(type==="error"?"error":"success","show");
    setTimeout(()=>{el.classList.remove("show")}, 2200);
  }
  function formatDateFR(raw){
    if(!raw) return '';
    try{ const d = new Date(raw); if(!isNaN(d)) return d.toLocaleString('fr-FR'); }catch(e){}
    if(/^\d{4}-\d{2}-\d{2}$/.test(raw)){ const [y,m,dd]=raw.split('-'); return `${dd}/${m}/${y}`; }
    return raw;
  }
  function ellipsis(str, max=80){
    const s=(str||'').trim();
    if(s.length<=max) return s;
    return s.slice(0,max-1)+"…";
  }

  async function http(method, url, body) {
    const opt = { method, headers: { "Cache-Control": "no-store" } };
    if (body) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
    const r = await fetch(url, opt);

    const text = await r.text();
    let data = null;
    try { data = JSON.parse(text); }
    catch { data = (text || '').trim(); }

    if (!r.ok) {
      let msg = "HTTP " + r.status;
      if (data && typeof data === 'object' && data.error) msg = data.error;
      throw new Error(msg);
    }
    return (typeof data === 'string') ? { raw: data } : (data || {});
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
            <button class="perf-btn perf-btn-outline btn-history" type="button" title="Historique (toutes les perf)">Historique</button>
            <button class="perf-btn perf-btn-primary btn-add-perf" type="button">+ Ajouter</button>
          </div>
        </div>
        <div class="perf-content">
          <div class="perf-general-container"></div>
          <div class="perf-personal-container"></div>
        </div>
      `;
      mountEl.prepend(wrapper);
    }

    // 1) Performance générale
    try {
      const activitySection = mountEl.closest('.activity-section');
      const linkId = activitySection ? activitySection.dataset.linkId : null;
      const genCtn = $('.perf-general-container', wrapper);
      if (linkId) {
        const htmlFrag = await http('GET', `/performance/render/${linkId}`);
        genCtn.innerHTML = (typeof htmlFrag === 'object' && htmlFrag.raw) ? htmlFrag.raw : htmlFrag;
      } else {
        const htmlFrag = await http('GET', `/performance/render_activity/${activityId}`);
        genCtn.innerHTML = (typeof htmlFrag === 'object' && htmlFrag.raw) ? htmlFrag.raw : htmlFrag;
      }
    } catch (e) {
      console.error("perf générale:", e);
      $('.perf-general-container', wrapper).innerHTML = `<div class="perf-box"><em>Impossible de charger la performance générale.</em></div>`;
    }

    // 2) Personnalisées
    const persoCtn = $('.perf-personal-container', wrapper);
    if (!userId) {
      persoCtn.innerHTML = `<div class="perf-subtitle">Performances personnalisées</div><div class="perf-empty"><em>Sélectionnez un collaborateur pour voir ses performances personnalisées.</em></div>`;
    } else {
      await reloadPersonalList(persoCtn, userId, activityId);
    }

    // 3) Historique global
    $('.btn-history', wrapper).onclick = () => openHistoryModalAll(userId, activityId);
    $('.btn-add-perf', wrapper).onclick = () => openEditorCreate(persoCtn, userId, activityId);
  };

  async function reloadPersonalList(container, userId, activityId) {
    try {
      const items = await http('GET', `/performance_perso/list?user_id=${userId}&activity_id=${activityId}`);
      renderPersonalList(container, items);
    } catch (e) {
      console.error(e);
      container.innerHTML = `<div class="perf-subtitle">Performances personnalisées</div><div class="perf-empty">Erreur de chargement des performances personnalisées.</div>`;
    }
  }

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

    // Bind events
    itemsEl.querySelectorAll('.btn-edit')
      .forEach(btn => btn.addEventListener('click', () => toggleEdit(btn.closest('.perf-item'))));
    itemsEl.querySelectorAll('.btn-apply-status')
      .forEach(btn => btn.addEventListener('click', () => applyStatus(btn.closest('.perf-item'))));
    itemsEl.querySelectorAll('.btn-delete')
      .forEach(btn => btn.addEventListener('click', () => deleteItem(btn.closest('.perf-item'))));
    itemsEl.querySelectorAll('.btn-save-content')
      .forEach(btn => btn.addEventListener('click', () => saveContent(btn.closest('.perf-item'))));
    itemsEl.querySelectorAll('.btn-cancel-edit')
      .forEach(btn => btn.addEventListener('click', () => cancelEdit(btn.closest('.perf-item'))));
    itemsEl.querySelectorAll('.btn-history-item')
      .forEach(btn => btn.addEventListener('click', () => openHistoryModalForPerf(Number(btn.closest('.perf-item').dataset.id))));
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
          <div class="perf-item-buttons">
            <button class="perf-btn perf-btn-outline btn-history-item" type="button" title="Historique de cette performance">Historique</button>
            <button class="perf-btn perf-btn-outline btn-edit" type="button" title="Modifier">Modifier</button>
            <button class="perf-btn perf-btn-danger btn-delete" type="button" title="Supprimer">Supprimer</button>
          </div>
        </div>

        <div class="perf-content-read">${escapeHtml(p.content || '')}</div>

        <div class="perf-item-actions" style="display:none;">
          <div class="perf-content-edit" style="width:100%;">
            <textarea class="perf-textarea" rows="3" placeholder="Modifier la performance...">${escapeHtml(p.content || '')}</textarea>
            <div class="perf-edit-row">
              <label class="perf-radio">
                <input type="radio" name="perf-status-${p.id}" value="validee" ${p.validation_status === 'validee' ? 'checked' : ''}> Validée
              </label>
              <label class="perf-radio">
                <input type="radio" name="perf-status-${p.id}" value="non-validee" ${p.validation_status !== 'validee' ? 'checked' : ''}> Non-validée
              </label>
              <input type="date" class="perf-status-date" value="${p.validation_date || ''}">
            </div>
            <div class="perf-edit-actions">
              <button class="perf-btn perf-btn-primary btn-save-content" type="button">Enregistrer</button>
              <button class="perf-btn perf-btn-outline btn-apply-status" type="button">Appliquer statut</button>
              <button class="perf-btn perf-btn-outline btn-cancel-edit" type="button">Annuler</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function toggleEdit(itemEl) {
    if (!itemEl) return;
    const actions = itemEl.querySelector('.perf-item-actions');
    const now = actions.style.display === 'none' || actions.style.display === '' ? 'flex' : 'none';
    actions.style.display = now;
    itemEl.classList.toggle('editing', now === 'flex');
  }

  function cancelEdit(itemEl) {
    if (!itemEl) return;
    const actions = itemEl.querySelector('.perf-item-actions');
    const textarea = itemEl.querySelector('.perf-textarea');
    const read = itemEl.querySelector('.perf-content-read');
    if (textarea && read) textarea.value = read.textContent;
    actions.style.display = 'none';
    itemEl.classList.remove('editing');
  }

  async function saveContent(itemEl) {
    const id = Number(itemEl.dataset.id);
    const textarea = itemEl.querySelector('.perf-textarea');
    const content = (textarea?.value || '').trim();
    const dateIso = itemEl.querySelector('.perf-status-date')?.value || null;
    const status = itemEl.querySelector(`input[name="perf-status-${id}"]:checked`)?.value;

    try {
      const payload = { content };
      if (status) payload.validation_status = status;
      if (dateIso) payload.validation_date = dateIso;

      const res = await http('PUT', `/performance_perso/update/${id}`, payload);

      if ((res && res.ok) || (res && res.item)) {
        itemEl.querySelector('.perf-content-read').textContent = content;

        const label = itemEl.querySelector('[data-role="status-label"]');
        const date = itemEl.querySelector('[data-role="status-date"]');
        if (status && label) {
          label.textContent = (status === 'validee') ? 'Validée' : 'Non-validée';
          label.classList.toggle('perf-badge-success', status === 'validee');
          label.classList.toggle('perf-badge-muted', status !== 'validee');
        }
        if (date && dateIso) { date.style.display = ''; date.textContent = formatDateFR(dateIso); }

        toast("Performance mise à jour.");
        cancelEdit(itemEl);
      } else {
        toast("Mise à jour impossible.", "error");
      }
    } catch (e) {
      console.error(e);
      toast("Mise à jour impossible.", "error");
    }
  }

  async function applyStatus(itemEl) {
    const id = Number(itemEl.dataset.id);
    const status = itemEl.querySelector(`input[name="perf-status-${id}"]:checked`)?.value === 'validee' ? 'validee' : 'non-validee';
    const dateIso = itemEl.querySelector('.perf-status-date')?.value || new Date().toISOString().slice(0,10);
    try {
      const res = await http('PUT', `/performance_perso/update/${id}`, { validation_status: status, validation_date: dateIso });
      if ((res && res.ok) || (res && res.item)) {
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

  async function deleteItem(itemEl) {
    if (!itemEl) return;
    const id = Number(itemEl.dataset.id);
    if (!confirm("Confirmez-vous la suppression de cette performance ?")) return;
    try {
      const res = await http('DELETE', `/performance_perso/delete/${id}`);
      if ((res && res.ok) || (res && res.item === undefined)) {
        itemEl.remove();
        toast("Performance supprimée.");
      } else {
        toast("Suppression impossible.", "error");
      }
    } catch(e){ console.error(e); toast("Suppression impossible.", "error"); }
  }

  function openEditorCreate(container, userId, activityId) {
    if (!userId) return toast("Sélectionnez un collaborateur.", "error");
    const editor = document.createElement('div');
    editor.className = 'perf-editor perf-box';
    editor.innerHTML = `
      <textarea class="perf-contenu" rows="3" placeholder="Décris la performance..."></textarea>
      <div class="perf-editor-actions">
        <button class="perf-btn perf-btn-primary btn-save" type="button">Enregistrer</button>
        <button class="perf-btn perf-btn-outline btn-cancel" type="button">Annuler</button>
      </div>
    `;
    container.prepend(editor);

    editor.querySelector('.btn-cancel').onclick = () => editor.remove();
    editor.querySelector('.btn-save').onclick = async () => {
      const content = editor.querySelector('.perf-contenu').value.trim();
      if (!content) { toast("Le contenu est obligatoire.", "error"); return; }
      try {
        const res = await http('POST', '/performance_perso/create', {
          user_id: userId,
          activity_id: activityId,
          content,
          validation_status: 'non-validee'
        });
        if ((res && res.ok) || (res && res.item)) {
          toast("Performance créée.");
          editor.remove();
          await reloadPersonalList(container, userId, activityId);
        } else {
          toast((res && res.error) || "Création impossible.", "error");
        }
      } catch(e){ console.error(e); toast("Création impossible.", "error"); }
    };
  }

  // ===== Historique global (activité + user) — regroupé par performance + PURGE d'historique (pas suppression perf)
  async function openHistoryModalAll(userId, activityId) {
    try {
      // 1) Historique brut
      const resp = await http('GET', `/performance_perso/history?user_id=${userId}&activity_id=${activityId}`);

      // 2) État actuel pour label vivant
      let currentMap = new Map();
      try {
        const current = await http('GET', `/performance_perso/list?user_id=${userId}&activity_id=${activityId}`);
        if (Array.isArray(current)) {
          current.forEach(p => currentMap.set(p.id, p.content || ""));
        }
      } catch (e) { /* ignore */ }

      const modal = document.getElementById('perf-history-modal');
      const title = modal?.querySelector('#history-title');
      const list = document.getElementById('history-entries');
      if (title) title.textContent = `Historique — Performances personnalisées (activité ${activityId})`;

      if (!resp || !resp.history || !resp.history.length) {
        list.innerHTML = `<div class="timeline"><div class="timeline-empty">Aucun historique.</div></div>`;
      } else {
        // Groupage par performance_id
        const groups = new Map();
        for (const r of resp.history) {
          const pid = r.performance_id;
          if (!groups.has(pid)) groups.set(pid, []);
          groups.get(pid).push(r);
        }

        // Accordéon <details> par perf
        let html = `<div class="perf-accordion">`;
        const sorted = Array.from(groups.entries()).sort((a,b)=> Number(a[0]) - Number(b[0]));
        for (const [pid, rows] of sorted) {
          const rowsSorted = rows.slice().sort((a,b)=>{
            const da = (new Date(a.changed_at||0)).getTime();
            const db = (new Date(b.changed_at||0)).getTime();
            return db - da;
          });
          const last = rowsSorted[0] || {};
          const isDeleted = (last.event === 'deleted');

          // Titre : nom vivant si existe, sinon dernier contenu connu
          const liveContent = currentMap.get(Number(pid));
          let displayName = liveContent && liveContent.trim() ? liveContent.trim() : null;
          if (!displayName) {
            const withContent = rowsSorted.find(r => (r.content||'').trim().length>0);
            displayName = withContent ? withContent.content.trim() : `#${pid}`;
          }
          const titleText = `Performance : ${ellipsis(displayName, 120)}`;

          const count = rows.length;
          const lastDate = last.changed_at ? formatDateFR(last.changed_at) : '—';
          const metaText = isDeleted ? `Supprimée · Dernière modif : ${lastDate}` : `${count} entrée${count>1?'s':''} · Dernière modif : ${lastDate}`;

          const timeline = buildTimeline(rowsSorted.map(r => ({...r, perf_id: pid})), { showPerfBadge: false, deleted: isDeleted });

          html += `
            <details class="acc ${isDeleted ? 'acc--deleted':''}" data-pid="${pid}">
              <summary class="acc-summary">
                <span class="acc-left">
                  <span class="acc-caret" aria-hidden="true"></span>
                  <strong class="acc-name" title="${escapeHtml(displayName)}">${escapeHtml(titleText)}</strong>
                </span>
                <span class="acc-meta">${escapeHtml(metaText)}</span>
                <button class="acc-trash" type="button" title="Supprimer l'historique de cette performance" aria-label="Supprimer l'historique">
                  <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
                    <path d="M9 3h6l1 2h4v2H4V5h4l1-2zm1 6h2v9h-2V9zm4 0h2v9h-2V9zM7 9h2v9H7V9z"/>
                  </svg>
                </button>
              </summary>
              <div class="acc-panel">
                ${timeline}
              </div>
            </details>
          `;
        }
        html += `</div>`;
        list.innerHTML = html;

        // Bind PURGE d'historique (DELETE /performance_perso/history/<id>)
        bindAccordionHistoryPurge(list);
      }
      showHistoryModal();
    } catch(e){ console.error(e); toast("Erreur lors du chargement de l'historique.", "error"); }
  }

  function bindAccordionHistoryPurge(container){
    container.querySelectorAll('.acc-trash').forEach(btn => {
      btn.addEventListener('click', (ev) => {
        // Empêcher le toggle du <details> via <summary>
        ev.preventDefault();
        ev.stopPropagation();

        const acc = btn.closest('details.acc');
        if (!acc) return;

        // Toujours ouvrir pour voir la confirmation
        acc.open = true;

        // Fermer toute confirmation existante
        container.querySelectorAll('.acc-confirm').forEach(c => c.remove());

        // Afficher confirm inline
        const confirm = document.createElement('div');
        confirm.className = 'acc-confirm';
        confirm.innerHTML = `
          <div class="acc-confirm-text">Voulez-vous supprimer l'historique de cette performance ?</div>
          <div class="acc-confirm-actions">
            <button class="acc-confirm-btn acc-confirm-yes" type="button">Oui</button>
            <button class="acc-confirm-btn acc-confirm-cancel" type="button">Non</button>
          </div>
        `;
        acc.querySelector('.acc-panel').prepend(confirm);

        confirm.querySelector('.acc-confirm-cancel').onclick = () => confirm.remove();
        confirm.querySelector('.acc-confirm-yes').onclick = async () => {
          const pid = Number(acc.dataset.pid);
          try {
            const res = await http('DELETE', `/performance_perso/history/${pid}`);
            if ((res && res.ok) || (res && res.purged)) {
              const wasDeleted = acc.classList.contains('acc--deleted');

              if (wasDeleted) {
                // Si la perf était déjà supprimée : retirer complètement du listing historique
                const accordion = container.querySelector('.perf-accordion') || container;
                acc.remove();
                const remaining = accordion.querySelectorAll('details.acc').length;
                if (remaining === 0) {
                  container.innerHTML = `<div class="timeline"><div class="timeline-empty">Aucun historique.</div></div>`;
                }
              } else {
                // Sinon, garder la perf et indiquer que l'historique est vide
                const panel = acc.querySelector('.acc-panel');
                if (panel) panel.innerHTML = `<div class="timeline"><div class="timeline-empty">Historique supprimé.</div></div>`;
                const meta = acc.querySelector('.acc-meta');
                const now = new Date();
                const stamp = now.toLocaleString('fr-FR');
                if (meta) meta.textContent = `Historique supprimé · ${stamp}`;
              }

              toast("Historique supprimé.");
            } else {
              toast("Suppression d'historique impossible.", "error");
            }
          } catch (e) {
            console.error(e);
            toast("Suppression d'historique impossible.", "error");
          } finally {
            confirm.remove();
          }
        };
      });
    });
  }

  // -------- Historique par performance (ID)
  async function openHistoryModalForPerf(perfId) {
    try {
      const resp = await http('GET', `/performance_perso/history/${perfId}`);
      const modal = document.getElementById('perf-history-modal');
      const title = modal?.querySelector('#history-title');
      const list = document.getElementById('history-entries');
      if (title) title.textContent = `Historique — Performance #${perfId}`;
      if (!resp || !resp.history || !resp.history.length) {
        list.innerHTML = `<div class="timeline"><div class="timeline-empty">Aucun historique pour cette performance.</div></div>`;
      } else {
        list.innerHTML = buildTimeline(resp.history.map(r => ({ ...r, perf_id: perfId })), { showPerfBadge: true });
      }
      showHistoryModal();
    } catch (e) {
      console.error(e);
      toast("Erreur lors du chargement de l'historique.", "error");
    }
  }

  function buildTimeline(rows, opts = {}) {
    const { showPerfBadge = true, deleted = false } = opts;
    const mapEvent = {
      created: "Création",
      before_update: "Avant modification",
      deleted: "Suppression"
    };
    const items = rows.map(r => {
      const stamp = r.changed_at ? formatDateFR(r.changed_at) : '—';
      const st = (r.validation_status === 'validee') ? 'Validée'
               : (r.validation_status === 'non-validee') ? 'Non-validée' : '—';
      const dt = r.validation_date ? formatDateFR(r.validation_date) : '—';
      const evt = r.event ? (mapEvent[r.event] || 'Modification') : 'Modification';
      const c  = (r.content || '').trim();
      const content = c ? `<div class="timeline-body">${escapeHtml(c)}</div>` : '';
      const perfBadge = (showPerfBadge && r.perf_id) ? `<span class="timeline-badge">#${r.perf_id}</span>` : '';
      return `
        <div class="timeline-item ${deleted ? 'timeline-item--deleted':''}">
          <div class="timeline-dot"></div>
          <div class="timeline-content">
            <div class="timeline-head">
              ${perfBadge}
              <span class="timeline-date">${stamp}</span>
              <span class="timeline-sep">·</span>
              <span class="timeline-event">${evt}</span>
              <span class="timeline-sep">·</span>
              <span class="timeline-status ${st==='Validée'?'ok':'ko'}">${st}</span>
              <span class="timeline-sep">·</span>
              <span class="timeline-vdate">Date de validation : ${dt}</span>
            </div>
            ${content}
          </div>
        </div>
      `;
    }).join('');
    return `<div class="timeline">${items || '<div class="timeline-empty">Aucune entrée.</div>'}</div>`;
  }

  function showHistoryModal() {
    const modal = document.getElementById('perf-history-modal');
    const closeBtn = modal?.querySelector('.close-history');
    modal.classList.remove('hidden');
    if (closeBtn) closeBtn.onclick = () => modal.classList.add('hidden');
    modal.onclick = (e) => { if (e.target === modal) modal.classList.add('hidden'); };
  }
})();
