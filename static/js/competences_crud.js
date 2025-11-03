// static/js/competences_crud.js

function showSpinner(){ const s=document.getElementById('spinner'); if(s) s.style.display='inline-block'; }
function hideSpinner(){ const s=document.getElementById('spinner'); if(s) s.style.display='none'; }
function notify(msg, type='info'){ console[type === 'error' ? 'error' : 'log'](`[${type}] ${msg}`); }
function esc(s){ return String(s ?? '').replace(/[&<>"']/g, m=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m])); }

async function refreshActivityItems(activityId){
  try{
    showSpinner();
    const r = await fetch(`/activities/${activityId}/details`);
    if(!r.ok) throw new Error("Impossible de récupérer les détails.");
    const data = await r.json();

    // === SAVOIRS ===
    const ulSv = document.querySelector(`#savoirs-container-${activityId} ul`);
    if (ulSv){
      const arr = Array.isArray(data.savoirs) ? data.savoirs : [];
      ulSv.innerHTML = arr.map(it => `
        <li id="savoir-${it.id}">
          <span class="savoir-text" id="savoir-text-${it.id}">${esc(it.description || it.name || '')}</span>
          <button class="edit-savoir-btn"
                  data-savoir='${JSON.stringify({id: it.id, description: it.description || it.name || ''})}'
                  onclick="showEditSavoirForm(this)">✏</button>
          <button onclick="deleteSavoir('${activityId}','${it.id}')">🗑</button>
          <div id="edit-savoir-form-${it.id}" style="display:none;margin-top:6px;"></div>
        </li>`).join('');
    }

    // === SAVOIR-FAIRES ===
    const ulSF = document.querySelector(`#savoir-faires-container-${activityId} ul`);
    if (ulSF){
      const arr = Array.isArray(data.savoir_faires) ? data.savoir_faires : [];
      ulSF.innerHTML = arr.map(it => `
        <li id="savoir-faire-${it.id}">
          <span class="savoir-faire-text" id="sf-text-${it.id}">${esc(it.description || it.name || '')}</span>
          <button class="edit-sf-btn"
                  data-savoir-faires='${JSON.stringify({id: it.id, description: it.description || it.name || ''})}'
                  onclick="showEditSavoirFairesForm(this)">✏</button>
          <button onclick="deleteSavoirFaires('${activityId}','${it.id}')">🗑</button>
          <div id="edit-sf-form-${it.id}" style="display:none;margin-top:6px;"></div>
        </li>`).join('');
    }

    // === SOFTSKILLS ===
    const ulSS = document.querySelector(`#softskills-container-${activityId} ul`);
    if (ulSS){
      const arr = Array.isArray(data.softskills) ? data.softskills : [];
      ulSS.innerHTML = arr.map(it => `
        <li id="softskill-${it.id}">
          <span class="softskill-text" id="ss-text-${it.id}">${esc(it.name || it.description || '')}</span>
          <button class="edit-ss-btn"
                  data-softskill='${JSON.stringify({id: it.id, name: it.name || it.description || ''})}'
                  onclick="showEditSoftskillForm(this)">✏</button>
          <button onclick="deleteSoftskill('${activityId}','${it.id}')">🗑</button>
          <div id="edit-ss-form-${it.id}" style="display:none;margin-top:6px;"></div>
        </li>`).join('');
    }

    // === APTITUDES ===
    const ulAP = document.querySelector(`#aptitudes-container-${activityId} ul`);
    if (ulAP){
      const arr = Array.isArray(data.aptitudes) ? data.aptitudes : [];
      ulAP.innerHTML = arr.map(it => `
        <li id="aptitude-${it.id}">
          <span class="aptitude-text" id="ap-text-${it.id}">${esc(it.description || it.name || '')}</span>
          <button class="edit-ap-btn"
                  data-aptitude='${JSON.stringify({id: it.id, description: it.description || it.name || ''})}'
                  onclick="showEditAptitudeForm(this)">✏</button>
          <button onclick="deleteAptitude('${activityId}','${it.id}')">🗑</button>
          <div id="edit-ap-form-${it.id}" style="display:none;margin-top:6px;"></div>
        </li>`).join('');
    }
  }catch(e){
    notify(e.message,'error');
  }finally{
    hideSpinner();
  }
}

// ===== Helpers d’édition : créent le mini-form si absent + pré-remplissent =====
function ensureInlineEdit(divId, inputId, value, onSaveJs){
  let host = document.getElementById(divId);
  if (!host){ return null; }
  if (!host.dataset.built){
    host.innerHTML = `
      <input id="${inputId}" type="text" style="width:70%" />
      <button onclick="${onSaveJs}">Enregistrer</button>
      <button onclick="(function(d){d.style.display='none'})(document.getElementById('${divId}'))">Annuler</button>`;
    host.dataset.built = "1";
  }
  const input = document.getElementById(inputId);
  input.value = value || '';
  host.style.display = 'block';
  input.focus();
  return host;
}

// === SAVOIRS ===
function showEditSavoirForm(btn){
  const data = btn.getAttribute('data-savoir');
  const {id, description} = JSON.parse(data);
  ensureInlineEdit(`edit-savoir-form-${id}`, `edit-savoir-input-${id}`, description,
    `submitEditSavoir('${findActivityId(btn)}','${id}')`);
}
function submitEditSavoir(activityId, id){
  const value = document.getElementById(`edit-savoir-input-${id}`).value.trim();
  fetch(`/savoirs/${activityId}/${id}`, {
    method:'PUT',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ description: value })
  }).then(r=>r.json()).then(async d=>{
    if(d.error) return notify(d.error,'error');
    await refreshActivityItems(activityId);
  }).catch(e=>notify(e.message,'error'));
}
function deleteSavoir(activityId, id){
  fetch(`/savoirs/${activityId}/${id}`, { method:'DELETE' })
    .then(r=>r.json()).then(async d=>{
      if(d.error) return notify(d.error,'error');
      await refreshActivityItems(activityId);
    }).catch(e=>notify(e.message,'error'));
}

// === SAVOIR-FAIRES === (accepte data-sf OU data-savoir-faires)
function showEditSavoirFairesForm(btn){
  const raw = btn.getAttribute('data-sf') || btn.getAttribute('data-savoir-faires');
  if (!raw) { console.warn("showEditSavoirFairesForm: data manquant", btn); return; }
  const obj = JSON.parse(raw);
  const {id} = obj;
  const value = obj.description || obj.name || '';
  ensureInlineEdit(`edit-sf-form-${id}`, `edit-sf-input-${id}`, value,
    `submitEditSavoirFaires('${findActivityId(btn)}','${id}')`);
}
function submitEditSavoirFaires(activityId, id){
  const value = document.getElementById(`edit-sf-input-${id}`).value.trim();
  fetch(`/savoir_faires/${activityId}/${id}`, {
    method:'PUT',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ description: value })
  }).then(r=>r.json()).then(async d=>{
    if(d.error) return notify(d.error,'error');
    await refreshActivityItems(activityId);
  }).catch(e=>notify(e.message,'error'));
}
function deleteSavoirFaires(activityId, id){
  fetch(`/savoir_faires/${activityId}/${id}`, { method:'DELETE' })
    .then(r=>r.json()).then(async d=>{
      if(d.error) return notify(d.error,'error');
      await refreshActivityItems(activityId);
    }).catch(e=>notify(e.message,'error'));
}

