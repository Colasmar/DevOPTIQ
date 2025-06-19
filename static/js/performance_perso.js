function insertPerformanceBlock(activityId, container) {
  if (!selectedUserId) return;

  container.innerHTML = '';

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

      // Performances personnalisées
      fetch(`/competences/performance_perso_list/${selectedUserId}/${activityId}`)
        .then(r => r.json())
        .then(list => {
          const subContainer = document.createElement('div');
          subContainer.className = 'perf-perso-container';

          if (list.length === 0) {
            const msg = document.createElement('p');
            msg.className = 'no-perf-message';
            msg.innerHTML = "<em>Aucune performance personnalisée définie pour cette activité.</em>";
            subContainer.appendChild(msg);
          } else {
            list.forEach(perf => {
              renderPersonalPerf(perf, subContainer, activityId);
            });
          }

          const actionRow = document.createElement('div');
          actionRow.style.display = 'flex';
          actionRow.style.gap = '10px';

          const addBtn = document.createElement('button');
          addBtn.className = 'btn-add-perf';
          addBtn.textContent = "+ Ajouter une performance";
          addBtn.addEventListener('click', () => {
            renderPersonalPerf({ content: "", id: null }, subContainer, activityId, true);
          });

          const historyBtn = document.createElement('button');
          historyBtn.className = 'btn-history-perf';
          historyBtn.textContent = 'Historique';
          historyBtn.addEventListener('click', () => {
            showPerformanceHistory(selectedUserId, activityId, data.content);
          });

          actionRow.appendChild(addBtn);
          actionRow.appendChild(historyBtn);
          subContainer.appendChild(actionRow);

          container.appendChild(subContainer);
        });
    });
}

function renderPersonalPerf(perf, container, activityId, isNew = false) {
  const wrapper = document.createElement('div');
  wrapper.className = 'perf-perso-block';

  const textarea = document.createElement('textarea');
  textarea.className = 'perf-text';
  textarea.value = perf.content || '';
  wrapper.appendChild(textarea);

  const dateSpan = document.createElement('div');
  dateSpan.className = 'perf-date';
  if (perf.updated_at) {
    dateSpan.textContent = `Dernière modification : ${perf.updated_at}`;
  }
  wrapper.appendChild(dateSpan);

  const btnSave = document.createElement('button');
  btnSave.className = 'btn-save-perf';
  btnSave.textContent = 'Enregistrer';

  const btnDelete = document.createElement('button');
  btnDelete.className = 'btn-delete-perf';
  btnDelete.textContent = 'Supprimer';

  const btnGroup = document.createElement('div');
  btnGroup.className = 'perf-buttons';
  btnGroup.appendChild(btnSave);
  btnGroup.appendChild(btnDelete);
  wrapper.appendChild(btnGroup);

  btnSave.addEventListener('click', () => {
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

  btnDelete.addEventListener('click', () => {
    if (!perf.id) {
      wrapper.remove();
    } else {
      fetch(`/competences/performance_perso/${perf.id}`, {
        method: 'DELETE'
      })
      .then(r => r.json())
      .then(resp => {
        if (resp.success) {
          showToast("Performance supprimée.", "success");
          insertPerformanceBlock(activityId, container.parentElement);
        } else {
          showToast("Erreur : " + resp.message, "error");
        }
      });
    }
  });

  container.insertBefore(wrapper, container.querySelector('.btn-add-perf')?.parentElement || null);
}

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("perf-history-modal");
  const closeBtn = modal.querySelector(".close-history");
  closeBtn.addEventListener("click", () => {
    modal.classList.add("hidden");
  });
});

window.showPerformanceHistory = function(userId, activityId, activityTitle = '') {
  fetch(`/competences/performance_history/${userId}/${activityId}`)
    .then(r => r.json())
    .then(history => {
      const container = document.getElementById("history-entries");
      const modalTitle = document.getElementById("history-modal-title");
      container.innerHTML = "";
      modalTitle.textContent = `Historique des performances personnalisées – ${activityTitle}`;

      if (history.length === 0) {
        container.innerHTML = "<p><em>Aucun historique trouvé.</em></p>";
      } else {
        history.forEach(h => {
          const div = document.createElement("div");
          div.classList.add("history-entry");
          div.innerHTML = `
            <p>
              <strong>${h.updated_at}</strong> 
              ${h.deleted ? '<span style="color:red">(supprimée)</span>' : ''}
              <br>${h.content}
            </p>`;
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
