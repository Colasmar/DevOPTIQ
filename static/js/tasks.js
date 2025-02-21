/* tasks.js - Gestion des tâches */

// Affiche le formulaire d'ajout d'une tâche pour une activité donnée
function showTaskForm(activityId) {
  document.getElementById('task-form-' + activityId).style.display = 'block';
}

// Cache le formulaire d'ajout d'une tâche pour une activité donnée
function hideTaskForm(activityId) {
  document.getElementById('task-form-' + activityId).style.display = 'none';
}

// Soumet une nouvelle tâche pour une activité
function submitTask(activityId) {
  const taskName = document.getElementById('task-name-' + activityId).value;
  const taskDesc = document.getElementById('task-desc-' + activityId).value;
  if (!taskName) {
    alert("Le nom de la tâche est requis.");
    return;
  }
  fetch('/activities/' + activityId + '/tasks/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: taskName, description: taskDesc })
  })
  .then(response => {
    if (response.ok) return response.json();
    throw new Error("Erreur lors de l'ajout de la tâche.");
  })
  .then(data => {
    let tasksList = document.getElementById('tasks-list-' + activityId);
    if (!tasksList) {
      tasksList = document.createElement('ul');
      tasksList.id = 'tasks-list-' + activityId;
      const tasksSection = document.getElementById('task-form-' + activityId).parentNode;
      tasksSection.insertBefore(tasksList, tasksSection.firstChild);
    }
    const li = document.createElement('li');
    li.className = 'task';
    li.id = 'task-' + data.id;
    li.setAttribute('data-task-id', data.id);
    li.innerHTML = `
      <div class="task-row">
        <div class="task-left">
          <i class="fa-solid fa-bars icon-btn" style="cursor: move;"></i>
          <span class="task-title">
            <strong id="task-name-display-${data.id}">${data.name}</strong>
            ${data.description ? ' - <span id="task-desc-display-' + data.id + '">' + data.description + '</span>' : ''}
          </span>
          <button class="icon-btn" onclick="deleteTask('${activityId}', '${data.id}')">
            <i class="fa-solid fa-trash"></i>
          </button>
          <button class="icon-btn" onclick="showEditTaskForm('${activityId}', '${data.id}', '${data.name}', '${data.description || ''}')">
            <i class="fa-solid fa-pencil"></i>
          </button>
        </div>
        <div class="task-right">
          <div class="tools-list" id="tools-for-task-${data.id}">
            <ul>
              <li id="no-tools-msg-${data.id}">Aucun outil associé.</li>
              <li class="add-tool-li">
                <button class="icon-btn add-tool-btn" onclick="showToolForm('${data.id}')">
                  <i class="fa-solid fa-plus"></i>
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div class="edit-task-form" id="edit-task-form-${data.id}">
        <input type="text" id="edit-task-name-${data.id}" placeholder="Nom de la tâche" />
        <input type="text" id="edit-task-desc-${data.id}" placeholder="Description (optionnelle)" />
        <button onclick="submitEditTask('${activityId}', '${data.id}')">Enregistrer</button>
        <button onclick="hideEditTaskForm('${data.id}')">Annuler</button>
      </div>
      <div id="tool-form-${data.id}" class="tool-form" style="display: none;">
        <div>
          <label for="existing-tools-${data.id}">Outils existants:</label>
          <select id="existing-tools-${data.id}" multiple style="width: 100%;"></select>
        </div>
        <div>
          <label for="new-tools-${data.id}">Nouveaux outils (séparés par des virgules):</label>
          <input type="text" id="new-tools-${data.id}" placeholder="Ex: Outil1, Outil2" style="width: 100%;" />
        </div>
        <button onclick="submitTools('${data.id}')">Enregistrer</button>
        <button onclick="hideToolForm('${data.id}')">Annuler</button>
      </div>
    `;
    tasksList.appendChild(li);
    document.getElementById('task-name-' + activityId).value = "";
    document.getElementById('task-desc-' + activityId).value = "";
    hideTaskForm(activityId);
  })
  .catch(error => {
    alert(error.message);
  });
}

// Supprime une tâche donnée
function deleteTask(activityId, taskId) {
  if (!confirm("Confirmez-vous la suppression de cette tâche ?")) return;
  fetch(`/activities/${activityId}/tasks/${taskId}`, { method: 'DELETE' })
  .then(response => response.json())
  .then(data => {
    const taskElem = document.getElementById('task-' + taskId);
    if (taskElem) {
      taskElem.parentNode.removeChild(taskElem);
    }
  })
  .catch(error => {
    alert(error.message);
  });
}

// Affiche le formulaire d'édition d'une tâche
function showEditTaskForm(activityId, taskId, name, description) {
  document.getElementById('edit-task-form-' + taskId).style.display = 'block';
  document.getElementById('edit-task-name-' + taskId).value = name;
  document.getElementById('edit-task-desc-' + taskId).value = description;
}

// Cache le formulaire d'édition d'une tâche
function hideEditTaskForm(taskId) {
  document.getElementById('edit-task-form-' + taskId).style.display = 'none';
}

// Soumet les modifications d'une tâche
function submitEditTask(activityId, taskId) {
  const newName = document.getElementById('edit-task-name-' + taskId).value;
  const newDesc = document.getElementById('edit-task-desc-' + taskId).value;
  if (!newName) {
    alert("Le nom de la tâche est requis.");
    return;
  }
  fetch(`/activities/${activityId}/tasks/${taskId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName, description: newDesc })
  })
  .then(response => response.json())
  .then(data => {
    const nameElem = document.getElementById('task-name-display-' + taskId);
    if (nameElem) {
      nameElem.textContent = data.name;
    }
    const descElem = document.getElementById('task-desc-display-' + taskId);
    if (descElem) {
      descElem.textContent = data.description;
    } else if (data.description) {
      const taskTitle = document.querySelector('#task-name-display-' + taskId).parentNode;
      const span = document.createElement('span');
      span.id = 'task-desc-display-' + taskId;
      span.textContent = data.description;
      taskTitle.appendChild(document.createTextNode(" - "));
      taskTitle.appendChild(span);
    }
    hideEditTaskForm(taskId);
  })
  .catch(error => {
    alert(error.message);
  });
}

/* --- DRAG & DROP POUR LES TÂCHES --- */
document.addEventListener('DOMContentLoaded', function() {
  const taskLists = document.querySelectorAll('[id^="tasks-list-"]');
  taskLists.forEach(list => {
    Sortable.create(list, {
      animation: 150,
      handle: '.fa-bars',
      onEnd: function(evt) {
        const listId = list.getAttribute('id'); // ex: tasks-list-123
        const activityId = listId.split('-')[2];   // ex: 123
        console.log("Reorder tasks for activityId=", activityId);
        let newOrder = [];
        list.querySelectorAll('li.task').forEach(taskElem => {
          newOrder.push(taskElem.getAttribute('data-task-id'));
        });
        fetch('/activities/' + activityId + '/tasks/reorder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order: newOrder })
        }).then(function(response) {
          if (!response.ok) {
            console.error("Erreur de sauvegarde de l'ordre");
          }
        });
      }
    });
  });
});
