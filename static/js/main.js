// main.js - Fonctions globales

// Fonction pour ouvrir/fermer les activités
function toggleDetails(detailsId, headerElem) {
    console.log("toggleDetails called with detailsId =", detailsId);
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
  }
  console.log("toggleDetails loaded in main.js");
  
  // Fonctions globales pour récupérer les informations d'une activité
  function getActivityDetails(activityId) {
      const detailsElem = document.getElementById('details-' + activityId);
      return detailsElem ? detailsElem.innerText : "";
  }
  
  function getCompetenciesData(activityId) {
      const compElem = document.getElementById('competencies-' + activityId);
      return compElem ? compElem.innerText : "";
  }
  