/**************************************************************
 * FICHIER : Code/static/js/softskills.js
 * Objet : Gérer le CRUD (ajout, mise à jour, suppression) des HSC
 *         + proposer HSC (appel IA)
 **************************************************************/

/**
 * Convertit la valeur numérique du niveau (1..4) en texte :
 * 1 -> aptitude, 2 -> acquisition, 3 -> maîtrise, 4 -> excellence
 */
function levelToLabel(lvl) {
  switch (lvl) {
    case "1": return "aptitude";
    case "2": return "acquisition";
    case "3": return "maîtrise";
    case "4": return "excellence";
    default:  return lvl; // fallback
  }
}

/**
 * Extrait la partie numérique d'une chaîne (ex: "2 (acquisition)" => "2").
 */
function extractNumericLevel(levelStr) {
  const match = levelStr.match(/\d/);
  return match ? match[0] : "1";
}

/* -------------------------------------------------------------------
   AJOUT / MISE À JOUR / SUPPRESSION HSC
   ------------------------------------------------------------------- */

/**
 * Ajoute ou met à jour une HSC dans le DOM (si on veut l'insérer manuellement).
 */
function addSoftskillItemToDOM(activityId, hscName, hscLevel, dbId, justification) {
  const container = document.getElementById('softskills-list-' + activityId);
  if (!container) return;

  const numericVal = extractNumericLevel(hscLevel);
  const label = levelToLabel(numericVal);

  // Chercher s'il existe déjà une HSC du même nom
  const targetNameLower = hscName.toLowerCase();
  let existingItem = null;
  container.querySelectorAll('.softskill-item').forEach(item => {
    if (item.getAttribute('data-habilete-lower') === targetNameLower) {
      existingItem = item;
    }
  });

  if (existingItem) {
    // Mettre à jour
    const levelElem = existingItem.querySelector('.softskill-level');
    if (levelElem) levelElem.innerText = label;
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

  // Sinon, créer un nouvel élément
  const div = document.createElement('div');
  div.className = 'softskill-item';
  div.style.marginBottom = '5px';
  div.setAttribute('data-ss-id', dbId);
  div.setAttribute('data-habilete-lower', targetNameLower);

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
      <input type="number" min="1" max="4" id="edit-softskill-level-${dbId}" value="${numericVal}" />
      <button onclick="submitEditSoftskillFromDOM('${dbId}')">Enregistrer</button>
      <button onclick="hideEditSoftskillForm('${dbId}')">Annuler</button>
    </div>
  `;
  container.appendChild(div);
}

/**
 * Événement : clic sur crayon => affiche le mini-formulaire
 */
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('edit-softskill')) {
    e.preventDefault();
    const itemElem = e.target.closest('.softskill-item');
    if (!itemElem) return;
    const dbId = itemElem.getAttribute('data-ss-id');
    const form = document.getElementById(`edit-softskill-form-${dbId}`);
    if (form) form.style.display = 'block';
  }
});

/**
 * Cache le formulaire d'édition
 */
function hideEditSoftskillForm(dbId) {
  const form = document.getElementById(`edit-softskill-form-${dbId}`);
  if (form) form.style.display = 'none';
}

/**
 * Soumet la modification via PUT /softskills/<dbId>
 */
function submitEditSoftskillFromDOM(dbId) {
  const newName = document.getElementById(`edit-softskill-name-${dbId}`).value.trim();
  const newNum = document.getElementById(`edit-softskill-level-${dbId}`).value.trim();

  if (!newName) {
    alert("Veuillez saisir un nom d'habileté.");
    return;
  }
  if (!["1","2","3","4"].includes(newNum)) {
    alert("Le niveau doit être 1..4.");
    return;
  }
  const labelVal = levelToLabel(newNum);
  const combined = newNum + " (" + labelVal + ")";

  showSpinner();
  fetch(`/softskills/${dbId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      habilete: newName,
      niveau: combined
    })
  })
  .then(res => res.json())
  .then(data => {
    hideSpinner();
    if (data.error) {
      alert("Erreur : " + data.error);
    } else {
      // Mettre à jour dans le DOM
      const itemElem = document.querySelector(`.softskill-item[data-ss-id='${dbId}']`);
      if (itemElem) {
        const numericVal = extractNumericLevel(data.niveau);
        const label = levelToLabel(numericVal);
        const textElem = itemElem.querySelector('.softskill-text');
        if (textElem) {
          textElem.innerHTML = `${data.habilete} (Niveau: <span class="softskill-level">${label}</span>)`;
        }
      }
      hideEditSoftskillForm(dbId);
      alert("HSC mise à jour.");
    }
  })
  .catch(err => {
    hideSpinner();
    alert("Erreur lors de la mise à jour : " + err);
  });
}

/**
 * Événement : clic sur poubelle => DELETE /softskills/<dbId>
 */
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('delete-softskill')) {
    e.preventDefault();
    const itemElem = e.target.closest('.softskill-item');
    if (!itemElem) return;
    const dbId = itemElem.getAttribute('data-ss-id');
    if (!confirm("Supprimer cette habileté ?")) return;
    showSpinner();
    fetch(`/softskills/${dbId}`, { method: 'DELETE' })
    .then(res => res.json())
    .then(data => {
      hideSpinner();
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        itemElem.remove();
      }
    })
    .catch(err => {
      hideSpinner();
      alert("Erreur lors de la suppression : " + err);
    });
  }
});


/* -------------------------------------------------------------------
   PROPOSER HSC (appel IA) : évite l’erreur 'int' object => data.get
   ------------------------------------------------------------------- */

/**
 * Récupère d’abord /activities/<id>/details,
 * puis envoie le JSON à /propose_softskills/propose
 */
function fetchActivityDetailsForPropose(activityId) {
  showSpinner();
  fetch(`/activities/${activityId}/details`)
    .then(resp => resp.json())
    .then(data => {
      hideSpinner();
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        proposeSoftskillsIA(data);
      }
    })
    .catch(err => {
      hideSpinner();
      alert("Erreur lors de la récupération de l'activité : " + err);
    });
}

/**
 * Envoie la structure d'activité à l'IA via /propose_softskills/propose
 */
function proposeSoftskillsIA(activityData) {
  showSpinner();
  fetch('/propose_softskills/propose', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(activityData)
  })
  .then(resp => resp.json())
  .then(data => {
    hideSpinner();
    if (data.error) {
      alert("Erreur IA : " + data.error);
    } else {
      // data.proposals => tableau d'objets {habilete, niveau, justification}
      insertProposedHSC(activityData.id, data.proposals);
    }
  })
  .catch(err => {
    hideSpinner();
    alert("Erreur propose_softskills/propose : " + err);
  });
}

/**
 * Insère les HSC proposées dans la base, via /softskills/add
 * puis les affiche dans le DOM.
 */
function insertProposedHSC(activityId, proposals) {
  if (!Array.isArray(proposals)) {
    alert("Réponse inattendue : proposals n'est pas un tableau.");
    return;
  }
  let addPromises = [];
  proposals.forEach(p => {
    const bodyData = {
      activity_id: activityId,
      habilete: p.habilete,
      niveau: p.niveau,
      justification: p.justification || ""
    };
    let pr = fetch('/softskills/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyData)
    })
    .then(res => res.json())
    .then(data => {
      if (!data.error) {
        addSoftskillItemToDOM(activityId, data.habilete, data.niveau, data.id, data.justification);
      }
    })
    .catch(err => console.error("Erreur /softskills/add:", err));
    addPromises.push(pr);
  });
  Promise.all(addPromises).then(() => {
    alert("Propositions HSC ajoutées avec succès.");
  });
}
