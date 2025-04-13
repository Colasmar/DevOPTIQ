// Code/static/js/main.js
// Fonctions globales et gestion du bouton cartographie

if (!window.OPTIQ_MAIN_LOADED) {
  window.OPTIQ_MAIN_LOADED = true;

  // Variables globales éventuelles
  window.currentActivityId = null;
  window.currentType = "";

  /**
   * toggleDetails(...) :
   * Bascule l'affichage (repli/dépli) d'un bloc details pour l'activité.
   * On sélectionne details-{{ activity.id }} et on modifie son style.
   */
  window.toggleDetails = function (detailsId, headerElem) {
    const detailsElem = document.getElementById(detailsId);
    const iconElem = headerElem.querySelector('.toggle-icon');
    const currentDisplay = window.getComputedStyle(detailsElem).display;

    if (currentDisplay === "none") {
      detailsElem.style.display = "block";
      iconElem.textContent = "▼";
    } else {
      detailsElem.style.display = "none";
      iconElem.textContent = "▶";
    }
  };

  /**
   * getActivityData(...) :
   * Retourne le texte brut (ex. description, tâches, etc.) depuis le bloc details-<activityId>.
   * Utile pour formuler un prompt IA.
   */
  window.getActivityData = function (activityId) {
    const detailsElem = document.getElementById(`details-${activityId}`);
    return detailsElem ? detailsElem.innerText : "";
  };
}

/**
 * À l’événement DOMContentLoaded, on associe par exemple
 * le bouton #update-cartography-button pour actualiser la carto.
 */
document.addEventListener("DOMContentLoaded", function () {
  const cartoButton = document.getElementById("update-cartography-button");
  if (cartoButton) {
    cartoButton.addEventListener("click", function () {
      showSpinner();

      fetch("/activities/update-cartography")
        .then(r => r.json())
        .then(data => {
          hideSpinner();
          if (data.error) {
            alert("Erreur : " + data.error);
          } else {
            alert(data.message + "\n\nRésumé :\n" + data.summary);
            location.reload();
          }
        })
        .catch(err => {
          hideSpinner();
          console.error("Erreur update-cartography:", err);
          alert("Erreur de mise à jour de la cartographie.");
        });
    });
  }
});
