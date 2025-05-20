// static/js/synth_competences.js

let selectedUserId = null;

document.addEventListener("DOMContentLoaded", () => {
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
});

function loadManagers() {
    fetch('/competences/managers')
        .then(res => res.json())
        .then(managers => {
            const select = document.getElementById('manager-select');
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

                if (evaluationsMap[key]) {
                    cell.classList.remove('red', 'orange', 'green');
                    cell.classList.add(evaluationsMap[key].note);
                    if (evaluationsMap[key].date) {
                        cell.dataset.date = evaluationsMap[key].date;
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

            // Charger et afficher la synthèse globale
            // Charger et afficher la synthèse globale
            const toggleSummaryBtn = document.getElementById('toggle-summary');
            const summarySection = document.getElementById('global-summary-section');

            if (toggleSummaryBtn && summarySection) {
                toggleSummaryBtn.addEventListener('click', () => {
                    const isHidden = summarySection.classList.contains('hidden');
                    if (isHidden) {
                        loadGlobalSummary(userId);  // charge et affiche le contenu
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

function loadGlobalSummary(userId) {
    fetch(`/competences/global_flat_summary/${userId}`)
        .then(res => res.text())
        .then(html => {
            const section = document.getElementById('global-summary-section');
            section.innerHTML = html;

            const detailBtn = document.getElementById('toggle-detail');
            const rows = document.querySelectorAll('.details-row');

            if (detailBtn) {
                detailBtn.addEventListener('click', () => {
                    const isHidden = rows[0]?.style.display === 'none';
                    rows.forEach(r => r.style.display = isHidden ? '' : 'none');
                    detailBtn.textContent = isHidden ? 'Masquer les détails' : 'Afficher les détails';
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
        const color = ['red', 'orange', 'green'].find(c => cell.classList.contains(c));
        const activityId = cell.dataset.activity;
        if (!color || !activityId) return;

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
            alert('Évaluations enregistrées avec succès !');

            // Si la synthèse globale est visible, la recharger dynamiquement
            const summarySection = document.getElementById('global-summary-section');
            const isVisible = summarySection && !summarySection.classList.contains('hidden');

            if (isVisible) {
                loadGlobalSummary(selectedUserId);
            }

        } else {
            alert('Erreur : ' + resp.message);
        }
    })
    .catch(err => {
        console.error(err);
        alert('Erreur serveur.');
    });
}



function saveAllEvaluations() {
    if (!selectedUserId) {
        alert("Aucun utilisateur sélectionné.");
        return;
    }

    const evaluationsToSend = [];

    document.querySelectorAll('.eval-cell').forEach(cell => {
        const color = ['red', 'orange', 'green'].find(c => cell.classList.contains(c));
        if (!color) return;

        evaluationsToSend.push({
            user_id: parseInt(selectedUserId),
            activity_id: parseInt(cell.dataset.activity),
            item_id: cell.dataset.id ? parseInt(cell.dataset.id) : null,
            item_type: cell.dataset.type || null,
            eval_number: cell.dataset.eval,
            note: color
        });
    });

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
    const colors = ['red', 'orange', 'green'];
    let current = colors.find(c => cell.classList.contains(c));
    let nextColor;

    if (!current) {
        nextColor = 'red';
    } else {
        const idx = colors.indexOf(current);
        nextColor = current === 'green' ? null : colors[(idx + 1) % colors.length];
        cell.classList.remove(current);
    }

    cell.classList.remove('red', 'orange', 'green');
    if (nextColor) {
        cell.classList.add(nextColor);
    }
}

document.addEventListener('click', e => {
    if (e.target.classList.contains('eval-cell') &&
        !document.getElementById('global-summary-section')?.contains(e.target)) {
        cycleEvalColor(e.target);
    }
});


let tooltipTimeout;
let tooltipActive = false;

document.addEventListener('mouseover', (e) => {
    const target = e.target;
    if (target.classList.contains('eval-cell') && target.dataset.date) {
        tooltipTimeout = setTimeout(() => {
            if (tooltipActive) return;
            tooltipActive = true;

            const tooltip = document.createElement('div');
            tooltip.id = 'tooltip-popup';
            tooltip.textContent = `Saisie le : ${new Date(target.dataset.date).toLocaleString('fr-FR')}`;
            tooltip.style.position = 'absolute';
            tooltip.style.background = '#f9f9f9';
            tooltip.style.border = '1px solid #ccc';
            tooltip.style.padding = '8px';
            tooltip.style.borderRadius = '6px';
            tooltip.style.fontSize = '13px';
            tooltip.style.zIndex = 9999;
            tooltip.style.maxWidth = '220px';
            tooltip.style.whiteSpace = 'normal';
            tooltip.style.boxShadow = '0 2px 6px rgba(0,0,0,0.15)';
            tooltip.style.top = `${e.pageY + 12}px`;
            tooltip.style.left = `${e.pageX + 12}px`;
            document.body.appendChild(tooltip);
        }, 1500);
    }
});

document.addEventListener('mouseout', (e) => {
    if (e.target.classList.contains('eval-cell')) {
        clearTimeout(tooltipTimeout);
        const popup = document.getElementById('tooltip-popup');
        if (popup) popup.remove();
        tooltipActive = false;
    }
});

document.addEventListener('mousedown', (e) => {
    if (e.target.classList.contains('eval-cell')) {
        clearTimeout(tooltipTimeout);
        const popup = document.getElementById('tooltip-popup');
        if (popup) popup.remove();
        tooltipActive = false;
    }
});

function refreshGlobalSummary(userId) {
    const summarySection = document.getElementById('global-summary-section');
    if (summarySection && !summarySection.classList.contains('hidden')) {
        loadGlobalSummary(userId); 
    }
}
