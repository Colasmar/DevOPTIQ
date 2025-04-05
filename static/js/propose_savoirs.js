document.addEventListener("DOMContentLoaded", function () {
  const bouton = document.querySelector("#boutonProposerSavoirs");

  if (!bouton) {
      console.error("Le bouton #boutonProposerSavoirs est introuvable dans le HTML.");
      return;
  }

  bouton.addEventListener("click", function () {
      const activityId = bouton.getAttribute("data-activity-id");

      fetch("/propose_savoirs", {
          method: "POST",
          headers: {
              "Content-Type": "application/json"
          },
          body: JSON.stringify({ activity_id: activityId })
      })
      .then(response => response.json())
      .then(data => {
          alert(data.message || data.error);
      })
      .catch(error => {
          console.error("Erreur de requête : ", error);
          alert("Erreur technique : " + error);
      });
  });
});
