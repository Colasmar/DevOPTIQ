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

// Proposer des softskills via IA
$(document).on('click', '.define-hsc-btn', function() {
    const activityId = $(this).data('activity-id');
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
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        renderSoftskills(activityId, data);
    })
    .catch(error => {
        alert("Erreur lors de la récupération des habiletés socio-cognitives.");
        console.error(error);
    });
}

function renderSoftskills(activityId, softskills) {
    const container = document.getElementById('softskills-list-' + activityId);
    if (!container) return;
    // On efface l'existant pour ne pas mélanger
    // (si vous voulez juste ajouter, c'est à vous de voir)
    // Puis on insère chaque HSC renvoyée par l'IA
    softskills.forEach(item => {
        addSoftskillItemToDOM(activityId, item.habilete, item.niveau);
    });
}

// Ajout manuel d'une HSC
function submitSoftskill(activityId) {
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
            addSoftskillItemToDOM(activityId, data.habilete, data.niveau);
            nameInput.value = "";
            levelInput.value = "";
            alert("Habileté sauvegardée en base.");
        }
    })
    .catch(err => {
        alert("Erreur lors de l'ajout : " + err.message);
    });
}

function addSoftskillItemToDOM(activityId, hscName, hscLevel) {
    const container = document.getElementById('softskills-list-' + activityId);
    if (!container) return;
    const index = container.children.length;
    const levelLabel = translateLevelToText(hscLevel);

    const div = document.createElement('div');
    div.className = 'softskill-item';
    div.style.marginBottom = '5px';
    div.setAttribute('data-index', index);

    div.innerHTML = `
      <span class="softskill-text">${hscName} (Niveau: <span class="softskill-level">${levelLabel}</span>)</span>
      <i class="fas fa-pencil-alt edit-softskill" title="Modifier"></i>
      <i class="fas fa-trash delete-softskill" title="Supprimer"></i>
      <div class="edit-softskill-form" id="edit-softskill-form-${activityId}-${index}" style="display:none;">
        <label>Habileté :</label>
        <input type="text" id="edit-softskill-name-${activityId}-${index}" value="${hscName}" />
        <label>Niveau (1..4) :</label>
        <input type="number" min="1" max="4" id="edit-softskill-level-${activityId}-${index}" value="${hscLevel}" />
        <button onclick="submitEditSoftskill('${activityId}', ${index})">Enregistrer</button>
        <button onclick="hideEditSoftskillForm('${activityId}', ${index})">Annuler</button>
      </div>
    `;
    container.appendChild(div);
}

// Edition locale
$(document).on('click', '.edit-softskill', function() {
    const itemElem = $(this).closest('.softskill-item');
    const index = itemElem.data('index');
    const parentId = itemElem.parent().attr('id'); // ex: "softskills-list-<activityId>"
    const activityId = parentId.split('-')[2];
    showEditSoftskillForm(activityId, index);
});

function showEditSoftskillForm(activityId, index) {
    document.getElementById(`edit-softskill-form-${activityId}-${index}`).style.display = 'block';
}

function hideEditSoftskillForm(activityId, index) {
    document.getElementById(`edit-softskill-form-${activityId}-${index}`).style.display = 'none';
}

function submitEditSoftskill(activityId, index) {
    const nameInput = document.getElementById(`edit-softskill-name-${activityId}-${index}`);
    const levelInput = document.getElementById(`edit-softskill-level-${activityId}-${index}`);
    const newName = nameInput.value.trim();
    const newLevel = levelInput.value.trim();
    if(!newName) {
      alert("Veuillez saisir un nom d'habileté.");
      return;
    }
    if(!["1","2","3","4"].includes(newLevel)) {
      alert("Le niveau doit être 1, 2, 3 ou 4.");
      return;
    }
    const container = document.getElementById('softskills-list-' + activityId);
    const itemElem = container.querySelector(`.softskill-item[data-index="${index}"]`);
    const textElem = itemElem.querySelector('.softskill-text');
    const levelLabel = translateLevelToText(newLevel);

    textElem.innerHTML = `${newName} (Niveau: <span class="softskill-level">${levelLabel}</span>)`;
    hideEditSoftskillForm(activityId, index);
}

// Suppression locale (pas de DELETE /softskills/<id> ici, à vous de l'ajouter si souhaité)
$(document).on('click', '.delete-softskill', function() {
    if(!confirm("Voulez-vous supprimer cette habileté ?")) return;
    $(this).closest('.softskill-item').remove();
});