// === SOFTSKILLS ===
function showEditSoftskillForm(btn){
  const obj = JSON.parse(btn.getAttribute('data-softskill'));
  ensureInlineEdit(`edit-ss-form-${obj.id}`, `edit-ss-input-${obj.id}`, obj.name || '',
    `submitEditSoftskill('${findActivityId(btn)}','${obj.id}')`);
}
function submitEditSoftskill(activityId, id){
  const value = document.getElementById(`edit-ss-input-${id}`).value.trim();
  fetch(`/softskills/${activityId}/${id}`, {
    method:'PUT',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ name: value })
  }).then(r=>r.json()).then(async d=>{
    if(d.error) return notify(d.error,'error');
    await refreshActivityItems(activityId);
  }).catch(e=>notify(e.message,'error'));
}
function deleteSoftskill(activityId, id){
  fetch(`/softskills/${activityId}/${id}`, { method:'DELETE' })
    .then(r=>r.json()).then(async d=>{
      if(d.error) return notify(d.error,'error');
      await refreshActivityItems(activityId);
    }).catch(e=>notify(e.message,'error'));
}

// === APTITUDES ===
function showEditAptitudeForm(btn){
  const obj = JSON.parse(btn.getAttribute('data-aptitude'));
  ensureInlineEdit(`edit-ap-form-${obj.id}`, `edit-ap-input-${obj.id}`, obj.description || '',
    `submitEditAptitude('${findActivityId(btn)}','${obj.id}')`);
}
function submitEditAptitude(activityId, id){
  const value = document.getElementById(`edit-ap-input-${id}`).value.trim();
  fetch(`/aptitudes/${activityId}/${id}`, {
    method:'PUT',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ description: value })
  }).then(r=>r.json()).then(async d=>{
    if(d.error) return notify(d.error,'error');
    await refreshActivityItems(activityId);
  }).catch(e=>notify(e.message,'error'));
}
function deleteAptitude(activityId, id){
  fetch(`/aptitudes/${activityId}/${id}`, { method:'DELETE' })
    .then(r=>r.json()).then(async d=>{
      if(d.error) return notify(d.error,'error');
      await refreshActivityItems(activityId);
    }).catch(e=>notify(e.message,'error'));
}

// util: retrouver l'activityId depuis le DOM (li parent porte un id "xxx-<id>"),
function findActivityId(el){
  const root = el.closest('[id^="activity-card-"], [data-activity-id]');
  if (root && root.dataset.activityId) return root.dataset.activityId;
  // sinon on tente dans un input hidden global
  const h = document.getElementById('current-activity-id');
  return h ? h.value : '';
}

// Expose
window.refreshActivityItems = refreshActivityItems;
window.showEditSavoirForm = showEditSavoirForm;
window.submitEditSavoir = submitEditSavoir;
window.deleteSavoir = deleteSavoir;
window.showEditSavoirFairesForm = showEditSavoirFairesForm;
window.submitEditSavoirFaires = submitEditSavoirFaires;
window.deleteSavoirFaires = deleteSavoirFaires;
window.showEditSoftskillForm = showEditSoftskillForm;
window.submitEditSoftskill = submitEditSoftskill;
window.deleteSoftskill = deleteSoftskill;
window.showEditAptitudeForm = showEditAptitudeForm;
window.submitEditAptitude = submitEditAptitude;
window.deleteAptitude = deleteAptitude;
