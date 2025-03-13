// translate_softskills.js - Gestion de la traduction des softskills en HSC

function openTranslateSoftskillsModal(activityId) {
  window.translateSoftskillsActivityId = activityId;
  document.getElementById('translateSoftskillsModal').style.display = 'block';
}

function closeTranslateSoftskillsModal() {
  document.getElementById('translateSoftskillsModal').style.display = 'none';
  window.translateSoftskillsActivityId = null;
}

// Soumet le texte entré pour traduction et ajoute les HSC traduites en base
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

  // On affiche le spinner
  showSpinner();

  // 1) Appel /softskills/translate => { "proposals": [ { habilete, niveau, justification }, ... ] }
  $.ajax({
    url: '/softskills/translate',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ user_input: userInput }),
    success: function(response) {
      hideSpinner();

      if (!response.proposals) {
        alert("Réponse inattendue : pas de 'proposals' ?");
        return;
      }

      let addPromises = [];
      // 2) Pour chaque proposition => /softskills/add
      response.proposals.forEach(function(item) {
        let p = $.ajax({
          url: '/softskills/add',
          method: 'POST',
          contentType: 'application/json',
          data: JSON.stringify({
            activity_id: activityId,
            habilete: item.habilete,
            niveau: item.niveau,
            justification: item.justification // <-- on envoie la justification
          }),
          success: function(added) {
            if (added.error) {
              console.error("Erreur ajout HSC:", added.error);
            } else {
              // 3) On insère la HSC dans le DOM
              // addSoftskillItemToDOM(activityId, hscName, hscLevel, dbId, justification)
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

      // Quand toutes les requêtes sont terminées
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
}

// Événement pour un bouton .translate-softskills-btn (facultatif)
$(document).on('click', '.translate-softskills-btn', function() {
  const activityId = $(this).data('activity-id');
  openTranslateSoftskillsModal(activityId);
});
