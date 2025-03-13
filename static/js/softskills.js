/**************************************************************
 * softskills.js
 * Gère la logique front-end pour les habiletés socio-cognitives (HSC)
 * dans le contexte des activités (bouton "Proposer HSC").
 *
 * L'appel à /softskills/propose se fait depuis proposeSoftskills(activityId).
 * => Nous affichons un spinner et ajoutons la justification.
 **************************************************************/

// Récupère le texte "détails" d'une activité (pour l'IA)
function getActivityDetails(activityId) {
  const detailsElem = document.getElementById('details-' + activityId);
  return detailsElem ? detailsElem.innerText : "";
}

// Récupère la liste des compétences associées à l'activité (texte brut)
function getCompetenciesData(activityId) {
  const compElem = document.getElementById('competencies-list-' + activityId);
  if (!compElem) return "";
  let items = [];
  compElem.querySelectorAll('li').forEach(li => items.push(li.textContent.trim()));
  return items.join(", ");
}

// Convertit un niveau "1..4" en libellé
function translateLevelToText(level) {
  switch(level) {
    case "1": return "Aptitude";
    case "2": return "Acquisition";
    case "3": return "Maîtrise";
    case "4": return "Excellence";
    default:  return "Inconnu";
  }
}

// Convertit un libellé éventuel en un nombre (pour comparer)
function parseLevelToNumber(level) {
  // "1","2","3","4" => num
  // ou "Aptitude","Acquisition", etc => on renvoie le num correspondant
  switch(level.toLowerCase()) {
    case "1": case "aptitude":        return 1;
    case "2": case "acquisition":     return 2;
    case "3": case "maîtrise":        return 3;
    case "4": case "excellence":      return 4;
  }
  // Essai d'extraire un chiffre
  let n = parseInt(level);
  if (!isNaN(n)) return n;
  return 0;
}

// Bouton "Proposer HSC" : on appelle proposeSoftskills(activityId)
$(document).on('click', '.define-hsc-btn', function() {
  const activityId = $(this).data('activity-id');
  proposeSoftskills(activityId);
});

/**
 * Fonction principale pour proposer des HSC via /softskills/propose
 * 1) Récupère le contexte (détails activité, compétences existantes)
 * 2) Appelle /softskills/propose
 * 3) Pour chaque HSC renvoyée => /softskills/add
 * 4) Ajoute la HSC dans le DOM (sans doublon, justification incluse)
 */
function proposeSoftskills(activityId) {
  const activityData = getActivityDetails(activityId);
  const competenciesData = getCompetenciesData(activityId);

  showSpinner();
  fetch('/softskills/propose', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      activity: activityData,
      competencies: competenciesData
    })
  })
  .then(res => {
    if (!res.ok) hideSpinner();
    return res.json();
  })
  .then(data => {
    if (data.error) {
      hideSpinner();
      alert(data.error);
      return;
    }
    // data = [ { habilete, niveau, justification }, ... ]
    let addPromises = [];
    data.forEach(item => {
      let p = fetch('/softskills/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity_id: activityId,
          habilete: item.habilete,
          niveau: item.niveau,
          justification: item.justification
        })
      })
      .then(r => r.json())
      .then(added => {
        if (!added.error) {
          addSoftskillItemToDOM(activityId, added.habilete, added.niveau, added.id, added.justification);
        } else {
          console.error("Erreur ajout HSC:", added.error);
        }
      })
      .catch(err => console.error("Erreur fetch /softskills/add:", err));

      addPromises.push(p);
    });
    return Promise.all(addPromises);
  })
  .then(() => {
    hideSpinner();
    alert("Proposition de HSC terminée !");
  })
  .catch(err => {
    hideSpinner();
    alert("Erreur lors de la proposition HSC : " + err.message);
  });
}

/**
 * Ajoute (ou met à jour) une HSC dans le DOM en évitant les doublons
 * @param activityId
 * @param hscName
 * @param hscLevel
 * @param dbId
 * @param justification
 */
