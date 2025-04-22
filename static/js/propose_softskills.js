// Code/static/js/propose_softskills.js

/**
 * Analyse l'activité, appelle /propose_softskills/propose (non fourni ici)
 * et affiche le résultat dans un modal => checkboxes => /softskills/add
 * 
 * => A titre d'exemple, si ton code actuel s'appelle autrement, 
 *    adapte ou supprime ce fichier. 
 */

function fetchActivityDetailsForPropose(activityId) {
  showSpinner();
  // On appelle /activities/<activityId>/details pour un JSON complet
  fetch(`/activities/${activityId}/details`)
    .then(r => {
      if (!r.ok) {
        hideSpinner();
        throw new Error("Erreur /activities/details");
      }
      return r.json();
    })
    .then(data => {
      hideSpinner();
      proposeSoftskills(data);
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur fetchActivityDetailsForPropose:", err);
      alert("Impossible de récupérer les détails pour Proposer HSC");
    });
}

function proposeSoftskills(activityData) {
  showSpinner();
  fetch('/propose_softskills/propose', {
    method: 'POST',
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(activityData)
  })
  .then(r => {
    if (!r.ok) {
      hideSpinner();
      throw new Error("Erreur /propose_softskills/propose");
    }
    return r.json();
  })
  .then(resp => {
    hideSpinner();
    if (resp.error) {
      alert("Erreur proposition HSC : " + resp.error);
      return;
    }
    if (!resp.proposals || !Array.isArray(resp.proposals)) {
      alert("Réponse inattendue : 'proposals' manquant.");
      return;
    }
    // On ouvre un modal similaire à la traduction ?
    showProposedSoftskills(resp.proposals, activityData.id);
  })
  .catch(err => {
    hideSpinner();
    console.error("Erreur proposeSoftskills:", err);
    alert("Erreur proposeSoftskills");
  });
}






// On crée un modal similaire à translateResultsModal
function showProposedSoftskills(hscProposals, activityId) {
  // Création d'un modal dynamique
  let modal = document.getElementById('proposeHscModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'proposeHscModal';
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
    <h4>Propositions d'HSC</h4>
    <ul id="proposedHscList" style="list-style:none; padding-left:0;"></ul>
    <div style="margin-top:10px;">
      <button id="validateProposedHscBtn">Enregistrer</button>
      <button id="cancelProposedHscBtn">Annuler</button>
    </div>
  `;

  const listEl = modal.querySelector('#proposedHscList');
  listEl.innerHTML = "";
  hscProposals.forEach((p) => {
    const li = document.createElement('li');
    li.style.marginBottom = "5px";
    const justifSafe = (p.justification || "").replace(/'/g, "\\'");
    li.innerHTML = `
      <label style="cursor:pointer;">
        <input type="checkbox" 
               data-habilete="${p.habilete}" 
               data-niveau="${p.niveau}" 
               data-justif="${justifSafe}" />
        <strong>${p.habilete}</strong> [${p.niveau}]<br/>
        <em>${p.justification}</em>
      </label>
    `;
    listEl.appendChild(li);
  });

  modal.style.display = 'block';

  // Bouton "Annuler"
  modal.querySelector('#cancelProposedHscBtn').onclick = () => {
    modal.style.display = 'none';
  };

  // Bouton "Enregistrer"
  modal.querySelector('#validateProposedHscBtn').onclick = () => {
    const checkboxes = listEl.querySelectorAll('input[type="checkbox"]:checked');
    if (!checkboxes.length) {
      alert("Aucune HSC sélectionnée.");
      return;
    }
    showSpinner();
    let addPromises = [];
    checkboxes.forEach(ch => {
      const habilete = ch.getAttribute('data-habilete');
      const niveau = ch.getAttribute('data-niveau');
      const justification = ch.getAttribute('data-justif') || "";
      let p = fetch('/softskills/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity_id: activityId,
          habilete,
          niveau,
          justification
        })
      })
      .then(r => r.json())
      .then(d => {
        if (d.error) {
          console.error("Erreur ajout HSC:", d.error);
        }
      })
      .catch(err => {
        console.error("Erreur /softskills/add:", err);
      });
      addPromises.push(p);
    });

    Promise.all(addPromises).then(() => {
      hideSpinner();
      modal.style.display = 'none';
      updateSoftskillsList(activityId);
    });
  };
}
