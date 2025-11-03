// Code/static/js/competences_crud.js
// Handlers CRUD unifiés pour Savoirs / Savoir-faire / Softskills / Aptitudes
// Compatible avec les onclick existants dans tes templates.
// Dépend uniquement de fetch() et des endpoints déjà en place.

///////////////////////////////
// Utils communs
///////////////////////////////
function showSpinner(){ const s=document.getElementById('spinner'); if(s) s.style.display='inline-block'; }
function hideSpinner(){ const s=document.getElementById('spinner'); if(s) s.style.display='none'; }

function notify(msg, type='success'){
  // remplace alert() par un toast si tu veux — pour l’instant simple fallback:
  console.log(`[${type}]`, msg);
}

///////////////////////////////
// Refresh section activité
///////////////////////////////
async function refreshActivityItems(activityId) {
  try {
    showSpinner();
    const res = await fetch(`/activities/${activityId}/details`);
    if (!res.ok) throw new Error("Impossible de récupérer les détails de l'activité");
    const data = await res.json();

    // On attend que chaque bloc activité soit isolé dans un container dédié par type
    // Ex: #savoirs-container-<id>, #savoir-faires-container-<id>, #softskills-container-<id>, #aptitudes-container-<id>
    // et que le serveur serve des partiels HTML si nécessaire (sinon on régénère côté client).
    // Ici, on re-render minimaliste: on remplace <ul> de chaque section si existant.
    const map = [
      { key: 'savoirs',           listSelector: `#savoirs-container-${activityId} ul` },
      { key: 'savoir_faires',     listSelector: `#savoir-faires-container-${activityId} ul` },
      { key: 'softskills',        listSelector: `#softskills-container-${activityId} ul` },
      { key: 'aptitudes',         listSelector: `#aptitudes-container-${activityId} ul` },
    ];

    map.forEach(({key, listSelector}) => {
      const ul = document.querySelector(listSelector);
      if (!ul) return;
      const arr = Array.isArray(data[key]) ? data[key] : [];
      ul.innerHTML = arr.length
        ? arr.map(item => {
            // Chaque item doit garder les mêmes ids que tes templates actuels
            // et les mêmes onclick pour rester 100% compatible.
            const id   = item.id;
            const text = item.name || item.description || item.label || '';
            // Boutons d’édition/suppression en conservant les noms de fonctions attendus
            if (key === 'savoir_faires') {
              return `
                <li id="savoir-faire-${id}">
                  <span class="savoir-faire-text">${escapeHtml(text)}</span>
                  <button class="edit-sf-btn"
                          data-sf='${JSON.stringify({id, name: text})}'
                          onclick="showEditSavoirFairesForm(this)">
                    <i class="fa-solid fa-pencil"></i>
                  </button>
                  <button onclick="deleteSavoirFaires('${activityId}','${id}')">
                    <i class="fa-solid fa-trash"></i>
                  </button>
                  <div id="edit-sf-form-${id}" style="display:none; margin-top:5px;">
                    <input type="text" id="edit-sf-input-${id}" />
                    <button onclick="submitEditSavoirFaires('${activityId}','${id}')">Enregistrer</button>
                    <button onclick="hideEditSavoirFairesForm('${id}')">Annuler</button>
                  </div>
                </li>`;
            }
            if (key === 'savoirs') {
              return `
                <li id="savoir-${id}">
                  <span class="savoir-text">${escapeHtml(text)}</span>
                  <button class="edit-savoir-btn"
                          data-savoir='${JSON.stringify({id, name: text})}'
                          onclick="showEditSavoirForm(this)">
                    <i class="fa-solid fa-pencil"></i>
                  </button>
                  <button onclick="deleteSavoir('${activityId}','${id}')">
                    <i class="fa-solid fa-trash"></i>
                  </button>
                  <div id="edit-savoir-form-${id}" style="display:none; margin-top:5px;">
                    <input type="text" id="edit-savoir-input-${id}" />
                    <button onclick="submitEditSavoir('${activityId}','${id}')">Enregistrer</button>
                    <button onclick="hideEditSavoirForm('${id}')">Annuler</button>
                  </div>
                </li>`;
            }
            if (key === 'softskills') {
              return `
                <li id="softskill-${id}">
                  <span class="softskill-text">${escapeHtml(text)}</span>
                  <button class="edit-softskill-btn"
                          data-softskill='${JSON.stringify({id, name: text})}'
                          onclick="showEditSoftskillForm(this)">
                    <i class="fa-solid fa-pencil"></i>
                  </button>
                  <button onclick="deleteSoftskill('${activityId}','${id}')">
                    <i class="fa-solid fa-trash"></i>
                  </button>
                  <div id="edit-softskill-form-${id}" style="display:none; margin-top:5px;">
                    <input type="text" id="edit-softskill-input-${id}" />
                    <button onclick="submitEditSoftskill('${activityId}','${id}')">Enregistrer</button>
                    <button onclick="hideEditSoftskillForm('${id}')">Annuler</button>
                  </div>
                </li>`;
            }
            // aptitudes
            return `
              <li id="aptitude-${id}">
                <span class="aptitude-text">${escapeHtml(text)}</span>
                <button class="edit-aptitude-btn"
                        data-aptitude='${JSON.stringify({id, description: text})}'
                        onclick="showEditAptitudeForm(this)">
                  <i class="fa-solid fa-pencil"></i>
                </button>
                <button onclick="deleteAptitude('${activityId}','${id}')">
                  <i class="fa-solid fa-trash"></i>
                </button>
                <div id="edit-aptitude-form-${id}" style="display:none; margin-top:5px;">
                  <input type="text" id="edit-aptitude-input-${id}" />
                  <button onclick="submitEditAptitude('${activityId}','${id}')">Enregistrer</button>
                  <button onclick="hideEditAptitudeForm('${id}')">Annuler</button>
                </div>
              </li>`;
          }).join('')
        : `<p>Aucun élément.</p>`;
    });

  } catch (e) {
    console.error(e);
    notify(e.message || 'Erreur de rafraîchissement', 'error');
  } finally {
    hideSpinner();
  }
}

