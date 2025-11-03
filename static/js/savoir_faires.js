// static/js/savoir_faires.js

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
        await refreshActivityItems(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur ajout savoir-faires :", err);
    });
}

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
        await refreshActivityItems(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur edit savoir-faires :", err);
      alert(err.message);
    });
}

function deleteSavoirFaires(activityId, savoirFairesId) {
  if (!confirm("Supprimer ce savoir-faires ?")) return;

  fetch(`/savoir_faires/${activityId}/${savoirFairesId}`, { method: "DELETE" })
    .then(r => r.json())
    .then(async data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        await refreshActivityItems(activityId);
      }
    })
    .catch(err => {
      console.error("Erreur suppression savoir-faires :", err);
    });
}
