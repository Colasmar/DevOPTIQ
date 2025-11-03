// static/js/savoirs.js

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

  if (typeof showSpinner === "function") showSpinner();
  fetch(`/savoirs/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      description: desc,
      activity_id: activityId
    })
  })
    .then(r => r.json())
    .then(async data => {
      if (typeof hideAddSavoirForm === "function") hideAddSavoirForm(activityId);
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        // ✅ on rafraîchit TOUT
        await refreshActivityItems(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur ajout savoir :", err);
    })
    .finally(() => {
      if (typeof hideSpinner === "function") hideSpinner();
    });
}

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
    .then(r => r.json())
    .then(async data => {
      if (data.error) {
        alert("Erreur édition Savoir : " + data.error);
      } else {
        await refreshActivityItems(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur modification savoir:", err);
      alert(err.message);
    });
}

function deleteSavoir(activityId, savoirId) {
  if (!confirm("Supprimer ce savoir ?")) return;

  fetch(`/savoirs/${activityId}/${savoirId}`, { method: "DELETE" })
    .then(r => r.json())
    .then(async data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        await refreshActivityItems(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur suppression savoir :", err);
    });
}
