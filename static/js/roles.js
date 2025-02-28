// static/js/roles.js

function openGarantModal(activityId) {
    document.getElementById('garantModal').style.display = 'block';
    document.getElementById('garant-activity-id').value = activityId;

    // Charger la liste des rôles
    let selectElem = document.getElementById('garant-role-select');
    selectElem.innerHTML = "";

    fetch('/roles/list')
    .then(response => response.json())
    .then(data => {
        data.forEach(r => {
            let opt = document.createElement('option');
            opt.value = r.name;
            opt.textContent = r.name;
            selectElem.appendChild(opt);
        });
    })
    .catch(err => {
        alert("Erreur lors du chargement des rôles: " + err.message);
    });
}

function closeGarantModal() {
    document.getElementById('garantModal').style.display = 'none';
}

function submitGarantRole() {
    let activityId = document.getElementById('garant-activity-id').value;
    let selectElem = document.getElementById('garant-role-select');
    let newRoleInput = document.getElementById('garant-new-role').value.trim();
    let roleName = newRoleInput || selectElem.value;

    if(!roleName) {
        alert("Veuillez sélectionner ou saisir un rôle.");
        return;
    }

    fetch('/roles/garant/activity/' + activityId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role_name: roleName })
    })
    .then(r => r.json())
    .then(data => {
        if(data.error) {
            alert("Erreur: " + data.error);
        } else {
            // Mettre à jour l'affichage
            let garantSpan = document.getElementById('activity-garant-' + activityId);
            garantSpan.textContent = "Garant : " + data.role.name;
            closeGarantModal();
        }
    })
    .catch(err => {
        alert("Erreur lors de l'enregistrement du rôle: " + err.message);
    });
}
