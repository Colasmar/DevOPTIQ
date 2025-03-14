// Montre le formulaire d'ajout
function showAddConstraintForm(activityId) {
    document.getElementById("add-constraint-form-" + activityId).style.display = "block";
  }
  
  // Cache le formulaire d'ajout
  function hideAddConstraintForm(activityId) {
    document.getElementById("add-constraint-form-" + activityId).style.display = "none";
  }
  
  // Soumission de l'ajout
  function submitAddConstraint(activityId) {
    const inputElem = document.getElementById("add-constraint-input-" + activityId);
    if (!inputElem) return;
    const desc = inputElem.value.trim();
    if (!desc) {
      alert("Veuillez saisir une description de contrainte.");
      return;
    }
  
    fetch(`/constraints/${activityId}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: desc })
    })
    .then(resp => resp.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        const container = document.getElementById("constraints-container-" + activityId);
        if (!container) return;
  
        // Retirer "Aucune contrainte enregistrée." si présent
        const noConstraintP = container.querySelector("p");
        if (noConstraintP) container.removeChild(noConstraintP);
  
        // Ajouter la nouvelle contrainte dans la liste <ul>
        let ul = container.querySelector("ul");
        if (!ul) {
          ul = document.createElement("ul");
          container.appendChild(ul);
        }
  
        const li = document.createElement("li");
        li.id = "constraint-" + data.id;
        li.innerHTML = `
          <span class="constraint-text">${data.description}</span>
          <button onclick="showEditConstraintForm('${activityId}', '${data.id}', '${data.description}')">
            <i class="fa-solid fa-pencil"></i>
          </button>
          <button onclick="deleteConstraint('${activityId}', '${data.id}')">
            <i class="fa-solid fa-trash"></i>
          </button>
          <div id="edit-constraint-form-${data.id}" style="display:none; margin-top:5px;">
            <input type="text" id="edit-constraint-input-${data.id}" />
            <button onclick="submitEditConstraint('${activityId}','${data.id}')">Enregistrer</button>
            <button onclick="hideEditConstraintForm('${data.id}')">Annuler</button>
          </div>
        `;
        ul.appendChild(li);
  
        hideAddConstraintForm(activityId);
        inputElem.value = "";
      }
    })
    .catch(err => {
      console.error("Erreur lors de l'ajout de la contrainte :", err);
    });
  }
  
  // Édition
  function showEditConstraintForm(activityId, constraintId, currentDesc) {
    document.getElementById("edit-constraint-form-" + constraintId).style.display = "block";
    document.getElementById("edit-constraint-input-" + constraintId).value = currentDesc;
  }
  function hideEditConstraintForm(constraintId) {
    document.getElementById("edit-constraint-form-" + constraintId).style.display = "none";
  }
  function submitEditConstraint(activityId, constraintId) {
    const inputElem = document.getElementById("edit-constraint-input-" + constraintId);
    if (!inputElem) return;
    const newDesc = inputElem.value.trim();
    if (!newDesc) {
      alert("Veuillez saisir une description.");
      return;
    }
  
    fetch(`/constraints/${activityId}/${constraintId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description: newDesc })
    })
    .then(resp => resp.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        // Mettre à jour la description
        const li = document.getElementById("constraint-" + data.id);
        if (!li) return;
        const descSpan = li.querySelector(".constraint-text");
        if (descSpan) descSpan.textContent = data.description;
        hideEditConstraintForm(data.id);
      }
    })
    .catch(err => {
      console.error("Erreur lors de la modification de la contrainte :", err);
    });
  }
  
  // Suppression
  function deleteConstraint(activityId, constraintId) {
    if (!confirm("Confirmez-vous la suppression de cette contrainte ?")) return;
    fetch(`/constraints/${activityId}/${constraintId}`, { method: "DELETE" })
    .then(resp => resp.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        // Retirer l'élément du DOM
        const li = document.getElementById("constraint-" + constraintId);
        if (li) {
          li.parentNode.removeChild(li);
        }
      }
    })
    .catch(err => {
      console.error("Erreur lors de la suppression de la contrainte :", err);
    });
  }
  