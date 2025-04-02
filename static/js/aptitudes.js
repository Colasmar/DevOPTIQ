// Code/static/js/aptitudes.js

function showAddAptitudeForm(activityId) {
    document.getElementById("add-aptitude-form-" + activityId).style.display = "block";
  }
  
  function hideAddAptitudeForm(activityId) {
    document.getElementById("add-aptitude-form-" + activityId).style.display = "none";
    const inputElem = document.getElementById("add-aptitude-input-" + activityId);
    if (inputElem) inputElem.value = "";
  }
  
  function submitAddAptitude(activityId) {
    const inputElem = document.getElementById("add-aptitude-input-" + activityId);
    if (!inputElem) return;
    const desc = inputElem.value.trim();
    if (!desc) {
      alert("Veuillez saisir une description pour l'aptitude.");
      return;
    }
  
    fetch(`/aptitudes/${activityId}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: desc })
    })
      .then(resp => resp.json())
      .then(data => {
        if (data.error) {
          alert("Erreur : " + data.error);
        } else {
          updateAptitudes(activityId);
        }
      })
      .catch(err => {
        console.error("Erreur ajout aptitude :", err);
      });
  }
  
  function updateAptitudes(activityId) {
    fetch(`/aptitudes/${activityId}/render`)
      .then(response => {
        if (!response.ok) throw new Error("Erreur lors du rafraîchissement des aptitudes.");
        return response.text();
      })
      .then(html => {
        const parentDiv = document.querySelector(`#aptitudes-container-${activityId}`).parentNode;
        parentDiv.innerHTML = html;
      })
      .catch(err => {
        console.error("Erreur updateAptitudes :", err);
        alert(err.message);
      });
  }
  
  /* Édition */
  
  function showEditAptitudeForm(btnElem) {
    const apStr = btnElem.getAttribute("data-aptitude");
    let apObj;
    try {
      apObj = JSON.parse(apStr);
    } catch (e) {
      console.error("Erreur parse JSON:", e, apStr);
      alert("Impossible de lire l'aptitude.");
      return;
    }
    const formDiv = document.getElementById("edit-aptitude-form-" + apObj.id);
    const inputEl = document.getElementById("edit-aptitude-input-" + apObj.id);
  
    if (formDiv && inputEl) {
      formDiv.style.display = "block";
      inputEl.value = apObj.description || "";
    }
  }
  
  function hideEditAptitudeForm(apId) {
    const formDiv = document.getElementById("edit-aptitude-form-" + apId);
    if (formDiv) {
      formDiv.style.display = "none";
    }
  }
  
  function submitEditAptitude(activityId, apId) {
    const inputEl = document.getElementById("edit-aptitude-input-" + apId);
    if (!inputEl) return;
    const newDesc = inputEl.value.trim();
    if (!newDesc) {
      alert("Veuillez saisir la description.");
      return;
    }
  
    fetch(`/aptitudes/${activityId}/${apId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: newDesc })
    })
      .then(resp => resp.json())
      .then(data => {
        if (data.error) {
          alert("Erreur : " + data.error);
        } else {
          updateAptitudes(activityId);
        }
      })
      .catch(err => {
        console.error("Erreur edit aptitude :", err);
      });
  }
  
  function deleteAptitude(activityId, apId) {
    if (!confirm("Supprimer cette aptitude ?")) return;
    fetch(`/aptitudes/${activityId}/${apId}`, { method: "DELETE" })
      .then(resp => resp.json())
      .then(data => {
        if (data.error) {
          alert("Erreur : " + data.error);
        } else {
          updateAptitudes(activityId);
        }
      })
      .catch(err => {
        console.error("Erreur suppression aptitude :", err);
      });
  }
  