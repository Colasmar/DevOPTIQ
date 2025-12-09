// Code/static/js/synth_competences.js
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
              .then(() => {
                document.getElementById('manager-name').textContent = `${user.manager_first_name} ${user.manager_last_name}`;
                loadCollaborators(user.manager_id);
              });
        }

        const saveButton = document.getElementById('save-competencies-button');
        if (saveButton) saveButton.addEventListener('click', saveAllEvaluations);

        const collaboratorSelect = document.getElementById("collaborator-select");
        if (collaboratorSelect) {
            collaboratorSelect.addEventListener("change", function () {
                selectedUserId = this.value;
                // expose global
                globalThis.selectedUserId = Number(selectedUserId);
                if (selectedUserId) loadRolesForCollaborator(selectedUserId);
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

// API util
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

                let note = 'empty';
                let formattedDate = '';

                if (evalData) {
                    note = evalData.note || 'empty';
                    const rawDate = evalData.date;
                    formattedDate = formatDateForFR(rawDate);
                }

                cell.classList.remove('red', 'orange', 'green', 'empty');
                cell.classList.add(note);
                cell.innerHTML = `
                    <div class="note-color"></div>
                    <div class="note-date">${note !== 'empty' ? formattedDate : ''}</div>
                `;

                cell.dataset.original = note;
                cell.dataset.originalDate = (note !== 'empty') ? formattedDate : '';
            });

            document.querySelectorAll('.eval-cell').forEach(cell => {
                if (!cell.dataset.original) {
                    const note = ['red','orange','green'].find(c => cell.classList.contains(c)) || 'empty';
                    const dateTxt = cell.querySelector('.note-date')?.textContent?.trim() || '';
                    cell.dataset.original = note;
                    cell.dataset.originalDate = (note !== 'empty') ? dateTxt : '';
                }
            });
        });
}

function loadRolesForCollaborator(userId) {
    globalThis.selectedUserId = Number(userId);

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

                        // Toggle rôles
                        wrapper.querySelectorAll('.toggle-role').forEach(header => {
                            header.addEventListener('click', () => {
                                const content = header.nextElementSibling;
                                content.classList.toggle('hidden');
                                const isOpen = !content.classList.contains('hidden');
                                header.innerHTML = (isOpen ? '▲ ' : '▼ ') + header.textContent.slice(2);
                            });
                        });

                        // Toggle activités
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

                        // 🔹 Performances tout en haut de .activity-content
                        wrapper.querySelectorAll('.activity-section').forEach(section => {
                            const activityId = Number(section.dataset.activityId);
                            const contentDiv = section.querySelector('.activity-content');
                            if (!contentDiv) return;

                            const perfTarget = document.createElement('div');
                            perfTarget.classList.add('perf-container');
                            perfTarget.style.marginBottom = '12px';
                            // 👉 insérer en tête
                            contentDiv.insertBefore(perfTarget, contentDiv.firstChild);

                            insertPerformanceBlock(activityId, perfTarget);
                        });
                    });
            });
        });
}

// Sauvegarde
function saveAllEvaluations() {
    if (!selectedUserId) return alert("Aucun utilisateur sélectionné.");

    const evaluations = [];
    document.querySelectorAll('.eval-cell').forEach(cell => {
        const colors = ['red', 'orange', 'green', 'empty'];
        const current = colors.find(c => cell.classList.contains(c)) || 'empty';
        const original = cell.dataset.original || 'empty';
        if (current === original) return;

        evaluations.push({
            user_id: parseInt(selectedUserId),
            activity_id: parseInt(cell.dataset.activity),
            item_id: cell.dataset.id ? parseInt(cell.dataset.id) : null,
            item_type: cell.dataset.type || null,
            eval_number: cell.dataset.eval,
            note: current
        });
    });

    if (evaluations.length === 0) return alert("Aucune modification à enregistrer.");

    fetch('/competences/save_user_evaluations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: selectedUserId, evaluations })
    })
    .then(r => r.json())
    .then(resp => {
        if (!resp.success) {
            alert("Erreur : " + (resp.message || ''));
            return;
        }
        if (Array.isArray(resp.evaluations)) applyUpdatedDatesFromBackend(resp.evaluations);
        clearDatesForEmptiedCells(evaluations, resp.evaluations || []);
        refreshOriginalStateForChangedCells(evaluations);

        const section = document.getElementById("global-summary-section");
        if (section && !section.classList.contains("hidden")) loadGlobalSummary();

        alert("Évaluations enregistrées !");
    })
    .catch(err => {
        console.error(err);
        alert("Erreur réseau lors de l’enregistrement.");
    });
}

// Clic cycle
document.addEventListener('click', e => {
    const cell = e.target.closest('.eval-cell');
    if (!cell) return;
    const colors = ['red', 'orange', 'green', 'empty'];
    const current = colors.find(c => cell.classList.contains(c)) || 'empty';
    const next = colors[(colors.indexOf(current) + 1) % colors.length];
    colors.forEach(c => cell.classList.remove(c));
    cell.classList.add(next);
    cell.classList.add('pending-change'); // on garde la date affichée jusqu'à la réponse serveur
});

