function showToast(message = "Changement enregistré !") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2000);
}

document.addEventListener("DOMContentLoaded", () => {
  // PARAMÈTRES ENTREPRISE
  document.querySelectorAll(".param-group").forEach(group => {
    const key = group.dataset.key;
    const valueDiv = group.querySelector(".param-value");
    const editBtn = group.querySelector(".edit-btn");

    editBtn.addEventListener("click", () => {
      const currentValue = valueDiv.textContent.trim();
      valueDiv.innerHTML = `<input type="number" value="${currentValue}" class="param-input">`;
      editBtn.style.display = "none";

      const saveBtn = document.createElement("button");
      saveBtn.textContent = "Enregistrer";
      const cancelBtn = document.createElement("button");
      cancelBtn.textContent = "Annuler";

      saveBtn.addEventListener("click", async () => {
        const input = valueDiv.querySelector("input");
        const newValue = input.value;

        const formData = new FormData();
        formData.append("key", key);
        formData.append("value", newValue);

        await fetch("/gestion_rh/update_single_setting", {
          method: "POST",
          body: formData,
        });

        valueDiv.textContent = newValue;
        editBtn.style.display = "inline-block";
        saveBtn.remove();
        cancelBtn.remove();
        showToast("Paramètre mis à jour");
      });

      cancelBtn.addEventListener("click", () => {
        valueDiv.textContent = currentValue;
        editBtn.style.display = "inline-block";
        saveBtn.remove();
        cancelBtn.remove();
      });

      group.querySelector(".param-actions").appendChild(saveBtn);
      group.querySelector(".param-actions").appendChild(cancelBtn);
    });
  });

  // CRÉATION DE RÔLE
  const createRoleForm = document.getElementById("create-role-form");
  createRoleForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(createRoleForm);
    await fetch("/gestion_rh/role", {
      method: "POST",
      body: formData,
    });
    showToast("Rôle créé");
    setTimeout(() => location.reload(), 1000);
  });

  // MODIFICATION + SUPPRESSION DES RÔLES
  document.querySelectorAll(".role-group").forEach(group => {
    const roleId = group.dataset.roleId;
    const label = group.querySelector(".role-label");
    const editBtn = group.querySelector(".edit-role-btn");

    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "Supprimer";
    deleteBtn.style.marginLeft = "10px";
    deleteBtn.style.backgroundColor = "#e74c3c";

    deleteBtn.addEventListener("click", async () => {
      if (confirm("Supprimer ce rôle ?")) {
        const response = await fetch(`/gestion_rh/delete_role/${roleId}`, {
          method: "POST"
        });
        if (response.ok) {
          group.remove();
          showToast("Rôle supprimé");
        }
      }
    });

    editBtn.after(deleteBtn);
    editBtn.addEventListener("click", () => {
      const currentValue = label.textContent.trim();
      label.innerHTML = `<input type="text" value="${currentValue}" class="role-input">`;
      editBtn.style.display = "none";
      deleteBtn.style.display = "none";

      const saveBtn = document.createElement("button");
      saveBtn.textContent = "Enregistrer";
      const cancelBtn = document.createElement("button");
      cancelBtn.textContent = "Annuler";

      saveBtn.addEventListener("click", async () => {
        const input = label.querySelector("input");
        const newValue = input.value;

        const formData = new FormData();
        formData.append("id", roleId);
        formData.append("name", newValue);

        await fetch("/gestion_rh/role", {
          method: "POST",
          body: formData,
        });

        label.textContent = newValue;
        editBtn.style.display = "inline-block";
        deleteBtn.style.display = "inline-block";
        saveBtn.remove();
        cancelBtn.remove();
        showToast("Rôle modifié");
      });

      cancelBtn.addEventListener("click", () => {
        label.textContent = currentValue;
        editBtn.style.display = "inline-block";
        deleteBtn.style.display = "inline-block";
        saveBtn.remove();
        cancelBtn.remove();
      });

      group.querySelector(".role-actions").appendChild(saveBtn);
      group.querySelector(".role-actions").appendChild(cancelBtn);
    });
  });

  // COLLABORATEURS
  async function loadCollaborateurs() {
    const search = document.getElementById("search-collab").value;
    const role = document.getElementById("filter-role").value;

    const res = await fetch(`/gestion_rh/collaborateurs?search=${encodeURIComponent(search)}&role=${encodeURIComponent(role)}`);
    const data = await res.json();

    const container = document.getElementById("collaborateur-list");
    container.innerHTML = "";

    window.fullCollabData = data;
    renderPartialCollaborators();
  }

  function renderPartialCollaborators(showAll = false) {
    const container = document.getElementById("collaborateur-list");
    container.innerHTML = "";
    const data = showAll ? window.fullCollabData : window.fullCollabData.slice(0, 4);

    data.forEach(user => {
      const div = document.createElement("div");
      div.className = "collab-item";

      // Nom du collaborateur (cliquable pour éditer)
      const label = document.createElement("div");
      label.className = "collab-name";
      label.textContent = user.name;
      
      // Icône d'édition du nom
      const editNameIcon = document.createElement("span");
      editNameIcon.innerHTML = " ✏️";
      editNameIcon.style.cursor = "pointer";
      editNameIcon.style.fontSize = "0.8em";
      editNameIcon.title = "Modifier le nom";
      editNameIcon.addEventListener("click", (e) => {
        e.stopPropagation();
        editCollaboratorName(user.id, user.name, label);
      });
      label.appendChild(editNameIcon);

      const summary = document.createElement("div");
      summary.className = "collab-summary";
      summary.textContent = "Rôles : " + (user.roles.length ? user.roles.join(", ") : "Aucun");

      const editZone = document.createElement("div");
      editZone.className = "collab-edit-zone";

      const roleContainer = document.createElement("div");
      roleContainer.className = "collab-role-checkboxes";

      roles.forEach(r => {
        const cbLabel = document.createElement("label");
        cbLabel.className = "checkbox-label";
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = r.id;
        checkbox.checked = user.roles.includes(r.name);
        if (checkbox.checked) cbLabel.classList.add("active");

        checkbox.addEventListener("change", () => {
          if (checkbox.checked) {
            cbLabel.classList.remove("removed");
            cbLabel.classList.add("active");
          } else if (user.roles.includes(r.name)) {
            cbLabel.classList.remove("active");
            cbLabel.classList.add("removed");
          } else {
            cbLabel.classList.remove("removed");
            cbLabel.classList.remove("active");
          }
        });

        cbLabel.appendChild(checkbox);
        cbLabel.appendChild(document.createTextNode(" " + r.name));
        roleContainer.appendChild(cbLabel);
      });

      const saveBtn = document.createElement("button");
      saveBtn.textContent = "Enregistrer les rôles";
      saveBtn.addEventListener("click", async () => {
        const selectedRoles = Array.from(roleContainer.querySelectorAll("input:checked")).map(c => c.value);
        const formData = new FormData();
        formData.append("user_id", user.id);
        selectedRoles.forEach(id => formData.append("role_ids[]", id));
        await fetch("/gestion_rh/collaborateur_roles", {
          method: "POST",
          body: formData
        });
        showToast("Rôles mis à jour");

        // 🔁 recharge à chaud
        loadCollaborateurs();
        document.getElementById("mode-by-users").click();

        roleContainer.querySelectorAll(".checkbox-label").forEach(lab => {
          lab.classList.remove("removed");
          lab.classList.add("transition-reset");
          setTimeout(() => {
            lab.classList.remove("transition-reset");
          }, 500);
        });
      });

      editZone.appendChild(roleContainer);
      editZone.appendChild(saveBtn);

      label.addEventListener("click", (e) => {
        // Ne pas expand si on clique sur l'icône d'édition
        if (e.target.tagName === 'SPAN') return;
        div.classList.toggle("expanded");
      });

      div.appendChild(label);
      div.appendChild(summary);
      div.appendChild(editZone);
      container.appendChild(div);
    });

    const toggleBtn = document.getElementById("toggle-collab-view");
    if (toggleBtn) {
      toggleBtn.textContent = showAll ? "Réduire la liste" : "Afficher tous les collaborateurs";
      toggleBtn.onclick = () => renderPartialCollaborators(!showAll);
    }
  }

  // Fonction pour éditer le nom d'un collaborateur
  function editCollaboratorName(userId, currentName, labelElement) {
    const newName = prompt("Modifier le nom du collaborateur :", currentName);
    if (newName === null || newName.trim() === "" || newName.trim() === currentName) return;

    fetch(`/gestion_rh/update_collaborator_name`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, name: newName.trim() })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast("Nom mis à jour");
        loadCollaborateurs();
      } else {
        alert("Erreur lors de la mise à jour du nom");
      }
    })
    .catch(err => {
      console.error(err);
      alert("Erreur réseau");
    });
  }

  document.getElementById("search-collab").addEventListener("input", loadCollaborateurs);
  document.getElementById("filter-role").addEventListener("change", loadCollaborateurs);

  window.roles = [];  
  fetch("/gestion_rh/roles")
    .then(res => res.json())
    .then(data => {
      window.roles = data;

      const select = document.getElementById("filter-role");
      if (select) {
        data.forEach(role => {
          const option = document.createElement("option");
          option.value = role.name;
          option.textContent = role.name;
          select.appendChild(option);
        });
      }

      loadCollaborateurs();  // charger les collaborateurs une fois que les rôles sont prêts
    });
});

