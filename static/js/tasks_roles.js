// static/js/tasks_roles.js

document.addEventListener('DOMContentLoaded', function() {
    console.log("tasks_roles.js chargé");
  });
  
  /**
   * Affiche le formulaire d'ajout de rôles pour la tâche donnée
   * et charge la liste des rôles existants depuis le backend (pour le <select>)
   */
  function showTaskRoleForm(taskId) {
    const form = document.getElementById(`task-role-form-${taskId}`);
    if (form) {
      form.style.display = 'block';
      loadExistingRoles(taskId);
    }
  }
  
  /**
   * Cache le formulaire d'ajout de rôles
   */
  function hideTaskRoleForm(taskId) {
    const form = document.getElementById(`task-role-form-${taskId}`);
    if (form) {
      form.style.display = 'none';
    }
  }
  
  /**
   * Charge la liste des rôles existants (pour le <select> "existing-roles-...")
   */
  function loadExistingRoles(taskId) {
    fetch('/roles/list')
      .then(response => response.json())
      .then(data => {
        const selectElem = document.getElementById('existing-roles-' + taskId);
        if (selectElem) {
          // Vider puis remplir la liste
          selectElem.innerHTML = '';
          data.forEach(role => {
            let option = document.createElement('option');
            option.value = role.id;
            option.text = role.name;
            selectElem.appendChild(option);
          });
        }
      })
      .catch(error => {
        console.error('Erreur lors du chargement des rôles existants:', error);
      });
  }
  
  /**
   * Ajoute un ou plusieurs rôles à la tâche, avec un statut
   */
  function submitTaskRoles(taskId) {
    const existingSelect = document.getElementById(`existing-roles-${taskId}`);
    const newRolesInput = document.getElementById(`new-roles-${taskId}`);
    const statusSelect  = document.getElementById(`role-status-${taskId}`);
  
    const existingRoleIds = Array.from(existingSelect.selectedOptions).map(opt => parseInt(opt.value));
    const newRoles = newRolesInput.value
      .split(',')
      .map(r => r.trim())
      .filter(r => r.length > 0);
    const chosenStatus = statusSelect.value;
  
    const payload = {
      existing_role_ids: existingRoleIds,
      new_roles: newRoles,
      status: chosenStatus
    };
  
    fetch(`/tasks/${taskId}/roles/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(err => {
          throw new Error(err.error || "Erreur lors de l'ajout des rôles.");
        });
      }
      return response.json();
    })
    .then(data => {
      console.log("Rôles ajoutés:", data.added_roles);
      hideTaskRoleForm(taskId);
      existingSelect.selectedIndex = -1;
      newRolesInput.value = '';
  
      // Recharger la liste des rôles
      loadTaskRolesForDisplay(taskId);
    })
    .catch(error => {
      alert(error.message);
      console.error("Erreur lors de la soumission des rôles:", error);
    });
  }
  
  /**
   * Récupère la liste des rôles existants pour la tâche, et l'affiche dans le DOM
   */
  function loadTaskRolesForDisplay(taskId) {
    fetch(`/tasks/${taskId}/roles`)
      .then(r => r.json())
      .then(data => {
        const rolesUl = document.querySelector(`#roles-for-task-${taskId} ul`);
        if (!rolesUl) return;
  
        rolesUl.innerHTML = '';
  
        data.roles.forEach(role => {
          let li = document.createElement('li');
          // Ex: "Coordination projet (Approbateur)"
          li.textContent = role.name + " (" + role.status + ")";
          rolesUl.appendChild(li);
        });
      })
      .catch(error => {
        console.error("Erreur lors du chargement des rôles pour la tâche " + taskId, error);
      });
  }
  