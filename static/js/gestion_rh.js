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

    data.forEach(user => {
      const div = document.createElement("div");
      div.className = "collab-item";

      const label = document.createElement("div");
      label.className = "collab-name";
      label.textContent = user.name;

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
      saveBtn.textContent = "Enregistrer";
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

      label.addEventListener("click", () => {
        div.classList.toggle("expanded");
      });

      div.appendChild(label);
      div.appendChild(summary);
      div.appendChild(editZone);
      container.appendChild(div);
    });
  }

  document.getElementById("search-collab").addEventListener("input", loadCollaborateurs);
  document.getElementById("filter-role").addEventListener("change", loadCollaborateurs);

  window.roles = Array.from(document.querySelectorAll("#filter-role option"))
    .filter(o => o.value)
    .map((o, i) => ({ id: i + 1, name: o.value }));

  loadCollaborateurs();
});
