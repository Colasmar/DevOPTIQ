// static/js/savoir_faires.js

/************* ADD *************/
function showAddSavoirFairesForm(activityId) {
  const zone = document.getElementById("add-savoir-faires-form-" + activityId);
  if (zone) zone.style.display = "block";
}

function hideAddSavoirFairesForm(activityId) {
  const zone = document.getElementById("add-savoir-faires-form-" + activityId);
  if (zone) zone.style.display = "none";
  const input = document.getElementById("add-savoir-faires-input-" + activityId);
  if (input) input.value = "";
}

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
    body: JSON.stringify({ description: desc, activity_id: activityId })
  })
    .then(async r => {
      if (!r.ok) throw new Error(`HTTP ${r.status} sur /savoir_faires/add`);
      return r.json();
    })
    .then(async data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        inputElem.value = "";
        if (typeof refreshActivityItems === "function") {
          await refreshActivityItems(activityId);
        }
      }
    })
    .catch(err => {
      console.error("Erreur ajout savoir-faire :", err);
      alert(err.message);
    });
}

/************* EDIT INLINE *************/
function showEditSavoirFairesForm(savoirFairesId) {
  const textEl = document.getElementById(`savoir-faires-desc-${savoirFairesId}`);
  const inputEl = document.getElementById(`edit-savoir-faires-input-${savoirFairesId}`);
  const btnEl   = document.getElementById(`submit-edit-savoir-faires-${savoirFairesId}`);

  if (!textEl || !inputEl || !btnEl) {
    console.warn("showEditSavoirFairesForm: éléments manquants pour", savoirFairesId);
    return;
  }
  textEl.style.display = "none";
  inputEl.style.display = "inline-block";
  btnEl.style.display   = "inline-block";
  inputEl.value = (textEl.innerText || "").trim();
  inputEl.focus();
}

function hideEditSavoirFairesForm(savoirFairesId) {
  const textEl = document.getElementById(`savoir-faires-desc-${savoirFairesId}`);
  const inputEl = document.getElementById(`edit-savoir-faires-input-${savoirFairesId}`);
  const btnEl   = document.getElementById(`submit-edit-savoir-faires-${savoirFairesId}`);
  if (!textEl || !inputEl || !btnEl) return;
  textEl.style.display = "inline";
  inputEl.style.display = "none";
  btnEl.style.display   = "none";
}

function submitEditSavoirFaires(activityId, savoirFairesId) {
  const inputEl = document.getElementById("edit-savoir-faires-input-" + savoirFairesId);
  if (!inputEl) return;

  const newDesc = inputEl.value.trim();
  if (!newDesc) {
    alert("Veuillez saisir la description du savoir-faire.");
    return;
  }

  fetch(`/savoir_faires/${activityId}/${savoirFairesId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description: newDesc })
  })
    .then(async r => {
      if (!r.ok) throw new Error(`HTTP ${r.status} sur /savoir_faires/${activityId}/${savoirFairesId}`);
      return r.json();
    })
    .then(async data => {
      if (data.error) {
        alert("Erreur édition savoir-faire : " + data.error);
      } else {
        if (typeof refreshActivityItems === "function") {
          await refreshActivityItems(activityId);
        }
      }
    })
    .catch(err => {
      console.error("Erreur edit savoir-faire :", err);
      alert(err.message);
    });
}

/************* DELETE *************/
function deleteSavoirFaires(activityId, savoirFairesId) {
  if (!confirm("Supprimer ce savoir-faire ?")) return;

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
      console.error("Erreur suppression savoir-faire :", err);
      alert("Erreur suppression savoir-faire (voir console).");
    });
}

// Expose global
window.showAddSavoirFairesForm  = showAddSavoirFairesForm;
window.hideAddSavoirFairesForm  = hideAddSavoirFairesForm;
window.submitAddSavoirFaires    = submitAddSavoirFaires;
window.showEditSavoirFairesForm = showEditSavoirFairesForm;
window.hideEditSavoirFairesForm = hideEditSavoirFairesForm;
window.submitEditSavoirFaires   = submitEditSavoirFaires;
window.deleteSavoirFaires       = deleteSavoirFaires;
