// Code/static/js/propose_softskills.js

/**
 * Analyse l'activité, appelle /propose_softskills/propose (non fourni ici)
 * et affiche le résultat dans un modal => checkboxes => /softskills/add
 * 
 * => A titre d'exemple, si ton code actuel s'appelle autrement, 
 *    adapte ou supprime ce fichier. 
 */

function fetchActivityDetailsForPropose(activityId) {
  showSpinner();
  // On appelle /activities/<activityId>/details pour un JSON complet
  fetch(`/activities/${activityId}/details`)
    .then(r => {
      if (!r.ok) {
        hideSpinner();
        throw new Error("Erreur /activities/details");
      }
      return r.json();
    })
    .then(data => {
      hideSpinner();
      proposeSoftskills(data);
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur fetchActivityDetailsForPropose:", err);
      alert("Impossible de récupérer les détails pour Proposer HSC");
    });
}

function proposeSoftskills(activityData) {
  showSpinner();
  fetch('/propose_softskills/propose', {
    method: 'POST',
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(activityData)
  })
  .then(r => {
    if (!r.ok) {
      hideSpinner();
      throw new Error("Erreur /propose_softskills/propose");
    }
    return r.json();
  })
  .then(resp => {
    hideSpinner();
    if (resp.error) {
      alert("Erreur proposition HSC : " + resp.error);
      return;
    }
    if (!resp.proposals || !Array.isArray(resp.proposals)) {
      alert("Réponse inattendue : 'proposals' manquant.");
      return;
    }
    // On ouvre un modal similaire à la traduction ?
    showProposedSoftskills(resp.proposals, activityData.id);
  })
  .catch(err => {
    hideSpinner();
    console.error("Erreur proposeSoftskills:", err);
    alert("Erreur proposeSoftskills");
  });
}



function showProposedSoftskills(hscProposals, activityId) {
  showSpinner();

  const addPromises = hscProposals.map(p => {
    return fetch('/softskills/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        activity_id: activityId,
        habilete: p.habilete,
        niveau: p.niveau,
        justification: p.justification || ""
      })
    }).then(r => r.json()).catch(err => {
      console.error("Erreur lors de l'ajout de la softskill :", err);
    });
  });

  Promise.all(addPromises)
    .then(() => {
      hideSpinner();
      updateSoftskillsList(activityId);
    });
}
