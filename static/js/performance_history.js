document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("perf-history-modal");
  const content = document.getElementById("perf-history-content");
  const closeBtn = modal.querySelector(".close-modal");

  closeBtn.addEventListener("click", () => {
    modal.classList.add("hidden");
  });

  document.body.addEventListener("click", e => {
    if (e.target.matches(".btn-show-history")) {
      const activityId = e.target.dataset.activity;
      const userId = e.target.dataset.user;

      fetch(`/competences/performance_history/${userId}/${activityId}`)
        .then(r => r.json())
        .then(data => {
          content.innerHTML = "";
          if (!data.length) {
            content.innerHTML = "<p><em>Aucun historique enregistré.</em></p>";
          } else {
            data.forEach(entry => {
              const block = document.createElement("div");
              block.classList.add("history-entry");
              block.innerHTML = `
                <p>${entry.content}</p>
                <small><i>Modifié le ${entry.updated_at}</i></small>
                <hr>
              `;
              content.appendChild(block);
            });
          }
          modal.classList.remove("hidden");
        });
    }
  });
});
