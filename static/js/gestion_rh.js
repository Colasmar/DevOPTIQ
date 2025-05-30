// Fonction toast
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

    // bouton Supprimer
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
});
