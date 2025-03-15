/*******************************************************
 * FICHIER : Code/static/js/competencies.js
 * Description :
 *    Gère l'ajout, la proposition et l'édition des
 *    compétences (API /skills).
 ******************************************************/

/**
 * Récupère les détails d'une activité (via /activities/<id>/details),
 * puis enchaîne sur la proposition de compétences par l'IA,
 * SANS afficher le spinner ici (pour ne pas créer de doublon).
 */
function fetchActivityDetailsForSkills(activityId) {
  // On NE met pas showSpinner() ici, pour ne pas bloquer cette requête rapide.
  fetch(`/activities/${activityId}/details`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Erreur lors de la récupération des détails de l'activité");
      }
      return response.json();
    })
    .then((activityData) => {
      // On passe ensuite à la proposition de compétences
      proposeSkills(activityData);
    })
    .catch((error) => {
      console.error("Erreur fetchActivityDetailsForSkills:", error);
      alert("Impossible de récupérer les détails de l'activité (voir console).");
    });
}

/**
 * Appelle l'IA pour proposer des compétences (POST /skills/propose),
 * en affichant un spinner pendant la durée de la requête.
 */
function proposeSkills(activityData) {
  // -- ICI on montre le spinner car l'appel à l'IA peut être plus long --
  showSpinner();

  fetch("/skills/propose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(activityData),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Réponse invalide de /skills/propose");
      }
      return response.json();
    })
    .then((data) => {
      if (data.error) {
        console.error("Erreur IA /skills/propose:", data.error);
        alert("Erreur IA : " + data.error);
        return;
      }
      // On récupère le tableau de propositions
      const proposals = data.proposals;
      if (!proposals || !Array.isArray(proposals)) {
        alert("Réponse inattendue : 'proposals' n'est pas un tableau.");
        return;
      }
      // Ouvre le modal (défini dans competency_modal.html) pour afficher ces phrases
      showProposalsModal(proposals, activityData.id);
    })
    .catch((err) => {
      console.error("Erreur lors de la proposition de compétences:", err);
      alert("Impossible d'obtenir des propositions de compétences (voir console).");
    })
    .finally(() => {
      // -- On masque le spinner quoi qu'il arrive --
      hideSpinner();
    });
}

/**
 * Ajout d'une compétence (POST /skills/add)
 * @param {number} activityId
 * @param {string} description
 */
function addCompetency(activityId, description) {
  showSpinner();
  fetch("/skills/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ activity_id: activityId, description: description }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        console.error("Erreur addCompetency:", data.error);
        alert("Erreur en ajoutant la compétence : " + data.error);
      } else {
        addCompetencyItemToDOM(activityId, data.id, data.description);
      }
    })
    .catch((error) => {
      console.error("Erreur /skills/add:", error);
      alert("Impossible d'ajouter la compétence (voir console).");
    })
    .finally(() => {
      hideSpinner();
    });
}

/**
 * Ajoute une entrée (li) dans le DOM, dans la liste #competencies-list-<activityId>
 * @param {number} activityId
 * @param {number} compId
 * @param {string} desc
 */
function addCompetencyItemToDOM(activityId, compId, desc) {
  const ul = document.getElementById(`competencies-list-${activityId}`);
  if (!ul) {
    console.warn("Impossible de trouver le UL pour activityId=", activityId);
    return;
  }

  const li = document.createElement("li");
  li.setAttribute("data-comp-id", compId);
  li.style.marginBottom = "5px";

  const span = document.createElement("span");
  span.className = "validated-skill-text";
  span.textContent = desc;

  // Bouton éditer
  const editBtn = document.createElement("button");
  editBtn.style.marginLeft = "5px";
  editBtn.innerHTML = '<i class="fa-solid fa-pencil"></i>';
  editBtn.onclick = function () {
    editCompetency(this, compId);
  };

  // Bouton supprimer
  const delBtn = document.createElement("button");
  delBtn.style.marginLeft = "5px";
  delBtn.innerHTML = '<i class="fa-solid fa-trash"></i>';
  delBtn.onclick = function () {
    deleteCompetency(this, compId);
  };

  // Formulaire d'édition local (caché)
  const formDiv = document.createElement("div");
  formDiv.className = "edit-competency-form";
  formDiv.id = `edit-competency-form-${compId}`;
  formDiv.style.display = "none";
  formDiv.style.marginTop = "5px";
  formDiv.innerHTML = `
    <label>Description :</label>
    <input type="text" id="edit-competency-desc-${compId}" value="${desc}" />
    <button onclick="submitEditCompetency('${compId}')">Enregistrer</button>
    <button onclick="hideEditCompetencyForm('${compId}')">Annuler</button>
  `;

  li.appendChild(span);
  li.appendChild(editBtn);
  li.appendChild(delBtn);
  li.appendChild(formDiv);
  ul.appendChild(li);
}

/**
 * Prépare l'édition d'une compétence
 */
function editCompetency(btnElem, compId) {
  const formId = `edit-competency-form-${compId}`;
  const formDiv = document.getElementById(formId);
  if (!formDiv) return;
  formDiv.style.display = "block";
}

/**
 * Soumet la modification d'une compétence vers /skills/<compId> (PUT)
 */
function submitEditCompetency(compId) {
  const input = document.getElementById(`edit-competency-desc-${compId}`);
  if (!input) return;

  const newDesc = input.value.trim();
  if (!newDesc) {
    alert("La description ne peut pas être vide.");
    return;
  }
  showSpinner();
  fetch(`/skills/${compId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description: newDesc }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        console.error("Erreur update_competency:", data.error);
        alert("Erreur mise à jour compétence: " + data.error);
      } else {
        // Mettre à jour le texte affiché
        const li = document.querySelector(`li[data-comp-id="${compId}"]`);
        if (li) {
          const span = li.querySelector(".validated-skill-text");
          if (span) {
            span.textContent = data.description;
          }
        }
        hideEditCompetencyForm(compId);
      }
    })
    .catch((error) => {
      console.error("Erreur submitEditCompetency:", error);
      alert("Impossible de mettre à jour la compétence (voir console).");
    })
    .finally(() => {
      hideSpinner();
    });
}

/**
 * Cache le formulaire d'édition
 */
function hideEditCompetencyForm(compId) {
  const formId = `edit-competency-form-${compId}`;
  const formDiv = document.getElementById(formId);
  if (formDiv) {
    formDiv.style.display = "none";
  }
}

/**
 * Supprime une compétence (DELETE /skills/<compId>)
 */
function deleteCompetency(btnElem, compId) {
  if (!confirm("Supprimer cette compétence ?")) return;
  showSpinner();
  fetch(`/skills/${compId}`, {
    method: "DELETE",
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        console.error("Erreur delete_competency:", data.error);
        alert("Erreur suppression compétence: " + data.error);
      } else {
        // Retirer l'élément du DOM
        const li = document.querySelector(`li[data-comp-id="${compId}"]`);
        if (li) {
          li.remove();
        }
      }
    })
    .catch((error) => {
      console.error("Erreur deleteCompetency:", error);
      alert("Impossible de supprimer la compétence (voir console).");
    })
    .finally(() => {
      hideSpinner();
    });
}
