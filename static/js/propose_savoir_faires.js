// Code/static/js/propose_savoirs
/**
 * Analyse l'activité, appelle /propose_savoir_faires/propose (non fourni ici)
 * et affiche le résultat dans un modal => checkboxes => /savoir_faires/add
 */

function fetchActivityDetailsForSavoirFaires(activityId) {
    showSpinner();
    fetch(`/activities/${activityId}/details`)
        .then(response => {
            if (!response.ok) {
                hideSpinner();
                throw new Error("Erreur lors de la récupération des détails de l'activité");
            }
            return response.json();
        })
        .then(activityData => {
            hideSpinner();
            proposeSavoirFaires(activityData);
        })
        .catch(error => {
            hideSpinner();
            console.error("Erreur fetchActivityDetailsForSavoirFaires:", error);
            alert("Impossible de récupérer les détails de l'activité pour Proposer Savoir-Faires");
        });
}

/**
 * Appelle l'IA pour proposer des savoir-faires (POST /propose_savoir_faires/propose),
 * Puis ouvre le modal avec les options proposées.
 */
function proposeSavoirFaires(activityData) {
    showSpinner();
    fetch("/propose_savoir_faires/propose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(activityData)
    })
        .then(async response => {
            if (!response.ok) {
                const text = await response.text();
                throw new Error(`Réponse invalide de /propose_savoir_faires/propose: ${text}`);
            }
            return response.json();
        })
        .then(data => {
            hideSpinner();
            if (data.error) {
                console.error("Erreur IA /propose_savoir_faires/propose:", data.error);
                alert("Erreur proposition Savoir-Faires : " + data.error);
                return;
            }
            const lines = data.proposals;
            if (!lines || !Array.isArray(lines)) {
                alert("Aucune proposition retournée.");
                return;
            }
            showProposedSavoirFaires(lines, activityData.id);
        })
        .catch(err => {
            hideSpinner();
            console.error("Erreur lors de la proposition de savoir-faires:", err);
            alert("Impossible d'obtenir des propositions de savoir-faires (voir console).");
        });
}

function showProposedSavoirFaires(proposals, activityId) {
    let modal = document.getElementById('proposeSavoirFairesModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'proposeSavoirFairesModal';
        modal.style.position = 'fixed';
        modal.style.left = '25%';
        modal.style.top = '25%';
        modal.style.width = '50%';
        modal.style.background = '#fff';
        modal.style.border = '1px solid #aaa';
        modal.style.padding = '10px';
        modal.style.zIndex = '9999';
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <h4>Propositions de Savoir-Faires</h4>
      <ul id="proposedSavoirFairesList" style="list-style:none; padding-left:0;"></ul>
      <div style="margin-top:10px;">
        <button id="validateProposedSavoirFairesBtn">Enregistrer</button>
        <button id="cancelProposedSavoirFairesBtn">Annuler</button>
      </div>
    `;

    const listEl = modal.querySelector('#proposedSavoirFairesList');
    listEl.innerHTML = "";
    proposals.forEach((p) => {
        const li = document.createElement('li');
        li.style.marginBottom = "5px";
        li.innerHTML = `
        <label style="cursor:pointer;">
          <input type="checkbox" 
                data-description="${p}" />
          ${p}
        </label>
      `;
        listEl.appendChild(li);
    });

    modal.style.display = 'block';

    modal.querySelector('#cancelProposedSavoirFairesBtn').onclick = () => {
        modal.style.display = 'none';
    };

    modal.querySelector('#validateProposedSavoirFairesBtn').onclick = () => {
        const selected = listEl.querySelectorAll('input[type="checkbox"]:checked');
        if (!selected.length) {
            alert("Aucun savoir-faires sélectionné.");
            return;
        }
        showSpinner();
        let addPromises = [];
        selected.forEach(ch => {
            const description = ch.getAttribute('data-description');
            let p = fetch('/savoir_faires/add', {
                method: 'POST',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    description,
                    activity_id: activityId
                })
            })
                .then(r => r.json())
                .then(d => {
                    if (d.error) {
                        console.error("Erreur ajout Savoir-Faires:", d.error);
                    }
                })
                .catch(err => {
                    console.error("Erreur /savoir_faires/add:", err);
                });
            addPromises.push(p);
        });

        Promise.all(addPromises).then(() => {
            hideSpinner();
            modal.style.display = 'none';
            updateSavoirFaires(activityId);
        })
            .catch(err => {
                hideSpinner();
                alert("Erreur lors de l'ajout des savoir-faires.");
                console.error(err);
            });
    };
}