// petit util
function escapeHtml(s){
  return String(s ?? '').replace(/[&<>"']/g, m => (
    { '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]
  ));
}

///////////////////////////////
// Savoir-FAIRE
///////////////////////////////
function showEditSavoirFairesForm(btn){
  const sf = JSON.parse(btn.getAttribute('data-sf'));
  document.getElementById(`edit-sf-input-${sf.id}`).value = sf.name || '';
  document.getElementById(`edit-sf-form-${sf.id}`).style.display = 'block';
}
function hideEditSavoirFairesForm(id){
  document.getElementById(`edit-sf-form-${id}`).style.display = 'none';
}
function submitEditSavoirFaires(activityId, id){
  const value = document.getElementById(`edit-sf-input-${id}`).value.trim();
  showSpinner();
  fetch(`/savoir_faires/${id}`, {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ name: value })
  })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    hideEditSavoirFairesForm(id);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur modification savoir-faire : ${e.message}`,'error'); })
  .finally(hideSpinner);
}
function deleteSavoirFaires(activityId, id){
  showSpinner();
  fetch(`/savoir_faires/${id}`, { method:'DELETE' })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur suppression savoir-faire : ${e.message}`,'error'); })
  .finally(hideSpinner);
}
function showAddSavoirFairesForm(activityId){
  document.getElementById(`add-sf-form-${activityId}`).style.display='block';
}
function hideAddSavoirFairesForm(activityId){
  document.getElementById(`add-sf-form-${activityId}`).style.display='none';
}
function submitAddSavoirFaires(activityId){
  const value = document.getElementById(`add-sf-input-${activityId}`).value.trim();
  showSpinner();
  fetch(`/savoir_faires`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ activity_id: activityId, name: value })
  })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    hideAddSavoirFairesForm(activityId);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur ajout savoir-faire : ${e.message}`,'error'); })
  .finally(hideSpinner);
}

///////////////////////////////
// SAVOIRS
///////////////////////////////
function showEditSavoirForm(btn){
  const sv = JSON.parse(btn.getAttribute('data-savoir'));
  document.getElementById(`edit-savoir-input-${sv.id}`).value = sv.name || '';
  document.getElementById(`edit-savoir-form-${sv.id}`).style.display = 'block';
}
function hideEditSavoirForm(id){
  document.getElementById(`edit-savoir-form-${id}`).style.display='none';
}
function submitEditSavoir(activityId, id){
  const value = document.getElementById(`edit-savoir-input-${id}`).value.trim();
  showSpinner();
  fetch(`/savoirs/${id}`, {
    method:'PUT',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ name: value })
  })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    hideEditSavoirForm(id);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur modification savoir : ${e.message}`,'error'); })
  .finally(hideSpinner);
}
function deleteSavoir(activityId, id){
  showSpinner();
  fetch(`/savoirs/${id}`, { method:'DELETE' })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur suppression savoir : ${e.message}`,'error'); })
  .finally(hideSpinner);
}

///////////////////////////////
// SOFTSKILLS
///////////////////////////////
function showEditSoftskillForm(btn){
  const ss = JSON.parse(btn.getAttribute('data-softskill'));
  document.getElementById(`edit-softskill-input-${ss.id}`).value = ss.name || '';
  document.getElementById(`edit-softskill-form-${ss.id}`).style.display='block';
}
function hideEditSoftskillForm(id){
  document.getElementById(`edit-softskill-form-${id}`).style.display='none';
}
function submitEditSoftskill(activityId, id){
  const value = document.getElementById(`edit-softskill-input-${id}`).value.trim();
  showSpinner();
  fetch(`/softskills/${id}`, {
    method:'PUT',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ name: value })
  })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    hideEditSoftskillForm(id);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur modification softskill : ${e.message}`,'error'); })
  .finally(hideSpinner);
}
function deleteSoftskill(activityId, id){
  showSpinner();
  fetch(`/softskills/${id}`, { method:'DELETE' })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur suppression softskill : ${e.message}`,'error'); })
  .finally(hideSpinner);
}

///////////////////////////////
// APTITUDES
///////////////////////////////
function showEditAptitudeForm(btn){
  const ap = JSON.parse(btn.getAttribute('data-aptitude'));
  document.getElementById(`edit-aptitude-input-${ap.id}`).value = ap.description || '';
  document.getElementById(`edit-aptitude-form-${ap.id}`).style.display='block';
}
function hideEditAptitudeForm(id){
  document.getElementById(`edit-aptitude-form-${id}`).style.display='none';
}
function submitEditAptitude(activityId, id){
  const value = document.getElementById(`edit-aptitude-input-${id}`).value.trim();
  showSpinner();
  fetch(`/aptitudes/${id}`, {
    method:'PUT',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ description: value })
  })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    hideEditAptitudeForm(id);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur modification aptitude : ${e.message}`,'error'); })
  .finally(hideSpinner);
}
function deleteAptitude(activityId, id){
  showSpinner();
  fetch(`/aptitudes/${id}`, { method:'DELETE' })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur suppression aptitude : ${e.message}`,'error'); })
  .finally(hideSpinner);
}
function showAddAptitudeForm(activityId){
  document.getElementById(`add-aptitude-form-${activityId}`).style.display='block';
}
function hideAddAptitudeForm(activityId){
  document.getElementById(`add-aptitude-form-${activityId}`).style.display='none';
}
function submitAddAptitude(activityId){
  const value = document.getElementById(`add-aptitude-input-${activityId}`).value.trim();
  showSpinner();
  fetch(`/aptitudes`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ activity_id: activityId, description: value })
  })
  .then(r=>r.json())
  .then(d=>{
    if(d.error) throw new Error(d.error);
    hideAddAptitudeForm(activityId);
    refreshActivityItems(activityId);
  })
  .catch(e=>{ notify(`Erreur ajout aptitude : ${e.message}`,'error'); })
  .finally(hideSpinner);
}

// Expose explicitement les fonctions attendues par les onclick des templates
window.refreshActivityItems = refreshActivityItems;
window.showEditSavoirFairesForm = showEditSavoirFairesForm;
window.hideEditSavoirFairesForm = hideEditSavoirFairesForm;
window.submitEditSavoirFaires = submitEditSavoirFaires;
window.deleteSavoirFaires = deleteSavoirFaires;
window.showAddSavoirFairesForm = showAddSavoirFairesForm;
window.hideAddSavoirFairesForm = hideAddSavoirFairesForm;
window.submitAddSavoirFaires = submitAddSavoirFaires;

window.showEditSavoirForm = showEditSavoirForm;
window.hideEditSavoirForm = hideEditSavoirForm;
window.submitEditSavoir = submitEditSavoir;
window.deleteSavoir = deleteSavoir;

window.showEditSoftskillForm = showEditSoftskillForm;
window.hideEditSoftskillForm = hideEditSoftskillForm;
window.submitEditSoftskill = submitEditSoftskill;
window.deleteSoftskill = deleteSoftskill;

window.showEditAptitudeForm = showEditAptitudeForm;
window.hideEditAptitudeForm = hideEditAptitudeForm;
window.submitEditAptitude = submitEditAptitude;
window.deleteAptitude = deleteAptitude;
window.showAddAptitudeForm = showAddAptitudeForm;
window.hideAddAptitudeForm = hideAddAptitudeForm;
window.submitAddAptitude = submitAddAptitude;
