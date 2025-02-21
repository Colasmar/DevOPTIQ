/* optiq.js - Version complète avec gestion des tâches, outils, habiletés socio-cognitives (HSC)
   et nouvelle fonctionnalité "Traduire softskills" avec niveaux 1..4 affichés en clair.
*/

console.log("optiq.js loaded!");

// ==============================
// 1) Ouverture / Fermeture des activités
// ==============================
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
console.log("toggleDetails is", typeof toggleDetails);

// ==============================
// 2) Chargement du DOM
// ==============================
document.addEventListener('DOMContentLoaded', function() {
  console.log("DOMContentLoaded event triggered!");

  // DRAG & DROP pour réordonner les tâches
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

  console.log("Initialization done. All tasks & tools management loaded.");
});

// ==============================
// 3) Fonctions de récupération d’informations d’activité
// ==============================
function getActivityDetails(activityId) {
    var detailsElem = document.getElementById('details-' + activityId);
    return detailsElem ? detailsElem.innerText : "";
}

function getCompetenciesData(activityId) {
    var compElem = document.getElementById('competencies-' + activityId);
    return compElem ? compElem.innerText : "";
}

// ==============================
// 4) GESTION DES TÂCHES
// ==============================
function showTaskForm(activityId) {
  document.getElementById('task-form-' + activityId).style.display = 'block';
}
function hideTaskForm(activityId) {
  document.getElementById('task-form-' + activityId).style.display = 'none';
}

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

function showEditTaskForm(activityId, taskId, name, description) {
  document.getElementById('edit-task-form-' + taskId).style.display = 'block';
  document.getElementById('edit-task-name-' + taskId).value = name;
  document.getElementById('edit-task-desc-' + taskId).value = description;
}
function hideEditTaskForm(taskId) {
  document.getElementById('edit-task-form-' + taskId).style.display = 'none';
}
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

