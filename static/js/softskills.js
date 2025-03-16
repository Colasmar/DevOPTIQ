/**************************************************************
 * FICHIER : Code/static/js/softskills.js
 * Gère la logique front-end pour les habiletés socio-cognitives (HSC)
 * dans le contexte des activités (boutons "Proposer HSC" et "Traduire Softskills").
 **************************************************************/

/**
 * Convertit la valeur numérique du niveau (1..4) en texte selon la norme :
 * 1 -> aptitude
 * 2 -> acquisition
 * 3 -> maîtrise
 * 4 -> excellence
 */
function levelToLabel(lvl) {
  switch (lvl) {
    case "1": return "aptitude";
    case "2": return "acquisition";
    case "3": return "maîtrise";
    case "4": return "excellence";
    default:  return lvl;
  }
}

/**
 * ================================
 *   FONCTION "PROPOSER HSC"
 * ================================
 * Elle récupère les infos de l'activité, puis appelle /softskills/propose
 */
function fetchActivityDetailsForSoftskills(activityId) {
  showSpinner();
  fetch(`/activities/${activityId}/details`)
    .then(response => {
      if (!response.ok) {
        hideSpinner();
        throw new Error("Impossible de récupérer les détails de l'activité");
      }
      return response.json();
    })
    .then(activityData => {
      hideSpinner();
      proposeSoftskills(activityData);
    })
    .catch(error => {
      hideSpinner();
      alert("Erreur : " + error.message);
    });
}

function proposeSoftskills(activityData) {
  showSpinner();
  fetch('/softskills/propose', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(activityData)
  })
  .then(response => {
    if (!response.ok) hideSpinner();
    return response.json();
  })
  .then(data => {
    hideSpinner();
    if (data.error) {
      alert("Erreur : " + data.error);
      return;
    }
    // data = tableau d'objets { habilete, niveau, justification }
    let addPromises = [];
    data.forEach(item => {
      // MAPPING : on cherche la bonne clé "habilete", "niveau", "justification"
      const rawHabilete = findClosestKey(item, ["habilete","habilite","habilité","habileté"]);
      const rawNiveauVal = findClosestKey(item, ["niveau","Niveau","level"]);
      const rawJustif = findClosestKey(item, ["justification","Justification","justif"]);

      const habilete = rawHabilete || "Inconnue";
      const niveau = rawNiveauVal ? String(rawNiveauVal) : "1";
      const justification = rawJustif || "";

      let p = fetch('/softskills/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity_id: activityData.id,
          habilete: habilete,
          niveau:   niveau,
          justification: justification
        })
      })
      .then(r => r.json())
      .then(added => {
        if (!added.error) {
          addSoftskillItemToDOM(activityData.id, added.habilete, added.niveau, added.id, added.justification);
        } else {
          console.error("Erreur ajout HSC:", added.error);
        }
      })
      .catch(err => console.error("Erreur /softskills/add:", err));

      addPromises.push(p);
    });
    return Promise.all(addPromises);
  })
  .then(() => {
    alert("Proposition de HSC terminée !");
  })
  .catch(err => {
    hideSpinner();
    alert("Erreur lors de la proposition HSC : " + err.message);
  });
}

/**
 * ================================
 *   FONCTION "TRADUIRE SOFTSKILLS"
 * ================================
 * On récupère d'abord l'activité, puis on appelle /softskills/translate
 * en passant user_input et activity_data
 */
