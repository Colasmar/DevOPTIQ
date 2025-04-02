// Code/static/js/translate_softskills.js

function openTranslateSoftskillsModal(activityId) {
  window.translateSoftskillsActivityId = activityId;
  document.getElementById('translateSoftskillsModal').style.display = 'block';
}

function closeTranslateSoftskillsModal() {
  document.getElementById('translateSoftskillsModal').style.display = 'none';
  window.translateSoftskillsActivityId = null;
}

function submitSoftskillsTranslation() {
  const activityId = window.translateSoftskillsActivityId;
  if (!activityId) {
    alert("Activité introuvable pour la traduction.");
    return;
  }
  const userInputElem = document.getElementById('translateSoftskillsInput');
  const userInput = (userInputElem.value || "").trim();
  if (!userInput) {
    alert("Veuillez saisir du texte (soft skills).");
    return;
  }

  // On récupère le contexte de l'activité (pour le prompt) => /activities/<id>/details
  showSpinner();
  fetch(`/activities/${activityId}/details`)
    .then(r => {
      if (!r.ok) {
        hideSpinner();
        throw new Error("Erreur /activities details");
      }
      return r.json();
    })
    .then(activityData => {
      // On envoie user_input + activityData => /translate_softskills/translate
      const payload = {
        user_input,
        activity_data: {
          name: activityData.name,
          tasks: activityData.tasks || [],
          constraints: activityData.constraints || [],
          outgoing: activityData.outgoing || []
        }
      };
      return fetch('/translate_softskills/translate', {
        method: 'POST',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    })
    .then(resp => resp.json())
    .then(data => {
      if (data.error) {
        hideSpinner();
        alert("Erreur traduction HSC : " + data.error);
      } else if (!data.proposals || !Array.isArray(data.proposals)) {
        hideSpinner();
        alert("Réponse inattendue : pas de 'proposals' !");
      } else {
        // data.proposals => un tableau d'objets HSC
        // On appelle /softskills/add pour chacune
        const proposals = data.proposals;
        if (proposals.length === 0) {
          hideSpinner();
          alert("Aucune HSC renvoyée par l'IA.");
          return;
        }
        // Fermeture de la modale
        document.getElementById('translateSoftskillsModal').style.display = 'none';
        let addPromises = [];
        proposals.forEach(item => {
          let p = fetch('/softskills/add', {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              activity_id: activityId,
              habilete: item.habilete || "HSC ?",
              niveau: item.niveau || "2 (Acquisition)",
              justification: item.justification || ""
            })
          })
          .then(r => r.json())
          .then(res => {
            if (res.error) {
              console.error("Erreur /softskills/add:", res.error);
            }
          })
          .catch(err => console.error("Erreur fetch /softskills/add:", err));
          addPromises.push(p);
        });
        return Promise.all(addPromises);
      }
    })
    .then(() => {
      // On fait le partial reload
      hideSpinner();
      updateSoftskillsList(activityId);
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur finale traduction HSC:", err);
      alert("Erreur finale traduction HSC. Voir console.");
    });
}

