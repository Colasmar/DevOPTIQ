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
    alert("Identifiant de l'activité introuvable.");
    return;
  }

  const userInputElem = document.getElementById('translateSoftskillsInput');
  const userInput = userInputElem.value.trim();
  if (!userInput) {
    alert("Veuillez saisir du texte.");
    return;
  }

  showSpinner();

  // Corrigé : Appel AJAX préalable pour récupérer les informations complètes de l'activité
  fetch(`/activities/${activityId}/details`)
    .then(response => response.json())
    .then(activity_data => {
      // Maintenant que tu as les détails complets, tu peux appeler ton API
      $.ajax({
        url: '/translate_softskills/translate',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
          user_input: userInput,
          activity_data: activity_data
        }),
        success: function(response) {
          hideSpinner();
          if (!response.proposals) {
            alert("Réponse inattendue : pas de 'proposals'");
            return;
          }

          let addPromises = [];
          response.proposals.forEach(function(item) {
            let p = $.ajax({
              url: '/softskills/add',
              method: 'POST',
              contentType: 'application/json',
              data: JSON.stringify({
                activity_id: activityId,
                habilete: item.habilete,
                niveau: item.niveau,
                justification: item.justification
              }),
              success: function(added) {
                if (added.error) {
                  console.error("Erreur ajout HSC:", added.error);
                } else {
                  addSoftskillItemToDOM(
                    activityId,
                    added.habilete,
                    added.niveau,
                    added.id,
                    added.justification
                  );
                }
              },
              error: function(err) {
                console.error("Erreur /softskills/add:", err);
              }
            });
            addPromises.push(p);
          });

          $.when.apply($, addPromises).then(function() {
            userInputElem.value = "";
            closeTranslateSoftskillsModal();
          });
        },
        error: function() {
          hideSpinner();
          alert("Erreur lors de la traduction des softskills.");
        }
      });
    })
    .catch(error => {
      hideSpinner();
      alert("Erreur récupération détails de l'activité : " + error);
    });
}
