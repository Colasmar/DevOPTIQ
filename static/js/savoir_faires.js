// static/js/savoir_faires.js

// affichage du petit formulaire d'édition inline
function showEditSavoirFairesForm(savoirFairesId) {
  const textEl = document.getElementById(`savoir-faires-desc-${savoirFairesId}`);
  const inputEl = document.getElementById(`edit-savoir-faires-input-${savoirFairesId}`);
  const btnEl   = document.getElementById(`submit-edit-savoir-faires-${savoirFairesId}`);

  if (!textEl || !inputEl || !btnEl) {
    console.warn("showEditSavoirFairesForm: éléments manquants pour", savoirFairesId);
    return;
  }

  // on masque le texte et on montre le champ
  textEl.style.display = "none";
  inputEl.style.display = "inline-block";
  btnEl.style.display   = "inline-block";

  // on pré-remplit
  inputEl.value = textEl.innerText.trim();
  inputEl.focus();
}

// ajout
function submitAddSavoirFaires(activityId) {
  const inputElem = document.getElementById("add-savoir-faires-input-" + activityId);
  if (!inputElem) return;
  const desc = inputElem.value.trim();
  if (!desc) {
    alert("Veuillez saisir une description pour le savoir-faire.");
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
    .then(r => r.json())
    .then(async data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        // on vide le champ
        inputElem.value = "";
        // on rafraîchit tout
        if (typeof refreshActivityItems === "function") {
          await refreshActivityItems(activityId);
        }
      }
    })
    .catch(err => {
      console.error("Erreur ajout savoir-faires :", err);
      alert("Erreur ajout savoir-faires (voir console).");
    });
}

// édition
function submitEditSavoirFaires(activityId, savoirFairesId) {
  const inputEl = document.getElementById("edit-savoir-faires-input-" + savoirFairesId);
  if (!inputEl) return;
  const newDesc = inputEl.value.trim();
  if (!newDesc) {
    alert("Veuillez saisir la description du Savoir-Faire.");
    return;
  }

  fetch(`/savoir_faires/${activityId}/${savoirFairesId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description: newDesc })
  })
    .then(r => r.json())
    .then(async data => {
      if (data.error) {
        alert("Erreur édition Savoir-Faire : " + data.error);
      } else {
        if (typeof refreshActivityItems === "function") {
          await refreshActivityItems(activityId);
        }
      }
    })
    .catch(err => {
      console.error("Erreur edit savoir-faires :", err);
      alert(err.message);
    });
}

// suppression
function deleteSavoirFaires(activityId, savoirFairesId) {
  if (!confirm("Supprimer ce savoir-faires ?")) return;

  fetch(`/savoir_faires/${activityId}/${savoirFairesId}`, { method: "DELETE" })
    .then(r => r.json())
    .then(async data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        if (typeof refreshActivityItems === "function") {
          await refreshActivityItems(activityId);
        }
      }
    })
    .catch(err => {
      console.error("Erreur suppression savoir-faires :", err);
      alert("Erreur suppression savoir-faires (voir console).");
    });
}

// on expose en global (si ton HTML inline les appelle)
window.showEditSavoirFairesForm = showEditSavoirFairesForm;
window.submitAddSavoirFaires = submitAddSavoirFaires;
window.submitEditSavoirFaires = submitEditSavoirFaires;
window.deleteSavoirFaires = deleteSavoirFaires;
