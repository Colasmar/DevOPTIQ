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
                    const date = new Date(evalData.date).toLocaleDateString('fr-FR');
                    cell.classList.remove('red', 'orange', 'green', 'empty');
                    cell.classList.add(note);
                    cell.innerHTML = `
                        <div class="note-color"></div>
                        <div class="note-date">${date}</div>
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
            loadExistingEvaluations(selectedUserId);
        } else {
            alert("Erreur : " + resp.message);
        }
    });
}

document.addEventListener('click', e => {
    if (e.target.classList.contains('eval-cell')) {
        if (e.target.dataset.locked === "true") return;
        const colors = ['red', 'orange', 'green', 'empty'];
        const current = colors.find(c => e.target.classList.contains(c)) || 'empty';
        const next = colors[(colors.indexOf(current) + 1) % colors.length];
        colors.forEach(c => e.target.classList.remove(c));
        e.target.classList.add(next);
        const date = new Date().toLocaleDateString('fr-FR');
        e.target.innerHTML = `
            <div class="note-color"></div>
            <div class="note-date">${next !== 'empty' ? date : ''}</div>
        `;
    }
});
