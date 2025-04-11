// Code/static/js/main.js
// Fonctions globales + cartographie

if (!window.OPTIQ_MAIN_LOADED) {
  window.OPTIQ_MAIN_LOADED = true;

  // Variables globales éventuelles
  window.currentActivityId = null;
  window.currentType = "";

  // Bascule repli/dépli
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

  // Récupère du texte brut (ex. description)
  window.getActivityData = function (activityId) {
    const detailsElem = document.getElementById(`details-${activityId}`);
    return detailsElem ? detailsElem.innerText : "";
  };
}

document.addEventListener("DOMContentLoaded", function () {
  const cartoButton = document.getElementById("update-cartography-button");
  if (cartoButton) {
    cartoButton.addEventListener("click", function () {
      // Cf. spinner.js
      showSpinner();

      fetch("/activities/update-cartography")
        .then((r) => r.json())
        .then((data) => {
          hideSpinner();
          if (data.error) {
            alert("Erreur : " + data.error);
          } else {
            alert(data.message + "\n\nRésumé :\n" + data.summary);
            location.reload();
          }
        })
        .catch((err) => {
          hideSpinner();
          console.error("Erreur update-cartography:", err);
          alert("Erreur de mise à jour de la cartographie.");
        });
    });
  }
});
