function insertPerformanceBlock(activityId, container) {
  if (!selectedUserId) return;

  container.innerHTML = '';

  // Performance générale
  fetch(`/competences/general_performance/${activityId}`)
    .then(r => r.json())
    .then(data => {
      const perfDiv = document.createElement('div');
      perfDiv.classList.add('perf-general');
      perfDiv.innerHTML = `
        <h4>Performance générale</h4>
        <div class="perf-fixed">${data.content || '<em>Aucune performance définie.</em>'}</div>
      `;
      container.appendChild(perfDiv);

      // Performances personnalisées — on les injecte après
      fetch(`/competences/performance_perso_list/${selectedUserId}/${activityId}`)
        .then(r => r.json())
        .then(list => {
          const subContainer = document.createElement('div');
          subContainer.className = 'perf-perso-container';

          if (list.length === 0) {
            subContainer.innerHTML = `<p class="no-perf-message"><em>Aucune performance définie pour cette activité.</em></p>`;
          } else {
            list.forEach(perf => {
              renderPersonalPerf(perf, subContainer, activityId);
            });
          }

          const addBtn = document.createElement('button');
          addBtn.className = 'btn-add-perf';
          addBtn.textContent = "+ Ajouter une performance";
          addBtn.addEventListener('click', () => {
            renderPersonalPerf({ content: "", id: null }, subContainer, activityId, true);
          });
          subContainer.appendChild(addBtn);

          container.appendChild(subContainer);  // en dessous du bloc général
        });
    });
}

function renderPersonalPerf(perf, container, activityId, isNew = false) {
  const wrapper = document.createElement('div');
  wrapper.className = 'perf-perso-block';

  const idAttr = perf.id ? `data-id="${perf.id}"` : '';
  wrapper.innerHTML = `
    <textarea class="perf-text">${perf.content || ''}</textarea>
    <div class="perf-date">${perf.updated_at ? `Dernière modification : ${perf.updated_at}` : ''}</div>
    <button class="btn-save-perf">Enregistrer</button>
    <button class="btn-delete-perf">Supprimer</button>
    <button class="btn-history-perf">Historique</button>
  `;

  const textarea = wrapper.querySelector('.perf-text');
  const saveBtn = wrapper.querySelector('.btn-save-perf');
  const deleteBtn = wrapper.querySelector('.btn-delete-perf');
  const historyBtn = wrapper.querySelector('.btn-history-perf');

  saveBtn.addEventListener('click', () => {
    fetch('/competences/performance_perso', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: selectedUserId,
        activity_id: activityId,
        content: textarea.value
      })
    })
    .then(r => r.json())
    .then(resp => {
      if (resp.success) {
        showToast("Performance enregistrée.", "success");
        insertPerformanceBlock(activityId, container.parentElement);
      } else {
        showToast("Erreur : " + resp.message, "error");
      }
    });
  });

  deleteBtn.addEventListener('click', () => {
    textarea.value = "";
  });

  historyBtn.addEventListener('click', () => {
    showPerformanceHistory(selectedUserId, activityId);
  });

  container.insertBefore(wrapper, container.querySelector('.btn-add-perf'));
}

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("perf-history-modal");
  const closeBtn = modal.querySelector(".close-history");
  closeBtn.addEventListener("click", () => {
    modal.classList.add("hidden");
  });
});

window.showPerformanceHistory = function(userId, activityId) {
  fetch(`/competences/performance_history/${userId}/${activityId}`)
    .then(r => r.json())
    .then(history => {
      const container = document.getElementById("history-entries");
      container.innerHTML = "";

      if (history.length === 0) {
        container.innerHTML = "<p><em>Aucun historique trouvé.</em></p>";
      } else {
        history.forEach(h => {
          const div = document.createElement("div");
          div.classList.add("history-entry");
          div.innerHTML = `<p><strong>${h.updated_at}</strong><br>${h.content}</p>`;
          container.appendChild(div);
        });
      }

      document.getElementById("perf-history-modal").classList.remove("hidden");
    });
};

function showToast(message = "Action effectuée", type = "success") {
  const toast = document.getElementById("toast-message");
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.classList.add("hidden"), 500);
  }, 2000);
}
