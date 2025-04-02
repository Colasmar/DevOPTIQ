// Code/static/js/softskills.js

function toggleSoftskillJustification(ssId) {
  const div = document.getElementById("softskill-justif-" + ssId);
  if (!div) return;
  if (div.style.display === "none" || !div.style.display) {
    div.style.display = "block";
  } else {
    div.style.display = "none";
  }
}

/**************************************
 * AJOUT MANUEL
 **************************************/
function showAddSoftskillForm(activityId) {
  document.getElementById("add-softskill-form-" + activityId).style.display = "block";
}

function hideAddSoftskillForm(activityId) {
  document.getElementById("add-softskill-form-" + activityId).style.display = "none";
  // reset
  document.getElementById("new-softskill-name-" + activityId).value = "";
  document.getElementById("new-softskill-level-" + activityId).value = "";
  document.getElementById("new-softskill-justif-" + activityId).value = "";
}

function submitAddSoftskill(activityId) {
  const habilete = document.getElementById("new-softskill-name-" + activityId).value.trim();
  const niveau = document.getElementById("new-softskill-level-" + activityId).value.trim();
  const justification = document.getElementById("new-softskill-justif-" + activityId).value.trim();

  if (!habilete || !niveau) {
    alert("Veuillez renseigner au moins habileté et niveau.");
    return;
  }

  showSpinner();
  fetch("/softskills/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      activity_id: activityId,
      habilete,
      niveau,
      justification
    })
  })
  .then(r => r.json())
  .then(d => {
    hideSpinner();
    if (d.error) {
      alert("Erreur ajout HSC : " + d.error);
    } else {
      updateSoftskillsList(activityId);
      hideAddSoftskillForm(activityId);
    }
  })
  .catch(err => {
    hideSpinner();
    console.error("Erreur ajout HSC:", err);
    alert("Erreur ajout HSC : " + err.message);
  });
}

/**************************************
 * RAFFRAICHIR LA LISTE PARTIELLEMENT
 **************************************/
function updateSoftskillsList(activityId) {
  showSpinner();
  fetch(`/softskills/${activityId}/render`)
    .then(resp => {
      if (!resp.ok) throw new Error("Erreur lors du rafraîchissement des softskills");
      return resp.text();
    })
    .then(html => {
      hideSpinner();
      const container = document.getElementById("softskills-list-" + activityId);
      if (container) {
        container.innerHTML = html;
      }
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur updateSoftskillsList:", err);
      alert("Erreur updateSoftskillsList : " + err.message);
    });
}

/**************************************
 * EDITION
 **************************************/
function editSoftskill(ssId) {
  const formDiv = document.getElementById("edit-softskill-form-" + ssId);
  if (formDiv) {
    formDiv.style.display = "block";
  }
}

function hideEditSoftskillForm(ssId) {
  const formDiv = document.getElementById("edit-softskill-form-" + ssId);
  if (formDiv) {
    formDiv.style.display = "none";
  }
}

function submitEditSoftskillFromDOM(ssId) {
  const itemDiv = document.querySelector(`[data-ss-id='${ssId}']`);
  let activityId = null;
  if (itemDiv) {
    const container = itemDiv.closest(".activity-details");
    if (container && container.id.startsWith("details-")) {
      activityId = container.id.replace("details-", "");
    }
  }

  const nameEl = document.getElementById("edit-softskill-name-" + ssId);
  const levelEl = document.getElementById("edit-softskill-level-" + ssId);
  const justifEl = document.getElementById("edit-softskill-justif-" + ssId);

  if (!nameEl || !levelEl) {
    alert("Champs manquants dans le form d'édition HSC.");
    return;
  }

  const newHabilete = nameEl.value.trim();
  const newNiveau = levelEl.value.trim();
  const newJustif = justifEl ? justifEl.value.trim() : "";

  if (!newHabilete || !newNiveau) {
    alert("Veuillez renseigner habileté et niveau.");
    return;
  }

  showSpinner();
  fetch(`/softskills/${ssId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      habilete: newHabilete,
      niveau: newNiveau,
      justification: newJustif
    })
  })
  .then(r => r.json())
  .then(d => {
    hideSpinner();
    if (d.error) {
      alert("Erreur mise à jour HSC : " + d.error);
    } else {
      if (activityId) {
        updateSoftskillsList(activityId);
      } else {
        location.reload();
      }
    }
  })
  .catch(err => {
    hideSpinner();
    console.error("Erreur maj HSC:", err);
  });
}

/**************************************
 * SUPPRESSION
 **************************************/
function deleteSoftskill(ssId) {
  if (!confirm("Voulez-vous vraiment supprimer cette HSC ?")) return;

  const itemDiv = document.querySelector(`[data-ss-id='${ssId}']`);
  let activityId = null;
  if (itemDiv) {
    const container = itemDiv.closest(".activity-details");
    if (container && container.id.startsWith("details-")) {
      activityId = container.id.replace("details-", "");
    }
  }

  showSpinner();
  fetch(`/softskills/${ssId}`, { method: "DELETE" })
  .then(r => r.json())
  .then(data => {
    hideSpinner();
    if (data.error) {
      alert("Erreur suppression HSC : " + data.error);
    } else {
      if (activityId) {
        updateSoftskillsList(activityId);
      } else {
        location.reload();
      }
    }
  })
  .catch(err => {
    hideSpinner();
    console.error("Erreur suppression HSC:", err);
    alert("Erreur suppression HSC : " + err.message);
  });
}