function submitSoftskillsTranslation() {
  const activityId = window.translateSoftskillsActivityId;
  if (!activityId) {
    alert("Aucun ID d'activité n'est défini pour la traduction.");
    return;
  }
  const userInputElem = document.getElementById('translateSoftskillsInput');
  const userInput = userInputElem.value.trim();
  if (!userInput) {
    alert("Veuillez saisir des softskills en langage naturel.");
    return;
  }

  showSpinner();

  // 1) Récupération de l'activité
  fetch(`/activities/${activityId}/details`)
    .then(res => {
      if (!res.ok) throw new Error("Impossible de récupérer les détails de l'activité");
      return res.json();
    })
    .then(activityData => {
      // 2) Appel à /softskills/translate
      return fetch('/softskills/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_input: userInput,
          activity_data: activityData
        })
      });
    })
    .then(r => r.json())
    .then(data => {
      hideSpinner();
      if (!data.proposals) {
        alert("Réponse inattendue : pas de 'proposals' !");
        return;
      }
      // 3) On ajoute chaque proposition
      let addPromises = [];
      data.proposals.forEach(item => {
        const rawHabilete = findClosestKey(item, ["habilete","habilite","habilité","habileté"]);
        const rawNiveauVal = findClosestKey(item, ["niveau","Niveau","level"]);
        const rawJustif = findClosestKey(item, ["justification","Justification","justif"]);

        const habilete = rawHabilete || "Inconnue";
        const niveau   = rawNiveauVal ? String(rawNiveauVal) : "1";
        const justification = rawJustif || "";

        let p = fetch('/softskills/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            activity_id: activityId,
            habilete: habilete,
            niveau:   niveau,
            justification: justification
          })
        })
        .then(rr => rr.json())
        .then(added => {
          if (added.error) {
            console.error("Erreur ajout HSC:", added.error);
          } else {
            addSoftskillItemToDOM(activityId, added.habilete, added.niveau, added.id, added.justification);
          }
        })
        .catch(err => console.error("Erreur /softskills/add:", err));

        addPromises.push(p);
      });
      // 4) On vide le champ et on ferme le modal
      return Promise.all(addPromises).then(() => {
        userInputElem.value = "";
        closeTranslateSoftskillsModal();
      });
    })
    .catch(err => {
      hideSpinner();
      alert("Erreur lors de la traduction des softskills : " + err.message);
      console.error(err);
    });
}

/**
 * ================================
 *    AJOUT / MISE À JOUR DOM
 * ================================
 * Ajoute ou met à jour une HSC dans le DOM, en évitant les doublons
 */
function addSoftskillItemToDOM(activityId, hscName, hscLevel, dbId, justification) {
  const container = document.getElementById('softskills-list-' + activityId);
  if (!container) return;

  const label = levelToLabel(hscLevel);
  const target = hscName.toLowerCase();
  let existingItem = null;
  container.querySelectorAll('.softskill-item').forEach(item => {
    if (item.getAttribute('data-habilete-lower') === target) {
      existingItem = item;
    }
  });

  if (existingItem) {
    // Mise à jour
    const levelElem = existingItem.querySelector('.softskill-level');
    levelElem.innerText = label;

    if (justification) {
      let justifElem = existingItem.querySelector('.softskill-justification');
      if (!justifElem) {
        justifElem = document.createElement('div');
        justifElem.className = 'softskill-justification';
        justifElem.style.fontSize = "0.9em";
        justifElem.style.marginTop = "3px";
        justifElem.style.color = "#444";
        existingItem.appendChild(justifElem);
      }
      justifElem.innerText = justification;
    }
    return;
  }

  // Sinon, création
  const div = document.createElement('div');
  div.className = 'softskill-item';
  div.style.marginBottom = '5px';
  div.setAttribute('data-ss-id', dbId);
  div.setAttribute('data-habilete-lower', target);

  const justificationHTML = justification
    ? `<div class="softskill-justification" style="font-size:0.9em; margin-top:3px; color:#444;">${justification}</div>`
    : '';

  div.innerHTML = `
    <span class="softskill-text">
      ${hscName} (Niveau: <span class="softskill-level">${label}</span>)
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
 * ================================
 *    ÉDITION / SUPPRESSION
 * ================================
 */
// Édition
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
      const itemElem = document.querySelector(`.softskill-item[data-ss-id='${dbId}']`);
      if (itemElem) {
        const label = levelToLabel(data.niveau);
        const textElem = itemElem.querySelector('.softskill-text');
        if (textElem) {
          textElem.innerHTML = `${data.habilete} (Niveau: <span class="softskill-level">${label}</span>)`;
        }
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

/**
 * ================================
 *   OUTILS DIVERS
 * ================================
 */

/**
 * findClosestKey(obj, possibleKeys)
 * Cherche la première clé de obj qui ressemble (en minuscules, sans accents) à l'une de possibleKeys.
 * Retourne la valeur, ou "" si non trouvée.
 */
function findClosestKey(obj, possibleKeys) {
  const normalize = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

  for (let key of Object.keys(obj)) {
    const normKey = normalize(key);
    for (let pk of possibleKeys) {
      const normPk = normalize(pk);
      if (normKey.includes(normPk)) {
        return obj[key];
      }
    }
  }
  return "";
}
