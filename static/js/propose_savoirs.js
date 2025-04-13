// Code/static/js/propose_savoirs.js
// Gère la proposition IA pour les Savoirs (côté client)

window.proposeSavoirs = function(activityId) {
  // Affiche le spinner
  showSpinner();

  window.currentActivityIdSavoirs = activityId;

  const text = window.getActivityData(activityId);

  fetch("/propose_savoirs/propose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      activity_data: {
        name: "",
        description: text,
        tasks: [],
        tools: []
      }
    })
  })
  .then(resp => resp.json())
  .then(data => {
    hideSpinner();

    if (data.error) {
      alert("Erreur proposition Savoirs : " + data.error);
      return;
    }

    const proposals = data.proposals || [];
    const ul = document.getElementById("proposalsList");
    if (!ul) {
      alert("Erreur : <ul id='proposalsList'> introuvable !");
      return;
    }
    ul.innerHTML = "";

    proposals.forEach(prop => {
      const li = document.createElement("li");
      li.innerHTML = `
        <label style="cursor:pointer;">
          <input type="checkbox" data-proposal="${prop}" />
          ${prop}
        </label>`;
      ul.appendChild(li);
    });

    // On affiche la modale
    const modal = document.getElementById("proposal-modal");
    if (!modal) {
      alert("Erreur : #proposal-modal introuvable !");
      return;
    }
    modal.style.display = "block";
  })
  .catch(err => {
    hideSpinner();
    console.error("Erreur proposition Savoirs :", err);
    alert("Erreur proposition Savoirs : " + err.message);
  });
};