// ==============================
// 5) GESTION DES OUTILS
// ==============================
function showToolForm(taskId) {
  document.getElementById('tool-form-' + taskId).style.display = 'block';
  fetch('/tools/all')
  .then(response => response.json())
  .then(data => {
    const selectElem = document.getElementById('existing-tools-' + taskId);
    selectElem.innerHTML = "";
    data.forEach(tool => {
      const option = document.createElement('option');
      option.value = tool.id;
      option.text = tool.name;
      selectElem.appendChild(option);
    });
  })
  .catch(error => {
    alert("Erreur lors du chargement des outils existants: " + error.message);
  });
}
function hideToolForm(taskId) {
  document.getElementById('tool-form-' + taskId).style.display = 'none';
}
function submitTools(taskId) {
  const selectElem = document.getElementById('existing-tools-' + taskId);
  const newToolsInput = document.getElementById('new-tools-' + taskId);
  const existingToolIds = Array.from(selectElem.selectedOptions).map(opt => parseInt(opt.value));
  const newTools = newToolsInput.value.split(",").map(item => item.trim()).filter(item => item.length > 0);

  const payload = {
    task_id: parseInt(taskId),
    existing_tool_ids: existingToolIds,
    new_tools: newTools
  };
  fetch('/tools/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(response => response.json())
  .then(data => {
    const noToolsMsg = document.getElementById('no-tools-msg-' + taskId);
    if (noToolsMsg) {
      noToolsMsg.parentNode.removeChild(noToolsMsg);
    }
    const toolsContainer = document.getElementById('tools-for-task-' + taskId);
    let ul = toolsContainer.querySelector('ul');
    if (!ul) {
      ul = document.createElement('ul');
      toolsContainer.appendChild(ul);
    }
    let addBtn = ul.querySelector('li.add-tool-li');
    if (addBtn) {
      addBtn.parentNode.removeChild(addBtn);
    }
    data.added_tools.forEach(tool => {
      const li = document.createElement('li');
      li.setAttribute("data-tool-id", tool.id);
      li.innerHTML = tool.name + ` <button class="icon-btn" onclick="deleteToolFromTask('${taskId}', '${tool.id}')">
                                    <i class="fa-solid fa-trash"></i></button>`;
      ul.appendChild(li);
    });
    const newAddLi = document.createElement('li');
    newAddLi.className = 'add-tool-li';
    newAddLi.innerHTML = `<button class="icon-btn add-tool-btn" onclick="showToolForm('${taskId}')">
                            <i class="fa-solid fa-plus"></i>
                          </button>`;
    ul.appendChild(newAddLi);
    selectElem.selectedIndex = -1;
    newToolsInput.value = "";
    hideToolForm(taskId);
  })
  .catch(error => {
    alert(error.message);
  });
}
function deleteToolFromTask(taskId, toolId) {
  if (!confirm("Confirmez-vous la suppression de cet outil ?")) return;
  fetch(`/activities/tasks/${taskId}/tools/${toolId}`, { method: 'DELETE' })
  .then(response => response.json())
  .then(data => {
    const toolsContainer = document.getElementById('tools-for-task-' + taskId);
    const ul = toolsContainer.querySelector('ul');
    if (!ul) return;
    const realToolElem = ul.querySelector(`li[data-tool-id="${toolId}"]`);
    if (realToolElem) {
      realToolElem.parentNode.removeChild(realToolElem);
    }
    let addBtn = ul.querySelector('li.add-tool-li');
    if (!addBtn) {
      const newAddLi = document.createElement('li');
      newAddLi.className = 'add-tool-li';
      newAddLi.innerHTML = `<button class="icon-btn add-tool-btn" onclick="showToolForm('${taskId}')">
                              <i class="fa-solid fa-plus"></i>
                            </button>`;
      ul.appendChild(newAddLi);
    }
  })
  .catch(error => {
    alert(error.message);
  });
}

console.log("All tasks & tools functions loaded. If no errors, everything is declared properly.");

// ==============================
// 6) GESTION DES HABILETÉS SOCIO-COGNITIVES (HSC)
// ==============================

// Convertit un niveau numérique (1..4) en label
function translateLevelToText(level) {
  switch(level) {
    case "1": return "Aptitude";
    case "2": return "Acquisition";
    case "3": return "Maîtrise";
    case "4": return "Excellence";
    default:  return "Inconnu";
  }
}

// Lancement de l'IA pour définir les HSC via le bouton "Définir HSC"
$(document).on('click', '.define-hsc-btn', function() {
  const activityId = $(this).data('activity-id');
  proposeSoftskills(activityId);
});

/**
 * Appel à l'endpoint /softskills/propose pour récupérer 3-4 habiletés socio-cognitives via l'IA.
 */
function proposeSoftskills(activityId) {
    var activityData = getActivityDetails(activityId);
    var competenciesData = getCompetenciesData(activityId);
    $.ajax({
        url: '/softskills/propose',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            activity: activityData,
            competencies: competenciesData
        }),
        success: function(response) {
            renderSoftskills(activityId, response);
        },
        error: function() {
            alert("Erreur lors de la récupération des habiletés socio-cognitives.");
        }
    });
}

function renderSoftskills(activityId, softskills) {
    var container = document.getElementById('softskills-list-' + activityId);
    container.innerHTML = "";
    softskills.forEach(function(item) {
        addSoftskillItemToDOM(activityId, item.habilete, item.niveau);
    });
}

// ==============================
// 7) GESTION DE LA TRADUCTION DES SOFTSKILLS
// ==============================

// Ouvre le modal de traduction (modal défini dans translate_softskills_modal.html)
function openTranslateSoftskillsModal(activityId) {
  window.translateSoftskillsActivityId = activityId;
  document.getElementById('translateSoftskillsModal').style.display = 'block';
}

// Ferme le modal de traduction
function closeTranslateSoftskillsModal() {
  document.getElementById('translateSoftskillsModal').style.display = 'none';
  window.translateSoftskillsActivityId = null;
}

// Soumet le texte entré pour traduction et ajoute les HSC traduites
function submitSoftskillsTranslation() {
  let activityId = window.translateSoftskillsActivityId;
  if (!activityId) {
    alert("Identifiant de l'activité introuvable.");
    return;
  }
  let userInput = document.getElementById('translateSoftskillsInput').value.trim();
  if (!userInput) {
    alert("Veuillez saisir du texte.");
    return;
  }
  $.ajax({
    url: '/softskills/translate',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ user_input: userInput }),
    success: function(response) {
      response.forEach(function(item) {
        addSoftskillItemToDOM(activityId, item.habilete, item.niveau);
      });
      closeTranslateSoftskillsModal();
    },
    error: function() {
      alert("Erreur lors de la traduction des softskills.");
    }
  });
}

