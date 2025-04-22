// Code/static/js/savoirfaires.js

/**
 * Récupère les détails d'une activité (via /activities/<id>/details),
 * puis enchaîne sur la proposition de savoir-faire IA.
 */

/* Ajout direct d'un savoir-faire */
function showAddSavoirFairesForm(activityId) {
  document.getElementById("add-savoir-faires-form-" + activityId).style.display = "block";
}

function hideAddSavoirFairesForm(activityId) {
  document.getElementById("add-savoir-faires-form-" + activityId).style.display = "none";
  const inputElem = document.getElementById("add-savoir-faires-input-" + activityId);
  if (inputElem) inputElem.value = "";
}

function submitAddSavoirFaires(activityId) {
  const inputElem = document.getElementById("add-savoir-faires-input-" + activityId);
  if (!inputElem) return;
  const desc = inputElem.value.trim();
  if (!desc) {
    alert("Veuillez saisir une description pour le savoir-faires.");
    return;
  }

  fetch(`/savoir_faires/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
        description: desc, 
        activity_id: activityId  
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
        updateSavoirFaires(activityId);
      }
  })
  .catch(err => {
      console.error("Erreur ajout savoir-faires :", err);
  });
}



/**************************************
 * RAFFRAICHIR LA LISTE PARTIELLEMENT
 **************************************/
function updateSavoirFairesList(activityId) {
  showSpinner();
  fetch(`/savoir_faires/${activityId}/render`)
    .then(resp => {
      if (!resp.ok) throw new Error("Erreur lors du rafraîchissement des savoir-faires");
      return resp.text();
    })
    .then(html => {
      hideSpinner();
      const container = document.getElementById("savoir-faires-list-" + activityId);
      if (container) {
        container.innerHTML = html;
      }
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur updateSavoirFairesList:", err);
      alert("Erreur updateSavoirFairesList : " + err.message);
    });
}

function updateSavoirFaires(activityId) {
  fetch(`/savoir_faires/${activityId}/render`)
    .then(response => {
      if (!response.ok) throw new Error("Erreur lors du rafraîchissement des savoir-faires.");
      return response.text();
    })
    .then(html => {
      const container = document.querySelector(`#savoir-faires-container-${activityId}`);
      container.innerHTML = html;
    })
    .catch(err => {
      console.error("Erreur updateSavoirFaires :", err);
      alert(err.message);
    });
}

/* Édition */

function editSavoirFaires(savoirFairesId, activityId) {
  const descElem = document.getElementById(`savoir-faires-desc-${savoirFairesId}`);
  const editInput = document.getElementById(`edit-savoir-faires-input-${savoirFairesId}`);
  const editBtn = document.getElementById(`submit-edit-savoir-faires-${savoirFairesId}`);

  descElem.style.display = "none";
  editInput.style.display = "inline-block";
  editBtn.style.display = "inline-block";
  editInput.value = descElem.innerText.trim();
}

function submitEditSavoirFaires(activityId, savoirFairesId) {
  const inputElem = document.getElementById("edit-savoir-faires-input-" + savoirFairesId);
  if (!inputElem) return;
  const newDesc = inputElem.value.trim();
  if (!newDesc) {
    alert("Veuillez saisir la description du savoir-faires.");
    return;
  }

  fetch(`/savoir_faires/${activityId}/${savoirFairesId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description: newDesc })
  })
    .then(resp => resp.json())
    .then(data => {
      if (data.error) {
        alert("Erreur édition savoir-faires : " + data.error);
      } else {
        updateSavoirFaires(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur modification savoir-faires:", err);
      alert(err.message);
    });
}

function showEditSavoirFairesForm(btnElem) {
  const savoirFairesStr = btnElem.getAttribute("data-savoir-faires");
  let savoirFairesObj;
  try {
    savoirFairesObj = JSON.parse(savoirFairesStr);
  } catch (e) {
    console.error("Erreur parse JSON:", e, savoirFairesStr);
    alert("Impossible de lire le savoir-faire.");
    return;
  }
  
  const formDiv = document.getElementById("edit-savoir-faires-form-" + savoirFairesObj.id);
  const inputEl = document.getElementById("edit-savoir-faires-input-" + savoirFairesObj.id);

  if (formDiv && inputEl) {
    formDiv.style.display = "block";
    inputEl.value = savoirFairesObj.description || "";
  }
}

function hideEditSavoirFairesForm(savoirFairesId) {
  const formDiv = document.getElementById("edit-savoir-faires-form-" + savoirFairesId);
  if (formDiv) {
    formDiv.style.display = "none";
  }
}

function deleteSavoirFaires(activityId, savoirFairesId) {
  if (!confirm("Supprimer ce savoir-faires ?")) return;

  fetch(`/savoir_faires/${activityId}/${savoirFairesId}`, { method: "DELETE" })
    .then(resp => resp.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        updateSavoirFaires(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur suppression savoir-faires :", err);
    });
}
