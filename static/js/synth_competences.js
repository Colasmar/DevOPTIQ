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
                map[key] = { note: e.note, date: e.created_at }; // date ISO désormais
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

                // applique la couleur + date
                cell.classList.remove('red', 'orange', 'green', 'empty');
                cell.classList.add(note);
                cell.innerHTML = `
                    <div class="note-color"></div>
                    <div class="note-date">${note !== 'empty' ? formattedDate : ''}</div>
                `;

                // ⚑ mémorise l’état d’origine pour ne sauvegarder que les changements
                cell.dataset.original = note;
                cell.dataset.originalDate = (note !== 'empty') ? formattedDate : '';
            });

            // Sécurise les cellules qui n'avaient rien en BDD (aucune entrée dans map)
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

                        // Déplier/replier les rôles
                        wrapper.querySelectorAll('.toggle-role').forEach(header => {
                            header.addEventListener('click', () => {
                                const content = header.nextElementSibling;
                                content.classList.toggle('hidden');
                                const isOpen = !content.classList.contains('hidden');
                                header.innerHTML = (isOpen ? '▲ ' : '▼ ') + header.textContent.slice(2);
                            });
                        });

                        // Déplier/replier les activités
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

                        // Performances personnalisées
                        wrapper.querySelectorAll('.activity-section').forEach(section => {
                            const activityId = section.dataset.activityId;
                            const perfTarget = document.createElement('div');
                            perfTarget.classList.add('perf-container');
                            section.appendChild(perfTarget);
                            insertPerformanceBlock(activityId, perfTarget);
                        });
                    });
            });
        });
}

// ⛳ n'envoie QUE les cellules modifiées
function saveAllEvaluations() {
    if (!selectedUserId) return alert("Aucun utilisateur sélectionné.");

    const evaluations = [];

    document.querySelectorAll('.eval-cell').forEach(cell => {
        const colors = ['red', 'orange', 'green', 'empty'];
        const current = colors.find(c => cell.classList.contains(c)) || 'empty';
        const original = cell.dataset.original || 'empty';

        if (current === original) return; // pas de changement

        evaluations.push({
            user_id: parseInt(selectedUserId),
            activity_id: parseInt(cell.dataset.activity),
            item_id: cell.dataset.id ? parseInt(cell.dataset.id) : null,
            item_type: cell.dataset.type || null,
            eval_number: cell.dataset.eval,
            note: current // 'empty' => suppression, sinon upsert
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
        if (resp.success) {
            alert("Évaluations enregistrées !");
            // On recharge depuis la BDD : date = date d'enregistrement côté serveur
            loadExistingEvaluations(selectedUserId);
            loadGlobalSummary();
        } else {
            alert("Erreur : " + resp.message);
        }
    });
}

// Cycle couleur au clic (pas d’écriture de date ici : la date affichée finale vient du serveur)
document.addEventListener('click', e => {
    const cell = e.target.closest('.eval-cell');
    if (cell) {
        const colors = ['red', 'orange', 'green', 'empty'];
        const current = colors.find(c => cell.classList.contains(c)) || 'empty';
        const next = colors[(colors.indexOf(current) + 1) % colors.length];
        colors.forEach(c => cell.classList.remove(c));
        cell.classList.add(next);

        // On laisse la date visuelle vide tant que ce n'est pas enregistré,
        // pour éviter toute confusion : la "vraie" date viendra du backend.
        cell.innerHTML = `
            <div class="note-color"></div>
            <div class="note-date">${''}</div>
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

      // Restyle (couleur + date), pas de verrouillage
      document.querySelectorAll('.eval-cell').forEach(cell => {
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

// Util : formatte ISO/texte en 'fr-FR'
function formatDateForFR(raw) {
  if (!raw) return '';
  try {
    // Privilégie l'ISO (backend renvoie isoformat)
    const d = new Date(raw);
    if (!isNaN(d)) return d.toLocaleDateString('fr-FR');
  } catch (e) {}
  // fallback si c'était déjà une chaîne lisible
  return typeof raw === 'string' ? raw : '';
}
