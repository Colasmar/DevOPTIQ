let selectedUserId = null;
let userStatus = 'user';

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const user = await getCurrentUserInfo();
        userStatus = user.status || 'user';

        if (user.roles.includes("manager")) {
            document.getElementById('manager-name').textContent = `${user.first_name} ${user.last_name}`;
            loadCollaborators(user.id);
        } else {
            fetch(`/competences/collaborators/${user.manager_id}`)
              .then(r => r.json())
              .then(collabs => {
                document.getElementById('manager-name').textContent = `${user.manager_first_name} ${user.manager_last_name}`;
                loadCollaborators(user.manager_id);
              });
        }

        const saveButton = document.getElementById('save-competencies-button');
        if (saveButton) {
            saveButton.addEventListener('click', saveAllEvaluations);
        }

        const collaboratorSelect = document.getElementById("collaborator-select");
        if (collaboratorSelect) {
            collaboratorSelect.addEventListener("change", function () {
                selectedUserId = this.value;
                if (selectedUserId) {
                    loadRolesForCollaborator(selectedUserId);
                }
            });
        }

        if (userStatus === 'administrateur') {
            const msg = document.getElementById("admin-permission-message");
            if (msg) msg.style.display = "block";
        }

        document.getElementById("toggle-summary")?.addEventListener("click", toggleGlobalSynthesis);

    } catch (err) {
        console.error("Erreur récupération utilisateur courant :", err);
    }
});

async function getCurrentUserInfo() {
  const response = await fetch('/auth/current_user_info');
  return await response.json();
}

function loadCollaborators(managerId) {
    if (!managerId) return;
    fetch(`/competences/collaborators/${managerId}`)
        .then(res => res.json())
        .then(collabs => {
            const select = document.getElementById('collaborator-select');
            select.innerHTML = '<option value="">Sélectionnez un collaborateur</option>';
            collabs.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = `${c.first_name} ${c.last_name}`;
                select.appendChild(opt);
            });
            document.getElementById('roles-sections-container').innerHTML = '';
        });
}

function loadExistingEvaluations(userId) {
    fetch(`/competences/get_user_evaluations_by_user/${userId}`)
        .then(res => res.json())
        .then(data => {
            const map = {};
            data.forEach(e => {
                const key = `${e.activity_id}_${e.item_type || 'null'}_${e.item_id || 'null'}_${e.eval_number}`;
                map[key] = { note: e.note, date: e.created_at };
            });

            document.querySelectorAll('.eval-cell').forEach(cell => {
                const activityId = cell.dataset.activity;
                const itemId = cell.dataset.id || 'null';
                const itemType = cell.dataset.type || 'null';
                const evalNumber = cell.dataset.eval;
                const key = `${activityId}_${itemType}_${itemId}_${evalNumber}`;
                const evalData = map[key];

                if (evalData) {
                    const note = evalData.note;
                    const rawDate = evalData.date;
                    let formattedDate = '';

                    try {
                        const parsedDate = new Date(rawDate);
                        if (!isNaN(parsedDate)) {
                            formattedDate = parsedDate.toLocaleDateString('fr-FR');
                        }
                    } catch (e) {
                        formattedDate = '';
                    }

                    cell.classList.remove('red', 'orange', 'green', 'empty');
                    cell.classList.add(note || 'empty');
                    cell.innerHTML = `
                        <div class="note-color"></div>
                        <div class="note-date">${formattedDate}</div>
                    `;
                    cell.dataset.locked = "true";
                }
            });
        });
}

function loadRolesForCollaborator(userId) {
    fetch(`/competences/get_user_roles/${userId}`)
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('roles-sections-container');
            container.innerHTML = '';
            data.roles.forEach(role => {
                fetch(`/competences/role_structure/${userId}/${role.id}`)
                    .then(r => r.json())
                    .then(roleData => {
                        const template = document.getElementById('template-role-block').innerHTML;
                        const rendered = _.template(template)(roleData);
                        const wrapper = document.createElement('div');
                        wrapper.innerHTML = rendered;

                        wrapper.querySelectorAll('.toggle-role').forEach(header => {
                            header.addEventListener('click', () => {
                                const content = header.nextElementSibling;
                                content.classList.toggle('hidden');
                                const isOpen = !content.classList.contains('hidden');
                                header.innerHTML = (isOpen ? '▲ ' : '▼ ') + header.textContent.slice(2);
                            });
                        });

                        wrapper.querySelectorAll('.toggle-activity').forEach(header => {
                            header.addEventListener('click', () => {
                                const content = header.nextElementSibling;
                                content.classList.toggle('hidden');
                                const isOpen = !content.classList.contains('hidden');
                                header.innerHTML = (isOpen ? '▲ ' : '▼ ') + header.textContent.slice(2);
                            });
                        });

                        container.appendChild(wrapper);
                        loadExistingEvaluations(userId);
                    });
            });
        });
}

