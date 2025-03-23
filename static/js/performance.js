// performance.js

// ---------- AJOUT PERFORMANCE ----------
function showAddPerfForm(dataId) {
  const formDiv = document.getElementById("perf-add-form-" + dataId);
  if (formDiv) formDiv.style.display = "block";
}
function hideAddPerfForm(dataId) {
  const formDiv = document.getElementById("perf-add-form-" + dataId);
  if (formDiv) formDiv.style.display = "none";
}
function submitAddPerf(dataId) {
  const inputElem = document.getElementById("perf-add-input-" + dataId);
  if (!inputElem) return;
  const perfName = inputElem.value.trim();
  if (!perfName) {
    alert("Veuillez saisir un nom de performance.");
    return;
  }
  fetch("/performance/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data_id: parseInt(dataId), name: perfName })
  })
  .then(r => r.json())
  .then(resp => {
    if (resp.error) {
      alert("Erreur : " + resp.error);
    } else {
      window.location.reload(); // simple rechargement
    }
  })
  .catch(err => {
    console.error("Erreur lors de l'ajout de la performance :", err);
    alert("Une erreur est survenue lors de l'ajout.");
  });
}

// ---------- ÉDITION PERFORMANCE ----------
function showEditPerfForm(perfId, currentName) {
  const infoSpan = document.getElementById("perf-info-" + perfId);
  if (infoSpan) infoSpan.style.display = "none";
  const formDiv = document.getElementById("perf-edit-form-" + perfId);
  if (formDiv) {
    formDiv.style.display = "block";
    const input = document.getElementById("perf-edit-input-" + perfId);
    if (input) input.value = currentName;
  }
}
function hideEditPerfForm(perfId) {
  const formDiv = document.getElementById("perf-edit-form-" + perfId);
  if (formDiv) formDiv.style.display = "none";
  const infoSpan = document.getElementById("perf-info-" + perfId);
  if (infoSpan) infoSpan.style.display = "inline";
}
function submitEditPerf(perfId) {
  const input = document.getElementById("perf-edit-input-" + perfId);
  if (!input) return;
  const newName = input.value.trim();
  if (!newName) {
    alert("Veuillez saisir un nom de performance.");
    return;
  }
  fetch(`/performance/${perfId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: newName })
  })
  .then(r => r.json())
  .then(resp => {
    if (resp.error) {
      alert("Erreur : " + resp.error);
    } else {
      const infoSpan = document.getElementById("perf-info-" + perfId);
      if (infoSpan) {
        infoSpan.textContent = resp.name
          + (resp.description ? ` - ${resp.description}` : "");
      }
      hideEditPerfForm(perfId);
    }
  })
  .catch(err => {
    console.error("Erreur lors de la modification :", err);
    alert("Une erreur est survenue lors de la modification.");
  });
}

// ---------- SUPPRESSION PERFORMANCE ----------
function deletePerformance(perfId) {
  if (!confirm("Confirmez-vous la suppression de cette performance ?")) return;
  fetch(`/performance/${perfId}`, { method: "DELETE" })
  .then(r => r.json())
  .then(resp => {
    if (resp.error) {
      alert("Erreur : " + resp.error);
    } else {
      window.location.reload();
    }
  })
  .catch(err => {
    console.error("Erreur lors de la suppression de la performance :", err);
    alert("Une erreur est survenue lors de la suppression.");
  });
}
