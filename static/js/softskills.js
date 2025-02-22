// static/js/softskills.js

function getActivityDetails(activityId) {
    const detailsElem = document.getElementById('details-' + activityId);
    return detailsElem ? detailsElem.innerText : "";
  }
  
  function getCompetenciesData(activityId) {
    const compElem = document.getElementById('competencies-list-' + activityId);
    if (!compElem) return "";
    let items = [];
    compElem.querySelectorAll('li').forEach(li => items.push(li.textContent.trim()));
    return items.join(", ");
  }
  
  function translateLevelToText(level) {
    switch(level) {
      case "1": return "Aptitude";
      case "2": return "Acquisition";
      case "3": return "Maîtrise";
      case "4": return "Excellence";
      default:  return "Inconnu";
    }
  }
  
  // Bouton "Proposer HSC"
  $(document).on('click', '.define-hsc-btn', function() {
    const activityId = $(this).data('activity-id');
    console.log("Proposer HSC pour activityId =", activityId);
    proposeSoftskills(activityId);
  });
  
  function proposeSoftskills(activityId) {
    const activityData = getActivityDetails(activityId);
    const competenciesData = getCompetenciesData(activityId);
    fetch('/softskills/propose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        activity: activityData,
        competencies: competenciesData
      })
    })
    .then(res => res.json())
    .then(data => {
      console.log("Réponse /softskills/propose:", data);
      if (data.error) {
        alert(data.error);
        return;
      }
      let addPromises = [];
      data.forEach(item => {
        let p = fetch('/softskills/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            activity_id: activityId,
            habilete: item.habilete,
            niveau: item.niveau
          })
        })
        .then(r => r.json())
        .then(added => {
          if (!added.error) {
            addSoftskillItemToDOM(activityId, added.habilete, added.niveau, added.id);
          } else {
            console.error("Erreur ajout HSC:", added.error);
          }
        })
        .catch(err => console.error("Erreur fetch /softskills/add:", err));
        addPromises.push(p);
      });
      return Promise.all(addPromises);
    })
    .catch(err => {
      alert("Erreur lors de la proposition HSC : " + err.message);
      console.error(err);
    });
  }
  
  // AJOUT MANUEL
  function submitSoftskill(activityId) {
    console.log("submitSoftskill pour activityId =", activityId);
    const nameInput = document.getElementById('softskill-name-' + activityId);
    const levelInput = document.getElementById('softskill-level-' + activityId);
    const hscName = nameInput.value.trim();
    const hscLevel = levelInput.value.trim();
    if(!hscName) {
      alert("Veuillez saisir un nom d'habileté.");
      return;
    }
    if(!["1","2","3","4"].includes(hscLevel)) {
      alert("Le niveau doit être 1, 2, 3 ou 4.");
      return;
    }
    fetch('/softskills/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        activity_id: activityId,
        habilete: hscName,
        niveau: hscLevel
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        addSoftskillItemToDOM(activityId, data.habilete, data.niveau, data.id);
        nameInput.value = "";
        levelInput.value = "";
        alert("Habileté sauvegardée en base.");
      }
    })
    .catch(err => {
      alert("Erreur lors de l'ajout : " + err.message);
      console.error(err);
    });
  }
  
  // Ajoute une HSC dans le DOM
  function addSoftskillItemToDOM(activityId, hscName, hscLevel, dbId) {
    console.log("Ajout DOM HSC:", { activityId, hscName, hscLevel, dbId });
    const container = document.getElementById('softskills-list-' + activityId);
    if (!container) {
      console.error("Conteneur #softskills-list-" + activityId + " introuvable.");
      return;
    }
    const levelLabel = translateLevelToText(hscLevel);
    const div = document.createElement('div');
    div.className = 'softskill-item';
    div.style.marginBottom = '5px';
    div.setAttribute('data-ss-id', dbId);
    div.innerHTML = `
      <span class="softskill-text">${hscName} (Niveau: <span class="softskill-level">${levelLabel}</span>)</span>
      <i class="fas fa-pencil-alt edit-softskill" title="Modifier"></i>
      <i class="fas fa-trash delete-softskill" title="Supprimer"></i>
      <div class="edit-softskill-form" id="edit-softskill-form-${dbId}" style="display:none;">
        <label>Habileté :</label>
        <input type="text" id="edit-softskill-name-${dbId}" value="${hscName}" />
        <label>Niveau (1..4) :</label>
        <input type="number" min="1" max="4" id="edit-softskill-level-${dbId}" value="${hscLevel}" />
        <button onclick="submitEditSoftskillFromDOM('${dbId}')">Enregistrer</button>
        <button onclick="hideEditSoftskillForm('${dbId}')">Annuler</button>
      </div>
    `;
    container.appendChild(div);
  }
  
  // Edition
  $(document).on('click', '.edit-softskill', function() {
    const itemElem = $(this).closest('.softskill-item');
    const dbId = itemElem.data('ss-id');
    console.log("Edition HSC dbId =", dbId);
    document.getElementById(`edit-softskill-form-${dbId}`).style.display = 'block';
  });
  
  function hideEditSoftskillForm(dbId) {
    document.getElementById(`edit-softskill-form-${dbId}`).style.display = 'none';
  }
  
  function submitEditSoftskillFromDOM(dbId) {
    console.log("submitEditSoftskillFromDOM dbId =", dbId);
    const newName = document.getElementById(`edit-softskill-name-${dbId}`).value.trim();
    const newLevel = document.getElementById(`edit-softskill-level-${dbId}`).value.trim();
    if(!newName) {
      alert("Veuillez saisir un nom d'habileté.");
      return;
    }
    if(!["1","2","3","4"].includes(newLevel)) {
      alert("Le niveau doit être 1, 2, 3 ou 4.");
      return;
    }
    fetch(`/softskills/${dbId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ habilete: newName, niveau: newLevel })
    })
    .then(res => res.json())
    .then(data => {
      console.log("Réponse PUT /softskills:", data);
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        const itemElem = document.querySelector(`.softskill-item[data-ss-id='${dbId}']`);
        if (itemElem) {
          const textElem = itemElem.querySelector('.softskill-text');
          const levelLabel = translateLevelToText(data.niveau);
          textElem.innerHTML = `${data.habilete} (Niveau: <span class="softskill-level">${levelLabel}</span>)`;
          hideEditSoftskillForm(dbId);
          alert("HSC mise à jour en base.");
        }
      }
    })
    .catch(err => {
      alert("Erreur lors de la mise à jour : " + err.message);
      console.error(err);
    });
  }
  
  // Suppression
  $(document).on('click', '.delete-softskill', function() {
    const itemElem = $(this).closest('.softskill-item');
    const dbId = itemElem.data('ss-id');
    console.log("deleteSoftskill dbId =", dbId);
    if(!confirm("Voulez-vous supprimer cette habileté ?")) return;
    fetch(`/softskills/${dbId}`, { method: 'DELETE' })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        itemElem.remove();
        alert("HSC supprimée.");
      }
    })
    .catch(err => {
      alert("Erreur lors de la suppression : " + err.message);
      console.error(err);
    });
  });
  