function saveAllEvaluations() {
    if (!selectedUserId) return alert("Aucun utilisateur sélectionné.");

    const evaluations = [];
    document.querySelectorAll('.eval-cell').forEach(cell => {
        const color = ['red', 'orange', 'green', 'empty'].find(c => cell.classList.contains(c)) || 'empty';
        if (cell.dataset.locked === "true") return;
        evaluations.push({
            user_id: parseInt(selectedUserId),
            activity_id: parseInt(cell.dataset.activity),
            item_id: cell.dataset.id ? parseInt(cell.dataset.id) : null,
            item_type: cell.dataset.type || null,
            eval_number: cell.dataset.eval,
            note: color
        });
    });

    if (evaluations.length === 0) return alert("Aucune évaluation à enregistrer.");

    fetch('/competences/save_user_evaluations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: selectedUserId, evaluations })
    })
    .then(r => r.json())
    .then(resp => {
        if (resp.success) {
            document.querySelectorAll('.eval-cell').forEach(cell => {
                if (!cell.dataset.locked && ['red', 'orange', 'green'].some(c => cell.classList.contains(c))) {
                    cell.dataset.locked = "true";
                }
            });
            alert("Évaluations enregistrées !");
            loadExistingEvaluations(selectedUserId);  // recharge activités
            loadGlobalSummary(); // recharge synthèse globale
        } else {
            alert("Erreur : " + resp.message);
        }
    });
}

document.addEventListener('click', e => {
    const cell = e.target.closest('.eval-cell');
    if (cell) {
        const isLocked = cell.dataset.locked === "true";
        const isEmpty = cell.classList.contains('empty');

        if (isLocked && !isEmpty) return;

        const colors = ['red', 'orange', 'green', 'empty'];
        const current = colors.find(c => cell.classList.contains(c)) || 'empty';
        const next = colors[(colors.indexOf(current) + 1) % colors.length];
        colors.forEach(c => cell.classList.remove(c));
        cell.classList.add(next);

        const date = new Date().toLocaleDateString('fr-FR');
        cell.innerHTML = `
            <div class="note-color"></div>
            <div class="note-date">${next !== 'empty' ? date : ''}</div>
        `;
    }
});

function toggleGlobalSynthesis() {
  const section = document.getElementById("global-summary-section");
  if (!section) return;

  const isVisible = !section.classList.contains("hidden");
  section.classList.toggle("hidden");

  const button = document.getElementById("toggle-summary");
  if (button) {
    button.textContent = isVisible ? "Afficher la synthèse globale" : "Masquer la synthèse globale";
  }

  if (!isVisible && section.innerHTML.trim() === "") {
    loadGlobalSummary();
  }
}

function loadGlobalSummary() {
  const section = document.getElementById("global-summary-section");
  if (!selectedUserId || !section) return;

  fetch(`/competences/global_flat_summary/${selectedUserId}`)
    .then(res => res.text())
    .then(html => {
      section.innerHTML = html;

      document.querySelectorAll('.eval-cell').forEach(cell => {
        const note = ['red', 'orange', 'green'].find(c => cell.classList.contains(c)) || 'empty';
        const rawDate = cell.dataset.date || '';
        let formattedDate = '';

        try {
          const parsed = new Date(rawDate);
          if (!isNaN(parsed)) {
            formattedDate = parsed.toLocaleDateString('fr-FR');
          } else {
            formattedDate = rawDate;
          }
        } catch (e) {
          formattedDate = '';
        }

        cell.classList.remove('red', 'orange', 'green', 'empty');
        cell.classList.add(note);
        cell.innerHTML = `
          <div class="note-color"></div>
          <div class="note-date">${note !== 'empty' ? formattedDate : ''}</div>
        `;

        if (note !== 'empty') {
          cell.dataset.locked = "true";
        }
      });
    })
    .catch(err => {
      console.error("Erreur chargement synthèse globale:", err);
      section.innerHTML = "<p>Erreur de chargement de la synthèse.</p>";
    });
}
