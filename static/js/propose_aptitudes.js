// static/js/propose_aptitudes.js

function fetchActivityDetailsForAptitudes(activityId) {
  showSpinner();
  fetch(`/activities/${activityId}/details`)
    .then(response => {
      if (!response.ok) throw new Error("Erreur lors de la récupération des détails de l'activité");
      return response.json();
    })
    .then(activityData => {
      hideSpinner();
      proposeAptitudes(activityData);
    })
    .catch(error => {
      hideSpinner();
      console.error("Erreur fetchActivityDetailsForAptitudes:", error);
      alert("Impossible de récupérer les détails de l'activité pour Proposer Aptitude");
    });
}

function proposeAptitudes(activityData) {
  showSpinner();
  fetch("/propose_aptitudes/propose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(activityData)
  })
    .then(async response => {
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Réponse invalide de /propose_aptitudes/propose: ${text}`);
      }
      return response.json();
    })
    .then(data => {
      hideSpinner();
      if (data.error) {
        console.error("Erreur IA /propose_aptitudes/propose:", data.error);
        alert("Erreur proposition Aptitudes : " + data.error);
        return;
      }
      const lines = data.proposals;
      if (!lines || !Array.isArray(lines)) {
        alert("Aucune proposition retournée.");
        return;
      }
      showProposedAptitudes(lines, activityData.id);
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur lors de la proposition d'aptitudes:", err);
      alert("Impossible d'obtenir des propositions d'aptitudes (voir console).");
    });
}

// showProposedAptitudes(modal) — tu conserves ta version existante
// qui sauvegarde via /aptitudes/add puis updateAptitudes(activityId)
