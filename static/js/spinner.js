/*******************************************************
 * FICHIER : Code/static/js/spinner.js
 * Gère l'affichage du voile gris + icône de chargement
 ******************************************************/

/**
 * Affiche le div overlay (voile gris + icône).
 */
function showSpinner() {
  const overlay = document.getElementById("spinnerOverlay");
  if (overlay) {
    overlay.style.display = "block";
  }
}

/**
 * Masque le div overlay (voile gris + icône).
 */
function hideSpinner() {
  const overlay = document.getElementById("spinnerOverlay");
  if (overlay) {
    overlay.style.display = "none";
  }
}
