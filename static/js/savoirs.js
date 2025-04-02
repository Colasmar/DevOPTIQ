// Code/static/js/savoirs.js

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
      alert("Veuillez saisir un texte pour le Savoir.");
      return;
    }
  
    fetch(`/savoirs/${activityId}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: desc })
    })
      .then(resp => resp.json())
      .then(data => {
        if (data.error) {
          console.error("Erreur ajout savoir:", data.error);
          alert("Erreur ajout savoir : " + data.error);
        } else {
          updateSavoirs(activityId);
        }
      })
      .catch(err => {
        console.error("Erreur ajout savoir:", err);
        alert("Erreur ajout savoir : " + err.message);
      });
  }
  
  function updateSavoirs(activityId) {
    fetch(`/savoirs/${activityId}/render`)
      .then(response => {
        if (!response.ok) throw new Error("Erreur lors du rafraîchissement des Savoirs");
        return response.text();
      })
      .then(html => {
        const parentDiv = document.querySelector(`#savoirs-container-${activityId}`).parentNode;
        parentDiv.innerHTML = html;
      })
      .catch(err => {
        console.error("updateSavoirs error:", err);
        alert(err.message);
      });
  }
  
  /* Edition */
  
  function showEditSavoirForm(btnElem) {
    const svStr = btnElem.getAttribute("data-savoir");
    let svObj;
    try {
      svObj = JSON.parse(svStr);
    } catch (e) {
      console.error("Erreur parse JSON:", e, svStr);
      alert("Impossible de lire ce Savoir.");
      return;
    }
    const formDiv = document.getElementById("edit-savoir-form-" + svObj.id);
    const inputEl = document.getElementById("edit-savoir-input-" + svObj.id);
  
    if (formDiv && inputEl) {
      formDiv.style.display = "block";
      inputEl.value = svObj.description || "";
    }
  }
  
  function hideEditSavoirForm(svId) {
    const formDiv = document.getElementById("edit-savoir-form-" + svId);
    if (formDiv) {
      formDiv.style.display = "none";
    }
  }
  
  function submitEditSavoir(activityId, svId) {
    const inputEl = document.getElementById("edit-savoir-input-" + svId);
    if (!inputEl) return;
    const newDesc = inputEl.value.trim();
    if (!newDesc) {
      alert("Veuillez saisir la description du Savoir.");
      return;
    }
  
    fetch(`/savoirs/${activityId}/${svId}`, {
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
        console.error("Erreur edit Savoir:", err);
        alert(err.message);
      });
  }
  
  function deleteSavoir(activityId, svId) {
    if (!confirm("Supprimer ce Savoir ?")) return;
    fetch(`/savoirs/${activityId}/${svId}`, { method: "DELETE" })
      .then(resp => resp.json())
      .then(data => {
        if (data.error) {
          alert("Erreur suppression Savoir : " + data.error);
        } else {
          updateSavoirs(activityId);
        }
      })
      .catch(err => {
        console.error("Erreur suppression Savoir:", err);
        alert(err.message);
      });
  }
  