// ---------- AFFECTATION DES MANAGERS ----------
document.addEventListener("DOMContentLoaded", () => {
  const managerSelect = document.getElementById("manager-select");
  const container = document.getElementById("manager-assignment-container");
  const btnConfirm = document.getElementById("confirm-manager-assignment");
  let selectedUserIds = new Set();
  let selectedUserRolesMap = {};

  // Charger les managers existants (utilisateurs ayant le rôle manager)
  fetch("/gestion_rh/users_with_role?role=manager")
    .then(res => res.json())
    .then(users => {
      users.forEach(u => {
        const opt = document.createElement("option");
        opt.value = u.id;
        opt.textContent = `${u.first_name} ${u.last_name}`;
        managerSelect.appendChild(opt);
      });
    });

  // Fonction pour recharger les utilisateurs + rôles dans la section manager (utilisée dynamiquement)
  function reloadManagerUserList() {
    const activeTab = document.querySelector(".manager-options .active-tab");
    if (activeTab && activeTab.id === "mode-by-users") {
      document.getElementById("mode-by-users").click();
    } else if (activeTab && activeTab.id === "mode-by-roles") {
      document.getElementById("mode-by-roles").click();
    }
  }

  // MODE PAR RÔLES
  document.getElementById("mode-by-roles").addEventListener("click", (e) => {
    e.target.classList.add("active-tab");
    document.getElementById("mode-by-users").classList.remove("active-tab");

    fetch("/gestion_rh/roles")
      .then(r => r.json())
      .then(roles => {
        container.innerHTML = `
          <div class="manager-role-section">
            <label class="section-title">Choisir des rôles :</label>
            <div id="multi-role-checkboxes" class="collab-role-checkboxes"></div>
          </div>
          <div class="manager-user-section">
            <label class="section-title">Collaborateurs correspondants :</label>
            <div id="user-list-by-role" class="user-list"></div>
          </div>
        `;

        const roleContainer = document.getElementById("multi-role-checkboxes");

        roles.forEach(role => {
          const label = document.createElement("label");
          label.className = "checkbox-label";
          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.value = role.id;
          checkbox.dataset.name = role.name;

          checkbox.addEventListener("change", () => {
            label.classList.toggle("active", checkbox.checked);
          });

          label.appendChild(checkbox);
          label.appendChild(document.createTextNode(" " + role.name));
          roleContainer.appendChild(label);
        });

        const loadBtn = document.createElement("button");
        loadBtn.textContent = "Charger collaborateurs";
        loadBtn.style.marginTop = "12px";
        loadBtn.style.marginBottom = "12px";
        loadBtn.className = "btn-validate";
        container.appendChild(loadBtn);

        loadBtn.addEventListener("click", () => {
          const selectedRoles = Array.from(roleContainer.querySelectorAll("input:checked")).map(c => c.value);
          fetch(`/gestion_rh/users_by_roles?roles=${selectedRoles.join(",")}`)
            .then(r => r.json())
            .then(users => {
              const list = document.getElementById("user-list-by-role");
              list.innerHTML = "";
              users.forEach(user => {
                const item = document.createElement("div");
                item.className = "user-item";
                item.textContent = `${user.first_name} ${user.last_name} (${user.roles.join(", ")})`;
                item.dataset.userId = user.id;
                item.addEventListener("click", () => {
                  const id = user.id;
                  item.classList.toggle("selected");
                  if (item.classList.contains("selected")) selectedUserIds.add(id);
                  else selectedUserIds.delete(id);
                  btnConfirm.classList.remove("hidden");
                });
                list.appendChild(item);
              });
            });
        });
      });
  });

  // MODE PAR UTILISATEUR
  document.getElementById("mode-by-users").addEventListener("click", (e) => {
    e.target.classList.add("active-tab");
    document.getElementById("mode-by-roles").classList.remove("active-tab");

    fetch("/gestion_rh/users_with_roles")
      .then(r => r.json())
      .then(users => {
        container.innerHTML = `<div id="user-list-by-user" class="user-list"></div>`;
        const list = document.getElementById("user-list-by-user");
        list.innerHTML = "";
        selectedUserIds = new Set();
        selectedUserRolesMap = {};

        users.forEach(user => {
          const item = document.createElement("div");
          item.className = "user-item";
          item.dataset.userId = user.id;

          const nameDiv = document.createElement("div");
          nameDiv.textContent = `${user.first_name} ${user.last_name}`;

          const roleBox = document.createElement("div");
          roleBox.className = "user-role-box";

          user.roles.forEach(r => {
            const roleObj = window.roles.find(ro => ro.name === r);
            if (!roleObj) return;
            const cbLabel = document.createElement("label");
            cbLabel.className = "checkbox-label";
            const cb = document.createElement("input");
            cb.type = "checkbox";
            cb.value = roleObj.id;

            cb.addEventListener("change", () => {
              const uid = user.id;
              if (!selectedUserRolesMap[uid]) selectedUserRolesMap[uid] = new Set();
              if (cb.checked) {
                cbLabel.classList.add("active");
                selectedUserRolesMap[uid].add(roleObj.id);
                selectedUserIds.add(uid);
              } else {
                cbLabel.classList.remove("active");
                selectedUserRolesMap[uid].delete(roleObj.id);
                if (selectedUserRolesMap[uid].size === 0) {
                  selectedUserIds.delete(uid);
                }
              }
              btnConfirm.classList.remove("hidden");
            });

            cbLabel.appendChild(cb);
            cbLabel.appendChild(document.createTextNode(" " + r));
            roleBox.appendChild(cbLabel);
          });

          item.appendChild(nameDiv);
          item.appendChild(roleBox);
          list.appendChild(item);
        });
      });
  });

  // ENREGISTRER
  btnConfirm.addEventListener("click", () => {
    const managerId = managerSelect.value;
    if (!managerId || selectedUserIds.size === 0) return;

    let assignments = [];

    selectedUserIds.forEach(uid => {
      const roleIds = selectedUserRolesMap[uid];
      if (roleIds && roleIds.size > 0) {
        roleIds.forEach(rid => {
          assignments.push({ user_id: uid, role_id: rid });
        });
      }
    });

    fetch("/gestion_rh/assign_manager", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        manager_id: managerId,
        assignments: assignments
      })
    }).then(() => {
      showToast("Affectation réussie !");
      selectedUserIds.clear();
      selectedUserRolesMap = {};
      btnConfirm.classList.add("hidden");
      reloadManagerUserList(); // 🔁 recharger section dynamique
    });
  });

});