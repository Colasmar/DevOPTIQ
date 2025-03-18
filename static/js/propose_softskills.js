// propose_softskills.js - Gère la logique "Proposer HSC" via /propose_softskills/propose
// et insère automatiquement les HSC dans la section "Habiletés socio-cognitives".

function fetchActivityDetailsForPropose(activityId) {
    showSpinner();
    fetch(`/activities/${activityId}/details`)
      .then(response => {
        if (!response.ok) {
          hideSpinner();
          throw new Error("Erreur lors de la récupération des détails de l'activité");
        }
        return response.json();
      })
      .then(activityData => {
        hideSpinner();
        proposeSoftskills(activityData);
      })
      .catch(error => {
        hideSpinner();
        alert("Erreur : " + error.message);
      });
  }
  
  function proposeSoftskills(activityData) {
    showSpinner();
    fetch('/propose_softskills/propose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(activityData)
    })
      .then(response => {
        if (!response.ok) {
          hideSpinner();
          throw new Error("Réponse invalide de /propose_softskills/propose");
        }
        return response.json();
      })
      .then(data => {
        hideSpinner();
        if (data.error) {
          alert("Erreur lors de la proposition HSC : " + data.error);
          return;
        }
  
        // data.proposals => tableau d'objets { habilete, niveau, justification }
        const proposals = data.proposals || [];
        if (proposals.length === 0) {
          alert("Aucune proposition reçue de l'IA.");
          return;
        }
  
        // Pour chaque HSC proposé, on l'ajoute en base via /softskills/add
        let addPromises = [];
        proposals.forEach(hscObj => {
          const habilete = hscObj.habilete || "Inconnue";
          const niveau = hscObj.niveau || "1";
          const justification = hscObj.justification || "";
  
          let p = fetch('/softskills/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              activity_id: activityData.id,
              habilete: habilete,
              niveau: niveau,  // ex: "2 (acquisition)"
              justification: justification
            })
          })
          .then(r => r.json())
          .then(added => {
            if (!added.error) {
              // On insère la HSC dans le DOM (softskills.js)
              addSoftskillItemToDOM(
                activityData.id,
                added.habilete,
                added.niveau,
                added.id,
                added.justification
              );
            } else {
              console.error("Erreur ajout HSC:", added.error);
            }
          })
          .catch(err => {
            console.error("Erreur /softskills/add:", err);
          });
  
          addPromises.push(p);
        });
  
        // Une fois toutes les requêtes terminées, on affiche un message
        Promise.all(addPromises).then(() => {
          alert("Les HSC proposées ont été ajoutées dans la section Habiletés socio-cognitives.");
        });
      })
      .catch(error => {
        hideSpinner();
        alert("Erreur lors de la proposition HSC : " + error.message);
      });
  }
  