
// static/js/synth_competences.js

let selectedUserId = null;
let userStatus = 'user';

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const user = await getCurrentUserInfo();
        userStatus = user.status || 'user';
    } catch (err) {
        console.error("Impossible de récupérer l'utilisateur courant :", err);
    }

    getCurrentUserInfo().then(user => {
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
    });

    loadManagers();

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
});

async function getCurrentUserInfo() {
  const response = await fetch('/auth/current_user_info');
  return await response.json();
}

function loadManagers() {
    fetch('/competences/managers')
        .then(res => res.json())
        .then(managers => {
            const select = document.getElementById('manager-select');
            if (!select) return;
            select.innerHTML = '<option value="">Sélectionnez un manager</option>';
            managers.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.name;
                select.appendChild(opt);
            });
            select.addEventListener('change', () => {
                loadCollaborators(select.value);
            });
        });
}

function loadExistingEvaluations(userId) {
    fetch(`/competences/get_user_evaluations_by_user/${userId}`)
        .then(res => res.json())
        .then(data => {
            const evaluationsMap = {};
            data.forEach(e => {
                const key = `${e.activity_id}_${e.item_type || 'null'}_${e.item_id || 'null'}_${e.eval_number}`;
                evaluationsMap[key] = {
                    note: e.note,
                    date: e.created_at
                };
            });

            document.querySelectorAll('.eval-cell').forEach(cell => {
                const activityId = cell.dataset.activity;
                const itemId = cell.dataset.id || 'null';
                const itemType = cell.dataset.type || 'null';
                const evalNumber = cell.dataset.eval;

                const key = `${activityId}_${itemType}_${itemId}_${evalNumber}`;

                const entry = evaluationsMap[key];
                if (entry) {
                    const note = entry.note || 'empty';
                    const date = entry.date ? new Date(entry.date).toLocaleDateString('fr-FR') : '';

                    cell.classList.remove('red', 'orange', 'green', 'empty');
                    cell.classList.add(note);

                    cell.innerHTML = `
                        <div class="note-color"></div>
                        <div class="note-date">${date}</div>
                    `;

                    if (note !== 'empty' && userStatus !== 'administrateur') {
                        cell.dataset.locked = "true";
                    } else {
                        cell.removeAttribute('data-locked');
                    }
                }
            });
        })
        .catch(err => {
            console.error('Erreur chargement évaluations:', err);
        });
}

function loadCollaborators(managerId) {
    if (!managerId) {
        document.getElementById('collaborator-select').innerHTML = '<option value="">Sélectionnez un collaborateur</option>';
        document.getElementById('roles-sections-container').innerHTML = '';
        selectedUserId = null;
        return;
    }
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

            const toggleSummaryBtn = document.getElementById('toggle-summary');
            const summarySection = document.getElementById('global-summary-section');

            if (toggleSummaryBtn && summarySection) {
                toggleSummaryBtn.addEventListener('click', () => {
                    const isHidden = summarySection.classList.contains('hidden');
                    if (isHidden) {
                        loadGlobalSummary(userId);
                        summarySection.classList.remove('hidden');
                        toggleSummaryBtn.textContent = "Masquer la synthèse globale";
                    } else {
                        summarySection.classList.add('hidden');
                        toggleSummaryBtn.textContent = "Afficher la synthèse globale";
                    }
                });
            }
        });
}


function saveAllEvaluations() {
    if (!selectedUserId) {
        alert("Aucun utilisateur sélectionné.");
        return;
    }

    const evaluationsToSend = [];

    document.querySelectorAll('.eval-cell').forEach(cell => {
        const color = ['red', 'orange', 'green', 'empty'].find(c => cell.classList.contains(c)) || 'empty';
        const activityId = cell.dataset.activity;
        if (!activityId) return;

        evaluationsToSend.push({
            user_id: parseInt(selectedUserId),
            activity_id: parseInt(activityId),
            item_id: cell.dataset.id ? parseInt(cell.dataset.id) : null,
            item_type: cell.dataset.type || null,
            eval_number: cell.dataset.eval,
            note: color
        });
    });

    if (evaluationsToSend.length === 0) {
        alert("Aucune évaluation à enregistrer.");
        return;
    }

    fetch('/competences/save_user_evaluations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            userId: selectedUserId,
            evaluations: evaluationsToSend
        })
    })
    .then(res => res.json())
    .then(resp => {
        if (resp.success) {
            document.querySelectorAll('.eval-cell').forEach(cell => {
                if (userStatus !== 'administrateur') {
                    const color = ['red', 'orange', 'green'].find(c => cell.classList.contains(c));
                    if (color) {
                        cell.dataset.locked = "true";
                    }
                }
            });

            // Afficher message succès
            alert('Évaluations enregistrées avec succès !');
            refreshGlobalSummary(selectedUserId);
        } else {
            alert('Erreur : ' + resp.message);
        }
    })
    .catch(err => {
        console.error(err);
        alert('Erreur serveur.');
    });
}
);

            alert('Évaluations enregistrées avec succès !');
            refreshGlobalSummary(selectedUserId);
        } else {
            alert('Erreur : ' + resp.message);
        }
    })
    .catch(err => {
        console.error(err);
        alert('Erreur serveur.');
    });
}

function cycleEvalColor(cell) {
    if (cell.dataset.locked === "true" && userStatus !== 'administrateur') return;

    const colors = ['red', 'orange', 'green', 'empty'];
    let current = colors.find(c => cell.classList.contains(c)) || 'empty';
    let nextColor = colors[(colors.indexOf(current) + 1) % colors.length];

    colors.forEach(c => cell.classList.remove(c));
    cell.classList.add(nextColor);

    const dateStr = new Date().toLocaleDateString('fr-FR');
    cell.innerHTML = `
        <div class="note-color"></div>
        <div class="note-date">${nextColor !== 'empty' ? dateStr : ''}</div>
    `;
}

document.addEventListener('click', e => {
    if (e.target.classList.contains('eval-cell') &&
        !document.getElementById('global-summary-section')?.contains(e.target)) {
        cycleEvalColor(e.target);
    }
});

function refreshGlobalSummary(userId) {
    const summarySection = document.getElementById('global-summary-section');
    if (summarySection && !summarySection.classList.contains('hidden')) {
        loadGlobalSummary(userId);
    }
}