// Dates backend -> UI
function applyUpdatedDatesFromBackend(updated) {
    updated.forEach(u => {
        const baseSelector = `.eval-cell[data-activity="${u.activity_id}"][data-type="${u.item_type || ''}"][data-eval="${u.eval_number}"]`;
        const candidates = document.querySelectorAll(baseSelector);
        let target = null;
        candidates.forEach(c => {
            const cid = c.dataset.id ? parseInt(c.dataset.id) : null;
            if ((u.item_id == null && (c.dataset.id === undefined || c.dataset.id === '' || c.dataset.id === null))
                || (u.item_id != null && cid === parseInt(u.item_id))) {
                target = c;
            }
        });
        if (!target) return;

        ['red','orange','green','empty'].forEach(cl => target.classList.remove(cl));
        target.classList.add(u.note || 'empty');

        const dateText = formatDateForFR(u.created_at);
        let dateEl = target.querySelector('.note-date');
        if (!dateEl) {
            const container = document.createElement('div');
            container.className = 'note-date';
            target.appendChild(container);
            dateEl = container;
        }
        dateEl.textContent = (u.note && u.note !== 'empty') ? dateText : '';
        target.classList.remove('pending-change');
    });
}

function clearDatesForEmptiedCells(requestEvals, backendEvals) {
    const backendKeys = new Set(
        backendEvals.map(u => `${u.activity_id}_${u.item_type || 'null'}_${u.item_id ?? 'null'}_${u.eval_number}`)
    );
    requestEvals.forEach(r => {
        const isEmpty = r.note === 'empty';
        const key = `${r.activity_id}_${r.item_type || 'null'}_${r.item_id ?? 'null'}_${r.eval_number}`;
        if (isEmpty && !backendKeys.has(key)) {
            const baseSelector = `.eval-cell[data-activity="${r.activity_id}"][data-type="${r.item_type || ''}"][data-eval="${r.eval_number}"]`;
            const candidates = document.querySelectorAll(baseSelector);
            candidates.forEach(c => {
                const cid = c.dataset.id ? parseInt(c.dataset.id) : null;
                const match =
                    (r.item_id == null && (c.dataset.id === undefined || c.dataset.id === '' || c.dataset.id === null))
                    || (r.item_id != null && cid === parseInt(r.item_id));
                if (match) {
                    const dateEl = c.querySelector('.note-date');
                    if (dateEl) dateEl.textContent = '';
                    c.classList.remove('pending-change');
                }
            });
        }
    });
}

function refreshOriginalStateForChangedCells(requestEvals) {
    requestEvals.forEach(r => {
        const baseSelector = `.eval-cell[data-activity="${r.activity_id}"][data-type="${r.item_type || ''}"][data-eval="${r.eval_number}"]`;
        const candidates = document.querySelectorAll(baseSelector);
        candidates.forEach(c => {
            const cid = c.dataset.id ? parseInt(c.dataset.id) : null;
            const match =
                (r.item_id == null && (c.dataset.id === undefined || c.dataset.id === '' || c.dataset.id === null))
                || (r.item_id != null && cid === parseInt(r.item_id));
            if (!match) return;

            const colors = ['red','orange','green','empty'];
            const current = colors.find(x => c.classList.contains(x)) || 'empty';
            c.dataset.original = current;

            const dateTxt = c.querySelector('.note-date')?.textContent?.trim() || '';
            c.dataset.originalDate = (current !== 'empty') ? dateTxt : '';
        });
    });
}

// Synthèse globale
function toggleGlobalSynthesis() {
  const section = document.getElementById("global-summary-section");
  if (!section) return;
  const isVisible = !section.classList.contains("hidden");
  section.classList.toggle("hidden");
  const button = document.getElementById("toggle-summary");
  if (button) button.textContent = isVisible ? "Afficher la synthèse globale" : "Masquer la synthèse globale";
  if (!isVisible && section.innerHTML.trim() === "") loadGlobalSummary();
}

function loadGlobalSummary() {
  const section = document.getElementById("global-summary-section");
  if (!selectedUserId || !section) return;
  fetch(`/competences/global_flat_summary/${selectedUserId}`)
    .then(res => res.text())
    .then(html => {
      section.innerHTML = html;
      section.querySelectorAll('.eval-cell').forEach(cell => {
        const note = ['red', 'orange', 'green'].find(c => cell.classList.contains(c)) || 'empty';
        const rawDate = cell.dataset.date || '';
        const formattedDate = formatDateForFR(rawDate);
        cell.classList.remove('red', 'orange', 'green', 'empty');
        cell.classList.add(note);
        cell.innerHTML = `
          <div class="note-color"></div>
          <div class="note-date">${note !== 'empty' ? formattedDate : ''}</div>
        `;
      });
    })
    .catch(err => {
      console.error("Erreur chargement synthèse globale:", err);
      section.innerHTML = "<p>Erreur de chargement de la synthèse.</p>";
    });
}

// Util
function formatDateForFR(raw) {
  if (!raw) return '';
  try { const d = new Date(raw); if (!isNaN(d)) return d.toLocaleDateString('fr-FR'); } catch (e) {}
  return typeof raw === 'string' ? raw : '';
}
