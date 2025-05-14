// static/js/synth_competences.js

document.addEventListener('DOMContentLoaded', () => {
    loadRoles();
    loadManagers();

    const saveButton = document.getElementById('save-competencies-button');
    if (saveButton) {
        saveButton.addEventListener('click', saveAllEvaluations);
    } else {
        console.error("Le bouton avec l'ID 'save-competencies-button' n'a pas été trouvé.");
    }

    // Événement changement de rôle (pour charger la nouvelle section aussi)
    document.getElementById('user-roles').addEventListener('change', () => {
        const roleId = document.getElementById('user-roles').value;
        if (roleId) {
            loadRoleCompetencies(roleId); // Charge les compétences avec connexions
            loadRoleKnowledge(roleId);    // Charge les savoirs, savoir-faire, et HSC avec évaluations passées <-- MODIFIÉ
            loadCompetencySynthesis(roleId); // NOUVEAU: Charge les compétences pour la synthèse
        } else {
            document.getElementById('roles-competencies').innerHTML = '';
            document.getElementById('knowledge-evolution').innerHTML = '';
            document.getElementById('competency-synthesis').innerHTML = ''; // Vider la nouvelle section
        }
    });
});

let selectedUserId = null;

// Charger la liste des rôles
function loadRoles() {
    fetch('/competences/roles')
        .then(res => res.json())
        .then(roles => {
            const select = document.getElementById('role-to-assign');
            select.innerHTML = '';
            roles.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r.id;
                opt.textContent = r.name;
                select.appendChild(opt);
            });
        });
}

// Charger la liste des managers
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

// Charger les collaborateurs
function loadCollaborators(managerId) {
    if (!managerId) {
        document.getElementById('collaborator-select').innerHTML = '<option value="">Sélectionnez un collaborateur</option>';
        document.getElementById('user-roles').innerHTML = '<option value="">-- Aucun rôle --</option>';
        // Vider les sections d'évaluation si aucun collaborateur sélectionné
        document.getElementById('roles-competencies').innerHTML = '';
        document.getElementById('knowledge-evolution').innerHTML = '';
        document.getElementById('competency-synthesis').innerHTML = '';
        selectedUserId = null; // Réinitialiser l'ID de l'utilisateur sélectionné
        return;
    }
    fetch(`/competences/collaborators/${managerId}`)
        .then(res => res.json())
        .then(collabs => {
            const select = document.getElementById('collaborator-select');
            select.innerHTML = '<option value="">Sélectionnez un collaborateur</option>';
            collabs.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id; // L'ID du collaborateur
                opt.textContent = `${c.first_name} ${c.last_name}`;
                select.appendChild(opt);
            });

            // Écouteur pour le changement de collaborateur
            select.removeEventListener('change', handleCollaboratorChange); // Supprimer l'ancien écouteur
            select.addEventListener('change', handleCollaboratorChange); // Ajouter le nouvel écouteur

            // Charger les rôles pour le premier collaborateur si la liste n'est pas vide
            if (collabs.length > 0) {
                 // Charger les rôles pour le premier collaborateur par défaut
                 // selectedUserId = collabs[0].id; // Définir l'ID du premier collaborateur
                 // loadUserRoles(selectedUserId);
                 // Ne pas charger automatiquement, attendre que l'utilisateur sélectionne
            } else {
                document.getElementById('user-roles').innerHTML = '<option value="">-- Aucun rôle assigné --</option>';
                // Vider les sections d'évaluation si aucun collaborateur
                document.getElementById('roles-competencies').innerHTML = '';
                document.getElementById('knowledge-evolution').innerHTML = '';
                document.getElementById('competency-synthesis').innerHTML = '';
                selectedUserId = null;
            }
        });
}

