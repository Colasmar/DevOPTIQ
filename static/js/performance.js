/*******************************************************
 * Gère l'ajout, l'édition et la suppression d'une Performance
 * associée à un Link (link_id).
 ******************************************************/

/**
 * Ouvre le formulaire d'ajout d'une Performance.
 */
function showAddPerfForm(linkId) {
  const formId = `perf-add-form-${linkId}`;
  const formDiv = document.getElementById(formId);
  if (formDiv) {
    formDiv.style.display = "block";
  }
}
function hideAddPerfForm(linkId) {
  const formId = `perf-add-form-${linkId}`;
  const formDiv = document.getElementById(formId);
  if (formDiv) formDiv.style.display = "none";
}

/**
 * Valide le formulaire d'ajout et appelle /performance/add (POST).
 */
function submitAddPerf(linkId) {
  const inputElem = document.getElementById(`perf-add-input-${linkId}`);
  if (!inputElem) {
    alert("Champ Performance introuvable.");
    return;
  }
  const name = inputElem.value.trim();
  if (!name) {
    alert("Veuillez saisir un nom de Performance.");
    return;
  }
  // ICI vous pouvez gérer la description si besoin
  const description = "";

  fetch("/performance/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ link_id: linkId, name: name, description: description })
  })
  .then(resp => resp.json())
  .then(data => {
    if (data.error) {
      alert("Erreur création performance: " + data.error);
    } else {
      hideAddPerfForm(linkId);
      refreshPerformanceDOM(linkId);
    }
  })
  .catch(err => {
    console.error("Erreur POST /performance/add:", err);
    alert("Impossible de créer la performance (voir console).");
  });
}

/**
 * Recharge le fragment HTML /performance/render/<linkId>
 * et remplace le contenu de #perf-cell-<linkId>.
 */
function refreshPerformanceDOM(linkId) {
  fetch(`/performance/render/${linkId}`)
    .then(r => {
      if (!r.ok) throw new Error("Performance partial not found");
      return r.text();
    })
    .then(html => {
      const container = document.getElementById(`perf-cell-${linkId}`);
      if (container) container.innerHTML = html;
    })
    .catch(err => {
      console.error(`Erreur chargement /performance/render/${linkId}:`, err);
    });
}

/**
 * Ouvre le formulaire d'édition d'une Performance existante.
 */
function showEditPerfForm(perfId, perfName) {
  const formDiv = document.getElementById(`perf-edit-form-${perfId}`);
  if (formDiv) {
    formDiv.style.display = "block";
    // On pré-remplit
    const inputElem = document.getElementById(`perf-edit-input-${perfId}`);
    if (inputElem) {
      inputElem.value = perfName || "";
    }
  }
}
function hideEditPerfForm(perfId) {
  const formDiv = document.getElementById(`perf-edit-form-${perfId}`);
  if (formDiv) formDiv.style.display = "none";
}

/**
 * Valide l'édition et appelle PUT /performance/<perfId>.
 */
function submitEditPerf(perfId) {
  const inputElem = document.getElementById(`perf-edit-input-${perfId}`);
  if (!inputElem) return;
  const newName = inputElem.value.trim();
  if (!newName) {
    alert("Veuillez saisir un nom de Performance.");
    return;
  }
  // Pas de description pour l'instant
  const newDesc = "";

  // On a besoin du linkId pour rafraîchir ensuite
  const displayDiv = document.getElementById(`perf-display-${perfId}`);
  if (!displayDiv) {
    alert("Impossible de localiser la performance dans le DOM.");
    return;
  }
  const perfContainer = displayDiv.closest(".perf-container");
  const linkId = perfContainer ? perfContainer.getAttribute("data-linkid") : null;

  fetch(`/performance/${perfId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: newName, description: newDesc })
  })
  .then(resp => resp.json())
  .then(data => {
    if (data.error) {
      alert("Erreur mise à jour performance: " + data.error);
    } else {
      hideEditPerfForm(perfId);
      if (linkId) refreshPerformanceDOM(linkId);
    }
  })
  .catch(err => {
    console.error("Erreur PUT /performance/<id>:", err);
    alert("Impossible de modifier la performance (voir console).");
  });
}

/**
 * Supprime la Performance (DELETE /performance/<perfId>),
 * puis rafraîchit la zone correspondante.
 */
function deletePerformance(perfId) {
  if (!confirm("Confirmez-vous la suppression de cette performance ?")) return;

  // Récup linkId
  const displayDiv = document.getElementById(`perf-display-${perfId}`);
  if (!displayDiv) {
    alert("Impossible de localiser la performance dans le DOM.");
    return;
  }
  const perfContainer = displayDiv.closest(".perf-container");
  const linkId = perfContainer ? perfContainer.getAttribute("data-linkid") : null;

  fetch(`/performance/${perfId}`, { method: "DELETE" })
    .then(resp => resp.json())
    .then(data => {
      if (data.error) {
        alert("Erreur suppression performance: " + data.error);
      } else {
        if (linkId) refreshPerformanceDOM(linkId);
      }
    })
    .catch(err => {
      console.error("Erreur DELETE /performance/<id>:", err);
      alert("Impossible de supprimer la performance (voir console).");
    });
}
