// translate_softskills.js - Gestion de la traduction des softskills en HSC

// Ouvre le modal de traduction (défini dans translate_softskills_modal.html)
function openTranslateSoftskillsModal(activityId) {
    window.translateSoftskillsActivityId = activityId;
    document.getElementById('translateSoftskillsModal').style.display = 'block';
  }
  
  // Ferme le modal de traduction
  function closeTranslateSoftskillsModal() {
    document.getElementById('translateSoftskillsModal').style.display = 'none';
    window.translateSoftskillsActivityId = null;
  }
  
  // Soumet le texte entré pour traduction et ajoute les HSC traduites
  function submitSoftskillsTranslation() {
    let activityId = window.translateSoftskillsActivityId;
    if (!activityId) {
      alert("Identifiant de l'activité introuvable.");
      return;
    }
    let userInput = document.getElementById('translateSoftskillsInput').value.trim();
    if (!userInput) {
      alert("Veuillez saisir du texte.");
      return;
    }
    $.ajax({
      url: '/softskills/translate',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ user_input: userInput }),
      success: function(response) {
        response.forEach(function(item) {
          addSoftskillItemToDOM(activityId, item.habilete, item.niveau);
        });
        closeTranslateSoftskillsModal();
      },
      error: function() {
        alert("Erreur lors de la traduction des softskills.");
      }
    });
  }
  
  // Événement pour le bouton "Traduire softskills"
  $(document).on('click', '.translate-softskills-btn', function() {
    const activityId = $(this).data('activity-id');
    openTranslateSoftskillsModal(activityId);
  });
  