function addSoftskillItemToDOM(activityId, hscName, hscLevel, dbId, justification) {
  const container = document.getElementById('softskills-list-' + activityId);
  if (!container) return;

  // 1) Chercher si une HSC du même nom existe déjà
  const existing = findSoftskillItemByName(container, hscName);
  const newNumLevel = parseLevelToNumber(hscLevel);

  if (existing) {
    // On compare les niveaux, si le nouveau est plus élevé, on met à jour
    const existingLevelElem = existing.querySelector('.softskill-level');
    const existingLevelText = existingLevelElem ? existingLevelElem.innerText.trim() : "";
    const existingNumLevel = parseLevelToNumber(existingLevelText);

    if (newNumLevel > existingNumLevel) {
      // Mettre à jour le texte
      existingLevelElem.innerText = translateLevelToText(hscLevel);

      // Mettre à jour la justification si on le souhaite
      if (justification && justification.trim() !== "") {
        const justifElem = existing.querySelector('.softskill-justif');
        if (justifElem) {
          justifElem.innerText = justification;
        } else {
          // Ajouter un bloc justification
          const newJustifDiv = document.createElement('div');
          newJustifDiv.className = 'softskill-justif';
          newJustifDiv.style.cssText = 'font-size:0.9em; margin-top:3px; color:#444;';
          newJustifDiv.innerText = "Justification : " + justification;
          existing.insertBefore(newJustifDiv, existing.querySelector('.edit-softskill-form'));
        }
      }
    }
    // On ne crée pas de doublon
    return;
  }

  // 2) Sinon, créer un nouvel item
  const levelLabel = translateLevelToText(hscLevel);
  const div = document.createElement('div');
  div.className = 'softskill-item';
  div.style.marginBottom = '5px';
  div.setAttribute('data-ss-id', dbId);

  // Optionnel: stocker le nom en data pour retrouver l'item
  div.setAttribute('data-habilete-lower', hscName.toLowerCase());

  let justificationHTML = "";
  if (justification && justification.trim() !== "") {
    justificationHTML = `
      <div class="softskill-justif" style="font-size:0.9em; margin-top:3px; color:#444;">
        Justification : ${justification}
      </div>
    `;
  }

  div.innerHTML = `
    <span class="softskill-text">
      ${hscName} (Niveau: <span class="softskill-level">${levelLabel}</span>)
    </span>
    ${justificationHTML}
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

/**
 * Trouve un item .softskill-item dont le nom est hscName (ignorer la casse).
 * Retourne l'élément correspondant ou null.
 */
function findSoftskillItemByName(containerElem, hscName) {
  const target = hscName.toLowerCase();
  const items = containerElem.querySelectorAll('.softskill-item');
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const stored = item.getAttribute('data-habilete-lower');
    if (stored && stored === target) {
      return item;
    }
  }
  return null;
}

// Edition (icône crayon)
$(document).on('click', '.edit-softskill', function() {
  const itemElem = $(this).closest('.softskill-item');
  const dbId = itemElem.data('ss-id');
  document.getElementById(`edit-softskill-form-${dbId}`).style.display = 'block';
});

function hideEditSoftskillForm(dbId) {
  document.getElementById(`edit-softskill-form-${dbId}`).style.display = 'none';
}

function submitEditSoftskillFromDOM(dbId) {
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
    if (data.error) {
      alert("Erreur : " + data.error);
    } else {
      // On met à jour l'affichage
      const itemElem = document.querySelector(`.softskill-item[data-ss-id='${dbId}']`);
      if (itemElem) {
        const textElem = itemElem.querySelector('.softskill-text');
        const levelLabel = translateLevelToText(data.niveau);
        textElem.innerHTML = `${data.habilete} (Niveau: <span class="softskill-level">${levelLabel}</span>)`;

        // Mettre à jour la justification s'il y en a une
        // (data.justification si tu veux la récupérer)
        // ...
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

// Suppression (icône poubelle)
$(document).on('click', '.delete-softskill', function() {
  const itemElem = $(this).closest('.softskill-item');
  const dbId = itemElem.data('ss-id');
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