// Nouvelle fonction pour gérer le changement de collaborateur sélectionné
function handleCollaboratorChange() {
    selectedUserId = this.value; // Attribuer l'ID du collaborateur sélectionné
    const userRolesSelect = document.getElementById('user-roles');
    if (selectedUserId) {
        loadUserRoles(selectedUserId); // Charger les rôles du nouvel utilisateur sélectionné
    } else {
        // Si l'utilisateur sélectionné est "Sélectionnez un collaborateur"
        userRolesSelect.innerHTML = '<option value="">-- Aucun rôle --</option>';
        document.getElementById('roles-competencies').innerHTML = '';
        document.getElementById('knowledge-evolution').innerHTML = '';
        document.getElementById('competency-synthesis').innerHTML = '';
    }
}


// Charger et afficher les rôles du collaborateur
function loadUserRoles(userId) {
    if (!userId) {
        document.getElementById('user-roles').innerHTML = '<option value="">-- Aucun rôle --</option>';
         // Vider les sections d'évaluation
        document.getElementById('roles-competencies').innerHTML = '';
        document.getElementById('knowledge-evolution').innerHTML = '';
        document.getElementById('competency-synthesis').innerHTML = '';
        return;
    }
    fetch(`/competences/get_user_roles/${userId}`)
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('user-roles');
            select.innerHTML = '';
            if (data.roles && data.roles.length > 0) {
                data.roles.forEach(role => {
                    const opt = document.createElement('option');
                    opt.value = role.id;
                    opt.textContent = role.name;
                    select.appendChild(opt);
                });
                // Charger les informations pour le premier rôle par défaut
                const firstRoleId = data.roles[0].id;
                loadRoleCompetencies(firstRoleId);
                loadRoleKnowledge(firstRoleId);
                loadCompetencySynthesis(firstRoleId); // NOUVEAU: Charger la synthèse pour le premier rôle
            } else {
                select.innerHTML = '<option value="">-- Aucun rôle assigné --</option>';
                // Vider les sections d'évaluation si aucun rôle
                document.getElementById('roles-competencies').innerHTML = '';
                document.getElementById('knowledge-evolution').innerHTML = '';
                document.getElementById('competency-synthesis').innerHTML = '';
            }
        });
}

// Charger les compétences d’un rôle (pour affichage avec connexions)
function loadRoleCompetencies(roleId) {
    if (!roleId) {
        document.getElementById('roles-competencies').innerHTML = '';
        return;
    }
    fetch(`/competences/get_role_competencies/${roleId}`)
        .then(res => res.json())
        .then(data => {
            let container = document.getElementById('roles-competencies');
             if (!container) {
                // Créer le conteneur s'il n'existe pas (moins probable maintenant avec le HTML statique)
                const main = document.querySelector('main');
                const section = document.createElement('div');
                section.id = 'roles-competencies';
                main.appendChild(section);
                container = section;
            }
            container.innerHTML = '<h3>Compétences du rôle</h3>'; // Vider et ajouter le titre

            if (data.competencies && data.competencies.length > 0) {
                data.competencies.forEach(comp => {
                    const compDiv = document.createElement('div');
                    compDiv.className = 'competency';
                    compDiv.dataset.competencyId = comp.id;
                    compDiv.style.cursor = 'pointer';
                    compDiv.innerHTML = `<strong>${comp.name}</strong>`;
                    compDiv.addEventListener('click', () => {
                        showConnections(comp.id, compDiv);
                    });

                    const connectionsDiv = document.createElement('div');
                    connectionsDiv.className = 'connections-outgoing';
                    connectionsDiv.style.display = 'none';
                    compDiv.appendChild(connectionsDiv);

                    container.appendChild(compDiv);
                });
            } else {
                container.innerHTML += '<p>Aucune compétence pour ce rôle.</p>';
            }
        });
}

