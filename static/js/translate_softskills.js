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
    alert("Erreur : activityId introuvable.");
    return;
  }
  // Récupère le texte saisi par l'utilisateur
  const userInputElem = document.getElementById('translateSoftskillsInput');
  const userInput = (userInputElem?.value || "").trim();
  if (!userInput) {
    alert("Veuillez saisir quelque chose dans le champ des soft skills.");
    return;
  }

  showSpinner();

  // (1) Récupère le contexte de l'activité
  fetch(`/activities/${activityId}/details`)
    .then(resp => {
      if (!resp.ok) {
        throw new Error("Erreur lors de la récupération du contexte (details).");
      }
      return resp.json();
    })
    .then(activityData => {
      if (activityData.error) {
        throw new Error(activityData.error);
      }

      // (2) Prépare les données pour la traduction (l'IA)
      const payload = {
        user_input: userInput,        // <--- on envoie la variable userInput en JSON
        activity_data: {
          name: activityData.name,
          tasks: activityData.tasks || [],
          constraints: activityData.constraints || [],
          outgoing: activityData.outgoing || []
        }
      };

      return fetch('/translate_softskills/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    })
    .then(resp => {
      if (!resp.ok) {
        throw new Error("Réponse non OK de /translate_softskills/translate");
      }
      return resp.json();
    })
    .then(data => {
      if (data.error) {
        throw new Error(data.error);
      }
      const proposals = data.proposals;
      if (!proposals || !Array.isArray(proposals) || proposals.length === 0) {
        throw new Error("L'IA n'a renvoyé aucune HSC.");
      }

      // Ferme la modale d'input
      closeTranslateSoftskillsModal();

      // (3) Insère les HSC en base, via /softskills/add
      const addPromises = proposals.map(p => {
        return fetch('/softskills/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            activity_id: activityId,
            habilete: p.habilete || "Habilete ?",
            niveau: p.niveau || "2 (Acquisition)",
            justification: p.justification || ""
          })
        })
        .then(r => r.json())
        .then(res => {
          if (res.error) {
            console.error("Erreur insertion softskill:", res.error);
          }
        })
        .catch(err => {
          console.error("Erreur /softskills/add:", err);
        });
      });

      return Promise.all(addPromises);
    })
    .then(() => {
      // (4) On rafraîchit partiellement la liste HSC
      hideSpinner();
      updateSoftskillsList(activityId);
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur finale traduction HSC:", err);
      alert("Erreur finale traduction HSC : " + err.message);
    });
}
