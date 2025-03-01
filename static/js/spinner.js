console.log("spinner.js chargé");

function showSpinner() {
  console.log("showSpinner() appelé");
  if (!document.getElementById('spinnerOverlay')) {
    var overlay = document.createElement('div');
    overlay.id = 'spinnerOverlay';
    overlay.className = 'spinner-overlay';

    var spinner = document.createElement('div');
    spinner.className = 'spinner';

    overlay.appendChild(spinner);
    document.body.appendChild(overlay);
    console.log("spinner affiché");
  }
}

function hideSpinner() {
  console.log("hideSpinner() appelé");
  var overlay = document.getElementById('spinnerOverlay');
  if (overlay) {
    document.body.removeChild(overlay);
    console.log("spinner masqué");
  }
}