// Charger les savoirs, savoir-faire, et HSC (pour l'évolution)
function loadRoleKnowledge(roleId) {
    const userId = selectedUserId; // Utiliser l'ID de l'utilisateur sélectionné
    if (!roleId || !userId) {
        document.getElementById('knowledge-evolution').innerHTML = '';
        return;
    }

    const container = document.getElementById('knowledge-evolution');
    container.innerHTML = ''; // Vider le conteneur avant de charger
    container.innerHTML = '<h3>Évolution des savoirs, savoir-faire et HSC</h3>'; // Ajouter le titre <-- MODIFIÉ

    // Charger la structure des connaissances (savoirs, savoir-faire, HSC)
    fetch(`/competences/get_role_knowledge/${roleId}`)
        .then(res => res.json())
        .then(data => {
            const sections = [
                { title: 'Savoirs', key: 'savoirs' },
                { title: 'Savoir-Faire', key: 'savoir_faires' },
                { title: 'HSC', key: 'softskills' } // Changez 'Aptitudes' en 'HSC' et la clé en 'softskills'
            ];

            sections.forEach(section => {
                const sectionData = data[section.key];

                const table = document.createElement('table');
                table.className = 'knowledge-table'; // Classe spécifique pour ce tableau

                const header = document.createElement('tr');
                header.innerHTML = `
                    <th>${section.title}</th>
                    <th>Évaluation 1</th>
                    <th>Évaluation 2</th>
                    <th>Évaluation 3</th>
                `;
                table.appendChild(header);

                if (sectionData && sectionData.length > 0) {
                    sectionData.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>
                                ${item.description}
                                ${section.key === 'softskills' && item.niveau ? ' - Niveau: ' + item.niveau : ''}
                            </td>
                            <td class="eval-cell" data-id="${item.id}" data-type="${section.key}" data-eval="1"></td>
                            <td class="eval-cell" data-id="${item.id}" data-type="${section.key}" data-eval="2"></td>
                            <td class="eval-cell" data-id="${item.id}" data-type="${section.key}" data-eval="3"></td>
                            `;
                        table.appendChild(row);
                    });
                } else {
                     const row = document.createElement('tr');
                     // Mettez à jour le message en fonction du nouveau titre
                     row.innerHTML = `<td colspan="4">Aucun ${section.title.toLowerCase()} défini pour ce rôle/cette activité.</td>`;
                     table.appendChild(row);
                }


                container.appendChild(table);
            });

            // Une fois que la structure est chargée et affichée, charger les évaluations existantes
            loadExistingKnowledgeEvaluations(userId, roleId);

        })
        .catch(error => {
            console.error('Erreur lors du chargement des connaissances du rôle:', error);
            container.innerHTML += '<p>Erreur lors du chargement des connaissances.</p>';
        });
}

// Nouvelle fonction pour charger et appliquer les évaluations existantes pour Savoirs/Savoir-faire/HSC
function loadExistingKnowledgeEvaluations(userId, roleId) {
     fetch(`/competences/get_user_evaluations/${userId}/${roleId}`)
        .then(res => res.json())
        .then(existingEvaluations => {
            const evaluationsMap = {};
            existingEvaluations.forEach(eval => {
                // La clé doit identifier l'élément évalué ET le numéro d'évaluation.
                // Le item_type peut être 'savoirs', 'savoir_faires', ou 'softskills' maintenant.
                 const key = `${eval.item_id}_${eval.item_type}_${eval.eval_number}`;
                 evaluationsMap[key] = {
                    note: eval.note,
                    date: eval.created_at
                };
            });

            // Appliquer les évaluations existantes aux cellules du tableau Knowledge (évolution)
            const evalCells = document.querySelectorAll('#knowledge-evolution .eval-cell');
            evalCells.forEach(cell => {
                 const itemId = cell.dataset.id;
                 const itemType = cell.dataset.type; // 'savoirs', 'savoir_faires', ou 'softskills'
                 const evalNumber = cell.dataset.eval;
                 const key = `${itemId}_${itemType}_${evalNumber}`;

                 if (evaluationsMap[key]) {
                    cell.classList.remove('red', 'orange', 'green'); // Nettoyer les classes existantes
                    cell.classList.add(evaluationsMap[key].note);
                    cell.dataset.date = evaluationsMap[key].date;
                    // Appliquer la classe enregistrée
                 } else {
                     // Si pas d'évaluation existante, s'assurer qu'il n'y a pas de couleur
                     cell.classList.remove('red', 'orange', 'green');
                 }
            });
        })
        .catch(error => {
            console.warn('Aucune évaluation existante trouvée ou erreur lors du chargement des évaluations existantes pour Knowledge:', error);
            // C'est une erreur moins critique, on peut simplement ne pas appliquer de couleurs
        });
}


// NOUVELLE FONCTION : Charger et afficher la synthèse des compétences
function loadCompetencySynthesis(roleId) {
    const userId = selectedUserId; // Utiliser l'ID de l'utilisateur sélectionné
    if (!roleId || !userId) {
        document.getElementById('competency-synthesis').innerHTML = '';
        return;
    }

    const container = document.getElementById('competency-synthesis');
    container.innerHTML = ''; // Vider le conteneur avant de charger
    container.innerHTML = '<h3>Synthèse des Compétences</h3>'; // Ajouter le titre

    // Récupérer la liste des compétences pour ce rôle (comme dans loadRoleCompetencies, mais sans les connexions)
    fetch(`/competences/get_role_competencies/${roleId}`)
        .then(res => res.json())
        .then(data => {
            const competencies = data.competencies;

            const table = document.createElement('table');
            table.className = 'synthesis-table'; // Classe spécifique pour ce tableau

            const header = document.createElement('tr');
            header.innerHTML = `
                <th>Compétence</th>
                <th>Statut Collaborateur</th>
                <th>Statut Manager</th>
                <th>Validation RH</th>
            `;
            table.appendChild(header);

            if (competencies && competencies.length > 0) {
                competencies.forEach(comp => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${comp.name}</td>
                        <td class="eval-cell synthesis-eval" data-id="${comp.id}" data-type="competencies" data-eval="collaborator"></td>
                        <td class="eval-cell synthesis-eval" data-id="${comp.id}" data-type="competencies" data-eval="manager"></td>
                        <td class="eval-cell synthesis-eval" data-id="${comp.id}" data-type="competencies" data-eval="rh"></td>
                    `;
                    table.appendChild(row);
                });
            } else {
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="4">Aucune compétence définie pour ce rôle.</td>`;
                table.appendChild(row);
            }

            container.appendChild(table);

            // Charger les évaluations existantes pour cette synthèse
            loadExistingSynthesisEvaluations(userId, roleId);

        })
        .catch(error => {
            console.error('Erreur lors du chargement des compétences pour la synthèse:', error);
            container.innerHTML += '<p>Erreur lors du chargement de la synthèse des compétences.</p>';
        });
}

// Nouvelle fonction pour charger et appliquer les évaluations existantes pour la synthèse des compétences
function loadExistingSynthesisEvaluations(userId, roleId) {
    // Utilise la même route backend mais filtre les résultats côté frontend
    fetch(`/competences/get_user_evaluations/${userId}/${roleId}`)
        .then(res => res.json())
        .then(existingEvaluations => {
            const evaluationsMap = {};
             // On ne prend que les évaluations dont le type est 'competencies'
            existingEvaluations.filter(eval => eval.item_type === 'competencies').forEach(eval => {
                // La clé doit identifier l'élément évalué ET le type d'évaluateur (représenté par eval_number)
                 const key = `${eval.item_id}_${eval.eval_number}`; // item_type est implicite 'competencies'
                 evaluationsMap[key] = {
                    note: eval.note,
                    date: eval.created_at
                };
            });

            // Appliquer les évaluations existantes aux cellules du tableau Synthèse
            const evalCells = document.querySelectorAll('#competency-synthesis .eval-cell');
            evalCells.forEach(cell => {
                 const itemId = cell.dataset.id;
                 const evalType = cell.dataset.eval; // 'collaborator', 'manager', 'rh'
                 const key = `${itemId}_${evalType}`;

                 if (evaluationsMap[key]) {
                    cell.classList.remove('red', 'orange', 'green'); // Nettoyer les classes existantes
                    cell.classList.add(evaluationsMap[key].note);
                    cell.dataset.date = evaluationsMap[key].date; // Appliquer la classe enregistrée
                 } else {
                     // Si pas d'évaluation existante, s'assurer qu'il n'y a pas de couleur
                     cell.classList.remove('red', 'orange', 'green');
                 }
            });
        })
        .catch(error => {
            console.warn('Aucune évaluation existante trouvée ou erreur lors du chargement des évaluations existantes pour la synthèse:', error);
            // C'est une erreur moins critique
        });
}


// Modal pour ajouter un collaborateur
function openAddCollaboratorModal() {
    fetch('/competences/all_users')
        .then(res => res.json())
        .then(users => {
            const select = document.getElementById('user-to-add');
            select.innerHTML = '';
            users.forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.id;
                opt.textContent = u.name;
                select.appendChild(opt);
            });
            document.getElementById('add-collaborator-modal').style.display = 'block';
        });
}

// Enregistrement collaborateur
function saveNewCollaborator() {
    const managerSelect = document.getElementById('manager-select');
    const managerId = managerSelect.value;
    const userId = document.getElementById('user-to-add').value;
    const roleId = document.getElementById('role-to-assign').value;

    if (!managerId || !userId || !roleId) {
        alert('Remplissez tous les champs.');
        return;
    }

    fetch('/competences/add_collaborator', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: parseInt(userId), manager_id: parseInt(managerId), role_id: parseInt(roleId) })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Assigner le rôle à l'utilisateur
            assignRoleToUser(userId, roleId).then(() => {
                 alert('Collaborateur et rôle ajoutés avec succès !');
                 document.getElementById('add-collaborator-modal').style.display = 'none';
                 // Recharger la liste des collaborateurs pour le manager actuel
                 loadCollaborators(managerId);
                 // Optionnel: Sélectionner le nouvel utilisateur ajouté après le rechargement
                 // Cela pourrait nécessiter de trouver l'option par ID et de déclencher l'événement change
            });
        } else {
            alert('Erreur : ' + data.message);
        }
    })
     .catch((error) => {
        console.error('Erreur lors de l\'ajout du collaborateur:', error);
        alert('Erreur lors de l\'ajout du collaborateur.');
    });
}

function assignRoleToUser(userId, roleId) {
    return fetch('/competences/add_role_to_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: parseInt(userId), role_id: parseInt(roleId) })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            console.error('Erreur lors de l\'ajout du rôle :', data.message);
            // Gérer l'erreur d'ajout de rôle si nécessaire, mais ne bloque pas l'ajout du collaborateur
        }
        return data; // Permet de chaîner les promesses
    })
     .catch((error) => {
        console.error('Erreur de connexion lors de l\'ajout du rôle:', error);
        // Gérer l'erreur de connexion si nécessaire
     });
}


function showConnections(compId, compDiv) {
    const connectionsDiv = compDiv.querySelector('.connections-outgoing');
    if (connectionsDiv.style.display === 'block') {
        connectionsDiv.style.display = 'none';
        return;
    }

    fetch(`/competences/get_competency_connections/${compId}`)
        .then(res => res.json())
        .then(data => {
            connectionsDiv.innerHTML = '';
            if (data.connections && data.connections.length > 0) {
                data.connections.forEach(conn => {
                    const div = document.createElement('div');
                    div.className = 'connection';
                    div.textContent = conn.name; // Assurez-vous que votre route renvoie un champ 'name'
                    connectionsDiv.appendChild(div);
                });
            } else {
                const div = document.createElement('div');
                div.textContent = 'Aucune connexion sortante';
                connectionsDiv.appendChild(div);
            }
            connectionsDiv.style.display = 'block';
        });
}



// Gestion des clics d’évaluation (modifiée pour gérer les deux types de cellules)
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('eval-cell')) {
        cycleEvalColor(e.target);
    }
});

function cycleEvalColor(cell) {
    const colors = ['red', 'orange', 'green'];
    let current = colors.find(c => cell.classList.contains(c));
    let nextColor;

    if (!current) {
        nextColor = 'red';
    } else {
        let idx = colors.indexOf(current);
        // Si on est sur green, le prochain clic enlève la couleur (pas d'évaluation)
        if (current === 'green') {
             nextColor = null; // Pas de couleur pour le prochain état
        } else {
            nextColor = colors[(idx + 1) % colors.length];
        }
        cell.classList.remove(current); // Toujours enlever la couleur actuelle
    }

    cell.classList.remove('red', 'orange', 'green'); // Nettoyer toutes les couleurs
    if (nextColor) {
        cell.classList.add(nextColor); // Ajouter la nouvelle couleur si elle existe
    }
}


// Fonction pour collecter toutes les évaluations et les envoyer au backend (modifiée pour inclure la synthèse)
function saveAllEvaluations() {
    if (!selectedUserId) {
        alert("Aucun utilisateur sélectionné.");
        return;
    }
    const selectedRoleId = document.getElementById('user-roles').value;
    if (!selectedRoleId) {
         alert("Aucun rôle sélectionné.");
         return;
    }

    const evaluationsToSend = [];
    // Sélectionne toutes les cellules d'évaluation, y compris celles de la synthèse
    const evalCells = document.querySelectorAll('.eval-cell');

    evalCells.forEach(cell => {
        const color = ['red', 'orange', 'green'].find(c => cell.classList.contains(c));
        // N'inclure que les cellules qui ont une couleur (ont été évaluées)
        if (color) {
            // Pour les cellules de synthèse, data-eval sera 'collaborator', 'manager', ou 'rh'
            // Pour les cellules d'évolution, data-eval sera '1', '2', ou '3'
            // Le item_type peut être 'savoirs', 'savoir_faires', 'softskills', ou 'competencies' <-- MODIFIÉ
            evaluationsToSend.push({
                item_id: parseInt(cell.dataset.id),
                item_type: cell.dataset.type,
                eval_number: cell.dataset.eval,
                note: color
            });
        }
    });

    const dataToSend = {
        userId: parseInt(selectedUserId),
        roleId: parseInt(selectedRoleId),
        evaluations: evaluationsToSend
    };

    fetch('/competences/save_user_evaluations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dataToSend)
    })
    .then(res => res.json())
    .then(resp => {
        if (resp.success) {
            alert('Évaluations enregistrées avec succès !');
            // Optionnel: Recharger les évaluations pour confirmer la sauvegarde
            // loadRoleKnowledge(selectedRoleId);
            // loadCompetencySynthesis(selectedRoleId);
        } else {
            alert('Erreur lors de l’enregistrement : ' + resp.message);
        }
    })
    .catch((error) => {
        console.error('Erreur de connexion au serveur:', error);
        alert('Erreur de connexion au serveur lors de la sauvegarde.');
    });
}


let tooltipTimeout;
let tooltipActive = false;

// Survol de cellule : lancer le timer pour afficher la date
document.addEventListener('mouseover', (e) => {
    const target = e.target;
    if (target.classList.contains('eval-cell') && target.dataset.date) {
        tooltipTimeout = setTimeout(() => {
            if (tooltipActive) return; // Empêche le double affichage
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
            tooltip.style.maxWidth = '220px';        // Plus large
            tooltip.style.whiteSpace = 'normal';     // Autorise les retours à la ligne
            tooltip.style.boxShadow = '0 2px 6px rgba(0,0,0,0.15)';
            tooltip.style.top = `${e.pageY + 12}px`;
            tooltip.style.left = `${e.pageX + 12}px`;
            document.body.appendChild(tooltip);
        }, 1500); // S'affiche après 1,5s de survol sans clic
    }
});

// Sortie de la cellule : supprimer le tooltip
document.addEventListener('mouseout', (e) => {
    if (e.target.classList.contains('eval-cell')) {
        clearTimeout(tooltipTimeout);
        const popup = document.getElementById('tooltip-popup');
        if (popup) popup.remove();
        tooltipActive = false;
    }
});

// Si l'utilisateur clique sur la cellule : annuler le tooltip immédiatement
document.addEventListener('mousedown', (e) => {
    if (e.target.classList.contains('eval-cell')) {
        clearTimeout(tooltipTimeout);
        const popup = document.getElementById('tooltip-popup');
        if (popup) popup.remove();
        tooltipActive = false;
    }
});
