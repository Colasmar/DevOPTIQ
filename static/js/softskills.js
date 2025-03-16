/**************************************************************
 * FICHIER : Code/static/js/softskills.js
 * Gère la logique front-end pour les habiletés socio-cognitives (HSC)
 * dans le contexte des activités (boutons "Proposer HSC" et "Traduire Softskills").
 * Version "robuste" : 
 *   - mapping des clés (si l'IA renvoie "Habilitéé" au lieu de "habilete")
 *   - conversion de niveau en string pour éviter l'erreur strip() côté backend.
 **************************************************************/

/**
 * Fonction appelée quand on clique sur "Proposer HSC".
 * Récupère les infos de l'activité via /activities/<id>/details, puis appelle proposeSoftskills().
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

/**
 * Appelle le back-end (/softskills/propose) pour générer des HSC.
 * Si aucune tâche n'est présente, le back-end renvoie "Saisissez d'abord des tâches".
 * On fait ensuite un "mapping" des clés pour éviter l'erreur 400 si l'IA renvoie "Habilité" ou "Niveau".
 * IMPORTANT : on convertit la valeur de niveau en string pour éviter l'erreur .strip() côté Python
 * si l'IA renvoie un entier.
 */
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

    // data = [ { habilete, niveau, justification } ] dans l'idéal,
    // mais l’IA peut renvoyer "Habilitéé", "Niveau": 3, etc.
    let addPromises = [];
    data.forEach(item => {
      // --- MAPPING : on trouve la bonne clé pour habilete, niveau, justification ---
      const rawHabilete = findClosestKey(item, ["habilete","habilite","habilité","habileté","Habilete","Habilité","Habilitéé"]);
      const rawNiveauVal = findClosestKey(item, ["niveau","Niveau","level"]); 
      // On force la conversion en chaîne :
      const rawNiveau = rawNiveauVal !== "" ? String(rawNiveauVal) : "";

      const rawJustif   = findClosestKey(item, ["justification","Justification","justif"]);

      // Valeurs par défaut si introuvables
      const habilete = rawHabilete || "Inconnue";
      const niveau   = rawNiveau   || "1";
      const justification = rawJustif || "";

      // On appelle /softskills/add en passant niveau en chaîne
      let p = fetch('/softskills/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity_id: activityData.id,
          habilete: habilete,
          niveau:   niveau,          // toujours une chaîne
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
      .catch(err => console.error("Erreur fetch /softskills/add:", err));

      addPromises.push(p);
    });
    return Promise.all(addPromises);
  })
  .then(() => {
    alert("Proposition de HSC terminée !");
  })
  .catch(err => {
    hideSpinner();
    console.error("Erreur lors de la proposition HSC :", err);
    alert("Impossible de proposer des HSC : " + err.message);
  });
}

/**
 * Ajoute ou met à jour une HSC dans le DOM, en évitant les doublons (même habilete).
 */
