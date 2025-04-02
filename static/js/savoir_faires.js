// Code/static/js/savoir_faires.js

function showAddSavoirFaireForm(activityId) {
    document.getElementById("add-sf-form-" + activityId).style.display = "block";
  }
  
  function hideAddSavoirFaireForm(activityId) {
    document.getElementById("add-sf-form-" + activityId).style.display = "none";
    const inputElem = document.getElementById("add-sf-input-" + activityId);
    if (inputElem) inputElem.value = "";
  }
  
  function submitAddSavoirFaire(activityId) {
    const inputElem = document.getElementById("add-sf-input-" + activityId);
    if (!inputElem) return;
    const desc = inputElem.value.trim();
    if (!desc) {
      alert("Veuillez saisir un texte pour le Savoir-Faire.");
      return;
    }
  
    fetch(`/savoir_faires/${activityId}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: desc })
    })
      .then(resp => resp.json())
      .then(data => {
        if (data.error) {
          console.error("Erreur ajout Savoir-Faire:", data.error);
          alert("Erreur : " + data.error);
        } else {
          updateSavoirFaires(activityId);
        }
      })
      .catch(err => {
        console.error("Erreur ajout Savoir-Faire:", err);
        alert(err.message);
      });
  }
  
  function updateSavoirFaires(activityId) {
    fetch(`/savoir_faires/${activityId}/render`)
      .then(response => {
        if (!response.ok) throw new Error("Erreur lors du rafraîchissement Savoir-Faire");
        return response.text();
      })
      .then(html => {
        const parentDiv = document.querySelector(`#savoir-faires-container-${activityId}`).parentNode;
        parentDiv.innerHTML = html;
      })
      .catch(err => {
        console.error("updateSavoirFaires error:", err);
        alert(err.message);
      });
  }
  
  /* Edition */
  
  function showEditSavoirFaireForm(btnElem) {
    const sfStr = btnElem.getAttribute("data-sf");
    let sfObj;
    try {
      sfObj = JSON.parse(sfStr);
    } catch (e) {
      console.error("Erreur parse JSON:", e, sfStr);
      alert("Impossible de lire ce Savoir-Faire.");
      return;
    }
    const formDiv = document.getElementById("edit-sf-form-" + sfObj.id);
    const inputEl = document.getElementById("edit-sf-input-" + sfObj.id);
  
    if (formDiv && inputEl) {
      formDiv.style.display = "block";
      inputEl.value = sfObj.description || "";
    }
  }
  
  function hideEditSavoirFaireForm(sfId) {
    const formDiv = document.getElementById("edit-sf-form-" + sfId);
    if (formDiv) {
      formDiv.style.display = "none";
    }
  }
  
  function submitEditSavoirFaire(activityId, sfId) {
    const inputEl = document.getElementById("edit-sf-input-" + sfId);
    if (!inputEl) return;
    const newDesc = inputEl.value.trim();
    if (!newDesc) {
      alert("Veuillez saisir la description du Savoir-Faire.");
      return;
    }
  
    fetch(`/savoir_faires/${activityId}/${sfId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: newDesc })
    })
      .then(resp => resp.json())
      .then(data => {
        if (data.error) {
          alert("Erreur édition Savoir-Faire : " + data.error);
        } else {
          updateSavoirFaires(activityId);
        }
      })
      .catch(err => {
        console.error("Erreur edit Savoir-Faire:", err);
        alert(err.message);
      });
  }
  
  function deleteSavoirFaire(activityId, sfId) {
    if (!confirm("Supprimer ce Savoir-Faire ?")) return;
    fetch(`/savoir_faires/${activityId}/${sfId}`, { method: "DELETE" })
      .then(resp => resp.json())
      .then(data => {
        if (data.error) {
          alert("Erreur suppression Savoir-Faire : " + data.error);
        } else {
          updateSavoirFaires(activityId);
        }
      })
      .catch(err => {
        console.error("Erreur suppression Savoir-Faire:", err);
        alert(err.message);
      });
  }
  