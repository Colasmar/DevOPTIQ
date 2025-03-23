/**************************************************************
 * FICHIER : Code/static/js/softskills.js
 * Objet : Gérer le CRUD (ajout, mise à jour, suppression) des HSC
 *         et insérer/mettre à jour ces habiletés dans le DOM.
 *
 * Remarque :
 *  - Cette version évite l'erreur "cannot be parsed" en n'injectant
 *    QUE la partie numérique dans <input type="number">.
 *  - On continue à stocker, si on le souhaite, "4 (excellence)" en base
 *    pour garder le label.
 **************************************************************/

/**
 * Convertit la valeur numérique du niveau (1..4) en texte selon votre logique :
 *  1 -> aptitude
 *  2 -> acquisition
 *  3 -> maîtrise
 *  4 -> excellence
 */
function levelToLabel(lvl) {
  switch (lvl) {
    case "1": return "aptitude";
    case "2": return "acquisition";
    case "3": return "maîtrise";
    case "4": return "excellence";
    default:  return lvl; // par défaut, on renvoie tel quel
  }
}

/**
 * Fonction utilitaire pour extraire la partie numérique
 * d'un niveau qui peut être "2 (acquisition)" ou "4 - expertise", etc.
 * Si aucun chiffre trouvé, on renvoie "1" par défaut.
 */
function extractNumericLevel(levelStr) {
  const match = levelStr.match(/\d/);
  return match ? match[0] : "1";
}

/**
 * Ajoute ou met à jour une HSC (habileté) dans le DOM, pour l'activité donnée.
 *
 * @param {number} activityId  L'ID de l'activité
 * @param {string} hscName     Le nom (habilete) de la HSC
 * @param {string} hscLevel    Le niveau tel que renvoyé par l'API (ex: "2 (acquisition)")
 * @param {number} dbId        L'ID de la HSC dans la base
 * @param {string} justification (facultatif)
 */
function addSoftskillItemToDOM(activityId, hscName, hscLevel, dbId, justification) {
  const container = document.getElementById('softskills-list-' + activityId);
  if (!container) return;

  // -- On extrait la partie numérique pour l'input, et on convertit pour l'affichage
  const numericVal = extractNumericLevel(hscLevel);  // ex: "4"
  const label      = levelToLabel(numericVal);       // ex: "excellence"

  // Vérifier si on a déjà une HSC du même nom (insensible à la casse)
  const targetNameLower = hscName.toLowerCase();
  let existingItem = null;
  container.querySelectorAll('.softskill-item').forEach(item => {
    if (item.getAttribute('data-habilete-lower') === targetNameLower) {
      existingItem = item;
    }
  });

  // Si la HSC existe déjà, on met simplement à jour le niveau/justification
  if (existingItem) {
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

  // Sinon, on crée un nouvel élément .softskill-item
  const div = document.createElement('div');
  div.className = 'softskill-item';
  div.style.marginBottom = '5px';
  div.setAttribute('data-ss-id', dbId);
  div.setAttribute('data-habilete-lower', targetNameLower);

  // Justification éventuelle
  const justificationHTML = justification
    ? `<div class="softskill-justification" style="font-size:0.9em; margin-top:3px; color:#444;">${justification}</div>`
    : '';

  // Construction du HTML à insérer
  div.innerHTML = `
    <span class="softskill-text">
      ${hscName} (Niveau: <span class="softskill-level">${label}</span>)
    </span>
    ${justificationHTML}
    <i class="fas fa-pencil-alt edit-softskill" title="Modifier"></i>
    <i class="fas fa-trash delete-softskill" title="Supprimer"></i>

    <!-- Formulaire d'édition caché -->
    <div class="edit-softskill-form" id="edit-softskill-form-${dbId}" style="display:none;">
      <label>Habileté :</label>
      <input type="text" id="edit-softskill-name-${dbId}" value="${hscName}" />
      <label>Niveau (1..4) :</label>
      <input type="number" min="1" max="4"
             id="edit-softskill-level-${dbId}"
             value="${numericVal}" />
      <button onclick="submitEditSoftskillFromDOM('${dbId}')">Enregistrer</button>
      <button onclick="hideEditSoftskillForm('${dbId}')">Annuler</button>
    </div>
  `;
  container.appendChild(div);
}

/**
 * Événement : clic sur l'icône crayon pour éditer => on affiche le formulaire
 */
$(document).on('click', '.edit-softskill', function() {
  const itemElem = $(this).closest('.softskill-item');
  const dbId = itemElem.data('ss-id');
  document.getElementById(`edit-softskill-form-${dbId}`).style.display = 'block';
});

/**
 * Cache le formulaire d'édition d'une HSC.
 */
function hideEditSoftskillForm(dbId) {
  document.getElementById(`edit-softskill-form-${dbId}`).style.display = 'none';
}

/**
 * Soumet la modification (PUT /softskills/<dbId>) et met à jour le DOM.
 * Ici, on recompose "4 (excellence)" avant l'envoi pour garder
 * la compatibilité avec le backend qui stocke la chaîne complète.
 */
function submitEditSoftskillFromDOM(dbId) {
  const newName = document.getElementById(`edit-softskill-name-${dbId}`).value.trim();
  const newNum  = document.getElementById(`edit-softskill-level-${dbId}`).value.trim();

  if (!newName) {
    alert("Veuillez saisir un nom d'habileté.");
    return;
  }
  if (!["1","2","3","4"].includes(newNum)) {
    alert("Le niveau doit être 1, 2, 3 ou 4.");
    return;
  }

  // On reconstitue la chaîne stockée en base, ex: "4 (excellence)"
  const labelVal = levelToLabel(newNum);
  const combined = newNum + " (" + labelVal + ")";

  fetch(`/softskills/${dbId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      habilete: newName,
      niveau: combined  // ex: "4 (excellence)"
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      alert("Erreur : " + data.error);
    } else {
      const itemElem = document.querySelector(`.softskill-item[data-ss-id='${dbId}']`);
      if (itemElem) {
        // Extraire la nouvelle valeur renvoyée par l'API
        // (elle peut être "4 (excellence)" ou identique)
        const numericVal = extractNumericLevel(data.niveau);
        const label = levelToLabel(numericVal);

        // Mettre à jour l'affichage du nom + niveau
        const textElem = itemElem.querySelector('.softskill-text');
        if (textElem) {
          textElem.innerHTML = `${data.habilete} (Niveau: <span class="softskill-level">${label}</span>)`;
        }
      }
      hideEditSoftskillForm(dbId);
      alert("HSC mise à jour en base.");
    }
  })
  .catch(err => {
    alert("Erreur lors de la mise à jour : " + err.message);
    console.error(err);
  });
}

/**
 * Événement : clic sur l'icône poubelle => suppression (DELETE /softskills/<dbId>)
 */
$(document).on('click', '.delete-softskill', function() {
  const itemElem = $(this).closest('.softskill-item');
  const dbId = itemElem.data('ss-id');
  if (!confirm("Voulez-vous supprimer cette habileté ?")) return;

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

