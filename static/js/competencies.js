// static/js/competencies.js

/**
 * Ajoute une compétence dans le DOM (après /skills/add).
 */
function addCompetencyItemToDOM(activityId, compId, description) {
    const container = document.getElementById(`competencies-list-${activityId}`);
    if (!container) return;
    const li = document.createElement('li');
    li.setAttribute('data-comp-id', compId);
    li.style.marginBottom = "5px";
    li.innerHTML = `
      <span class="validated-skill-text">${description}</span>
      <button onclick="editCompetency(this, ${compId})" style="margin-left:5px;">
        <i class="fa-solid fa-pencil"></i>
      </button>
      <button onclick="deleteCompetency(this, ${compId})" style="margin-left:5px;">
        <i class="fa-solid fa-trash"></i>
      </button>
      <div class="edit-competency-form" id="edit-competency-form-${compId}" style="display:none; margin-top:5px;">
        <label>Description :</label>
        <input type="text" id="edit-competency-desc-${compId}" value="${description}" />
        <button onclick="submitEditCompetency('${compId}')">Enregistrer</button>
        <button onclick="hideEditCompetencyForm('${compId}')">Annuler</button>
      </div>
    `;
    container.appendChild(li);
  }
  
  // Ouvre le formulaire d'édition
  function editCompetency(buttonElem, compId) {
    document.getElementById(`edit-competency-form-${compId}`).style.display = "block";
  }
  
  // Ferme le formulaire d'édition
  function hideEditCompetencyForm(compId) {
    document.getElementById(`edit-competency-form-${compId}`).style.display = "none";
  }
  
  // Soumet la mise à jour (PUT /skills/<compId>)
  function submitEditCompetency(compId) {
    const newDesc = document.getElementById(`edit-competency-desc-${compId}`).value.trim();
    if (!newDesc) {
      alert("Veuillez saisir une description.");
      return;
    }
    fetch(`/skills/${compId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: newDesc })
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        // On met à jour le texte dans le DOM
        const li = document.querySelector(`li[data-comp-id='${compId}']`);
        if (li) {
          li.querySelector('.validated-skill-text').textContent = data.description;
          hideEditCompetencyForm(compId);
          alert("Compétence mise à jour en base.");
        }
      }
    })
    .catch(err => {
      alert("Erreur lors de la mise à jour : " + err.message);
    });
  }
  
  // Supprime une compétence (DELETE /skills/<compId>)
  function deleteCompetency(buttonElem, compId) {
    if (!confirm("Confirmez-vous la suppression de cette compétence ?")) return;
    fetch(`/skills/${compId}`, { method: 'DELETE' })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        const li = buttonElem.parentNode;
        li.parentNode.removeChild(li);
        alert("Compétence supprimée.");
      }
    })
    .catch(err => {
      alert("Erreur lors de la suppression : " + err.message);
    });
  }
  