function addSoftskillItemToDOM(activityId, hscName, hscLevel, dbId, justification) {
  const container = document.getElementById('softskills-list-' + activityId);
  if (!container) return;

  const target = hscName.toLowerCase();
  let existingItem = null;
  container.querySelectorAll('.softskill-item').forEach(item => {
    if (item.getAttribute('data-habilete-lower') === target) {
      existingItem = item;
    }
  });

  const newLevelNum = parseInt(hscLevel) || 0;
  if (existingItem) {
    // Si l'item existe déjà, on compare les niveaux
    const levelElem = existingItem.querySelector('.softskill-level');
    const oldLevelNum = parseInt(levelElem ? levelElem.innerText : "0") || 0;
    if (newLevelNum > oldLevelNum) {
      levelElem.innerText = hscLevel;
      if (justification) {
        const justifElem = existingItem.querySelector('.softskill-justification');
        if (justifElem) {
          justifElem.innerText = justification;
        } else {
          const newJustifDiv = document.createElement('div');
          newJustifDiv.className = 'softskill-justification';
          newJustifDiv.innerText = justification;
          existingItem.appendChild(newJustifDiv);
        }
      }
    }
    return;
  }

  // Sinon, créer un nouvel item
  const div = document.createElement('div');
  div.className = 'softskill-item';
  div.style.marginBottom = '5px';
  div.setAttribute('data-ss-id', dbId);
  div.setAttribute('data-habilete-lower', target);

  let justificationHTML = justification
    ? `<div class="softskill-justification" style="font-size:0.9em; margin-top:3px; color:#444;">${justification}</div>`
    : '';

  div.innerHTML = `
    <span class="softskill-text">
      ${hscName} (Niveau: <span class="softskill-level">${hscLevel}</span>)
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

/* --- Édition / Suppression existantes --- */

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
        const textElem = itemElem.querySelector('.softskill-text');
        textElem.innerHTML = `${data.habilete} (Niveau: <span class="softskill-level">${data.niveau}</span>)`;
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

/* --- TRADUCTION DES SOFTSKILLS --- */

function openTranslateSoftskillsModal(activityId) {
  window.translateSoftskillsActivityId = activityId;
  document.getElementById('translateSoftskillsModal').style.display = 'block';
}

function closeTranslateSoftskillsModal() {
  document.getElementById('translateSoftskillsModal').style.display = 'none';
  window.translateSoftskillsActivityId = null;
}

function submitSoftskillsTranslation() {
  const activityId = window.translateSoftskillsActivityId;
  if (!activityId) {
    alert("Identifiant de l'activité introuvable.");
    return;
  }
  const userInputElem = document.getElementById('translateSoftskillsInput');
  const userInput = userInputElem.value.trim();
  if (!userInput) {
    alert("Veuillez saisir du texte.");
    return;
  }

  showSpinner();
  $.ajax({
    url: '/softskills/translate',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ user_input: userInput }),
    success: function(response) {
      hideSpinner();
      if (!response.proposals) {
        alert("Réponse inattendue : pas de 'proposals' !");
        return;
      }
      let addPromises = [];
      response.proposals.forEach(function(item) {
        // Mapping minimal pour la traduction aussi
        const rawHabilete = findClosestKey(item, ["habilete","habilite","habilité","habileté","Habilete","Habilité"]);
        const rawNiveauVal = findClosestKey(item, ["niveau","Niveau","level"]);
        // Convertit le niveau en string
        const rawNiveau = rawNiveauVal !== "" ? String(rawNiveauVal) : "";
        const rawJustif   = findClosestKey(item, ["justification","Justification","justif"]);

        const habilete = rawHabilete || "Inconnue";
        const niveau   = rawNiveau   || "1";
        const justification = rawJustif || "";

        let p = $.ajax({
          url: '/softskills/add',
          method: 'POST',
          contentType: 'application/json',
          data: JSON.stringify({
            activity_id: activityId,
            habilete: habilete,
            niveau:   niveau,  // toujours une chaîne
            justification: justification
          }),
          success: function(added) {
            if (added.error) {
              console.error("Erreur ajout HSC:", added.error);
            } else {
              addSoftskillItemToDOM(activityId, added.habilete, added.niveau, added.id, added.justification);
            }
          },
          error: function(err) {
            console.error("Erreur /softskills/add:", err);
          }
        });
        addPromises.push(p);
      });
      $.when.apply($, addPromises).then(function() {
        userInputElem.value = "";
        closeTranslateSoftskillsModal();
      });
    },
    error: function() {
      hideSpinner();
      alert("Erreur lors de la traduction des softskills.");
    }
  });
}

/**
 * findClosestKey(obj, possibleKeys)
 * Parcourt les clés de obj pour trouver la première qui ressemble
 * (en minuscules, sans accents) à l'une des possibleKeys.
 * Retourne la valeur de cette clé, ou "" si rien trouvé.
 */
function findClosestKey(obj, possibleKeys) {
  // Fonction locale pour normaliser une chaîne (minuscules, pas d'accents)
  const normalize = (s) => s
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "") // supprime accents
    .toLowerCase();

  // Parcourir toutes les clés de l'objet
  for (let key of Object.keys(obj)) {
    const normKey = normalize(key);
    // Pour chaque candidate
    for (let pk of possibleKeys) {
      const normPk = normalize(pk);
      // Si normKey contient normPk, on renvoie la valeur
      if (normKey.includes(normPk)) {
        return obj[key];
      }
    }
  }
  // Si rien trouvé
  return "";
}