// Événement pour le bouton "Traduire softskills"
$(document).on('click', '.translate-softskills-btn', function() {
  const activityId = $(this).data('activity-id');
  openTranslateSoftskillsModal(activityId);
});

// ==============================
// 8) Gestion manuelle des HSC
// ==============================
function showSoftskillForm(activityId) {
  document.getElementById('softskill-form-' + activityId).style.display = 'block';
}
function hideSoftskillForm(activityId) {
  document.getElementById('softskill-form-' + activityId).style.display = 'none';
}
function submitSoftskill(activityId) {
  let nameInput = document.getElementById('softskill-name-' + activityId);
  let levelInput = document.getElementById('softskill-level-' + activityId);
  let hscName = nameInput.value.trim();
  let hscLevel = levelInput.value.trim();
  if(!hscName) {
    alert("Veuillez saisir un nom d'habileté.");
    return;
  }
  if(!hscLevel || !["1","2","3","4"].includes(hscLevel)) {
    alert("Le niveau doit être 1, 2, 3 ou 4.");
    return;
  }
  addSoftskillItemToDOM(activityId, hscName, hscLevel);
  nameInput.value = "";
  levelInput.value = "";
  hideSoftskillForm(activityId);
}

function addSoftskillItemToDOM(activityId, hscName, hscLevel) {
  let container = document.getElementById('softskills-list-' + activityId);
  let index = container.children.length;
  let softskillItem = document.createElement('div');
  softskillItem.className = 'softskill-item';
  softskillItem.setAttribute('data-index', index);
  let levelLabel = translateLevelToText(hscLevel);
  softskillItem.innerHTML = `
    <span class="softskill-text">${hscName} (Niveau: <span class="softskill-level">${levelLabel}</span>)</span>
    <i class="fas fa-pencil-alt edit-softskill" title="Modifier"></i>
    <i class="fas fa-trash delete-softskill" title="Supprimer"></i>
    <div class="edit-softskill-form" id="edit-softskill-form-${activityId}-${index}" style="display:none;">
      <label>Habileté :</label>
      <input type="text" id="edit-softskill-name-${activityId}-${index}" value="${hscName}" />
      <label>Niveau (1..4) :</label>
      <input type="number" min="1" max="4" id="edit-softskill-level-${activityId}-${index}" value="${hscLevel}" />
      <button onclick="submitEditSoftskill('${activityId}', ${index})">Enregistrer</button>
      <button onclick="hideEditSoftskillForm('${activityId}', ${index})">Annuler</button>
    </div>
  `;
  container.appendChild(softskillItem);
}

$(document).on('click', '.edit-softskill', function() {
  let itemElem = $(this).closest('.softskill-item');
  let index = itemElem.data('index');
  let parentId = itemElem.parent().attr('id'); // ex: "softskills-list-123"
  let activityId = parentId.split('-')[2];
  showEditSoftskillForm(activityId, index);
});
function showEditSoftskillForm(activityId, index) {
  document.getElementById(`edit-softskill-form-${activityId}-${index}`).style.display = 'block';
}
function hideEditSoftskillForm(activityId, index) {
  document.getElementById(`edit-softskill-form-${activityId}-${index}`).style.display = 'none';
}
function submitEditSoftskill(activityId, index) {
  let nameInput = document.getElementById(`edit-softskill-name-${activityId}-${index}`);
  let levelInput = document.getElementById(`edit-softskill-level-${activityId}-${index}`);
  let newName = nameInput.value.trim();
  let newLevel = levelInput.value.trim();
  if(!newName) {
    alert("Veuillez saisir un nom d'habileté.");
    return;
  }
  if(!["1","2","3","4"].includes(newLevel)) {
    alert("Le niveau doit être 1, 2, 3 ou 4.");
    return;
  }
  let container = document.getElementById('softskills-list-' + activityId);
  let itemElem = container.querySelector(`.softskill-item[data-index="${index}"]`);
  let textElem = itemElem.querySelector('.softskill-text');
  let levelLabel = translateLevelToText(newLevel);
  textElem.innerHTML = `${newName} (Niveau: <span class="softskill-level">${levelLabel}</span>)`;
  hideEditSoftskillForm(activityId, index);
}

$(document).on('click', '.delete-softskill', function() {
  if(!confirm("Voulez-vous supprimer cette habileté ?")) return;
  $(this).closest('.softskill-item').remove();
});
