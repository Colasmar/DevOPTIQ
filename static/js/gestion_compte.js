document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const statusFilter = document.getElementById('statusFilter');
  const roleFilter = document.getElementById('roleFilter');
  const searchBtn = document.getElementById('searchButton') || document.querySelector('form#filterForm button[type="submit"]');

  if (searchBtn) {
    searchBtn.addEventListener('click', (e) => {
      e.preventDefault();
      applyFilters();
    });
  }

  function applyFilters() {
    const search = searchInput?.value.toLowerCase() || '';
    const status = statusFilter?.value || '';
    const role = roleFilter?.value || '';

    const items = document.querySelectorAll('.user-item');
    items.forEach(li => {
      const name = li.dataset.name.toLowerCase();
      const liStatus = li.dataset.status;
      const liRole = li.dataset.role;

      const matchesSearch = name.includes(search);
      const matchesStatus = !status || liStatus === status;
      const matchesRole = !role || liRole === role;

      li.style.display = (matchesSearch && matchesStatus && matchesRole) ? '' : 'none';
    });
  }

  // Affichage de la modale
  document.querySelectorAll('.add-collab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const managerId = btn.dataset.managerId;
      const modal = document.getElementById(`modal-${managerId}`);
      if (modal) {
        modal.style.display = 'flex';
        loadUsersForManager(managerId);
      }
    });
  });

  // Fermeture de la modale
  document.querySelectorAll('.close-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.collab-modal').style.display = 'none';
    });
  });

  // Recherche dynamique dans les modales
  document.querySelectorAll('.collab-search').forEach(input => {
    input.addEventListener('input', () => {
      const select = document.getElementById(input.dataset.target);
      const filter = input.value.toLowerCase();

      Array.from(select.options).forEach(option => {
        option.style.display = option.text.toLowerCase().includes(filter) ? '' : 'none';
      });
    });
  });

  // Toggle pour afficher/cacher les collaborateurs d'un manager
  document.querySelectorAll('.manager-toggle').forEach(toggle => {
    toggle.addEventListener('click', () => {
      const target = document.querySelector(toggle.dataset.target);
      if (target) {
        target.classList.toggle('hidden');
      }
    });
  });

  // Toggle multiple select (activation ou désactivation du mode multi)
  document.querySelectorAll('.toggle-multi-switch').forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      const targetId = checkbox.dataset.target;
      const select = document.getElementById(targetId);
      const hiddenInput = document.getElementById(`multi_select_${targetId.split('-')[1]}`);
      if (checkbox.checked) {
        select.setAttribute('multiple', '');
        hiddenInput.value = '1';
      } else {
        select.removeAttribute('multiple');
        hiddenInput.value = '0';
      }
    });
  });

  // Soumission du formulaire d’ajout de collaborateurs dans la modale
  document.querySelectorAll('.collab-modal form').forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const managerId = form.querySelector('input[name="manager_id"]').value;

      fetch(form.action, {
        method: 'POST',
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          form.closest('.collab-modal').style.display = 'none';
          updateSubordinateList(managerId);
        } else {
          alert("Erreur lors de l'ajout.");
        }
      })
      .catch(() => {
        alert("Une erreur est survenue.");
      });
    });
  });

  function updateSubordinateList(managerId) {
    fetch(`/comptes/manager/${managerId}/subordinates`)
      .then(res => res.json())
      .then(data => {
        const container = document.querySelector(`#collab-${managerId} ul`);
        if (container) {
          container.innerHTML = '';
          if (data.subordinates.length > 0) {
            data.subordinates.forEach(s => {
              const li = document.createElement('li');
              li.innerHTML = `
                ${s.name}
                <form method="POST" action="/comptes/remove_collaborator/${s.id}" style="display:inline;">
                  <button type="submit" class="delete-btn">Supprimer</button>
                </form>
              `;
              container.appendChild(li);
            });
          } else {
            container.innerHTML = '<p>Aucun collaborateur.</p>';
          }
        }
      });
  }
});

// Fonction pour charger les utilisateurs dans la modale (via le select)
function loadUsersForManager(managerId) {
  const select = document.getElementById(`select-${managerId}`);
  if (!select || select.dataset.loaded === 'true') return;

  fetch('/comptes/users')
    .then(res => res.json())
    .then(users => {
      select.innerHTML = '';
      users.forEach(user => {
        const option = document.createElement('option');
        option.value = user.id;
        option.textContent = user.name;
        select.appendChild(option);
      });
      select.dataset.loaded = 'true';
    })
    .catch(() => {
      alert("Erreur lors du chargement des utilisateurs.");
    });
}


