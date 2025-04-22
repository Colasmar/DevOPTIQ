// Code/static/js/savoirs.js

/**
 * Récupère les détails d'une activité (via /activities/<id>/details),
 * puis enchaîne sur la proposition de savoirs IA.
 */


/* Ajout direct d'un savoir */
function showAddSavoirForm(activityId) {
  document.getElementById("add-savoir-form-" + activityId).style.display = "block";
}

function hideAddSavoirForm(activityId) {
  document.getElementById("add-savoir-form-" + activityId).style.display = "none";
  const inputElem = document.getElementById("add-savoir-input-" + activityId);
  if (inputElem) inputElem.value = "";
}

function submitAddSavoir(activityId) {
  const inputElem = document.getElementById("add-savoir-input-" + activityId);
  if (!inputElem) return;
  const desc = inputElem.value.trim();
  if (!desc) {
    alert("Veuillez saisir une description pour le savoir.");
    return;
  }

  fetch(`/savoirs/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
        description: desc, 
        activity_id: activityId  // Assurez-vous de passer l'activity_id
    })
  })
  .then(resp => {
      if (!resp.ok) {
          throw new Error(`Erreur lors de la soumission : ${resp.statusText}`);
      }
      return resp.json();
  })
  .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        updateSavoirs(activityId);
      }
  })
  .catch(err => {
      console.error("Erreur ajout savoirs :", err);
  });
}




/**************************************
 * RAFFRAICHIR LA LISTE PARTIELLEMENT
 **************************************/
function updateSavoirsList(activityId) {
  showSpinner();
  fetch(`/savoirs/${activityId}/render`)
    .then(resp => {
      if (!resp.ok) throw new Error("Erreur lors du rafraîchissement des savoirs");
      return resp.text();
    })
    .then(html => {
      hideSpinner();
      const container = document.getElementById("savoirs-list-" + activityId);
      if (container) {
        container.innerHTML = html;
      }
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur updateSavoirsList:", err);
      alert("Erreur updateSavoirsList : " + err.message);
    });
}


function updateSavoirs(activityId) {
  fetch(`/savoirs/${activityId}/render`)
    .then(response => {
      if (!response.ok) throw new Error("Erreur lors du rafraîchissement des savoirs.");
      return response.text();
    })
    .then(html => {
      const container = document.querySelector(`#savoirs-container-${activityId}`);
      container.innerHTML = html;
    })
    .catch(err => {
      console.error("Erreur updateSavoirs :", err);
      alert(err.message);
    });
}

/* Édition */

function editSavoir(savoirId, activityId) {
  const descElem = document.getElementById(`savoir-desc-${savoirId}`);
  const editInput = document.getElementById(`edit-savoir-input-${savoirId}`);
  const editBtn = document.getElementById(`submit-edit-savoir-${savoirId}`);

  descElem.style.display = "none";
  editInput.style.display = "inline-block";
  editBtn.style.display = "inline-block";
  editInput.value = descElem.innerText.trim();
}

function submitEditSavoir(activityId, savoirId) {
  const inputElem = document.getElementById("edit-savoir-input-" + savoirId);
  if (!inputElem) return;
  const newDesc = inputElem.value.trim();
  if (!newDesc) {
    alert("Veuillez saisir la description du Savoir.");
    return;
  }

  fetch(`/savoirs/${activityId}/${savoirId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description: newDesc })
  })
    .then(resp => resp.json())
    .then(data => {
      if (data.error) {
        alert("Erreur édition Savoir : " + data.error);
      } else {
        updateSavoirs(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur modification savoir:", err);
      alert(err.message);
    });
}


function showEditSavoirForm(btnElem) {
  const savoirStr = btnElem.getAttribute("data-savoir");
  let savoirObj;
  try {
    savoirObj = JSON.parse(savoirStr);
  } catch (e) {
    console.error("Erreur parse JSON:", e, savoirStr);
    alert("Impossible de lire le savoir.");
    return;
  }
  
  const formDiv = document.getElementById("edit-savoir-form-" + savoirObj.id);
  const inputEl = document.getElementById("edit-savoir-input-" + savoirObj.id);

  if (formDiv && inputEl) {
    formDiv.style.display = "block";
    inputEl.value = savoirObj.description || "";
  }
}

function hideEditSavoirForm(savoirId) {
  const formDiv = document.getElementById("edit-savoir-form-" + savoirId);
  if (formDiv) {
    formDiv.style.display = "none";
  }
}


function deleteSavoir(activityId, savoirId) {
  if (!confirm("Supprimer ce savoir ?")) return;

  fetch(`/savoirs/${activityId}/${savoirId}`, { method: "DELETE" })
    .then(resp => resp.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        updateSavoirs(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur suppression savoir :", err);
    });
}

