// Code/static/js/propose_savoirs.js

/**
 * Analyse l'activité, appelle /propose_savoir/propose (non fourni ici)
 * et affiche le résultat dans un modal => checkboxes => /savoirs/add
 * 
 */

function fetchActivityDetailsForSavoirs(activityId) {
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
        proposeSavoirs(activityData);  
      })
      .catch(error => {
        hideSpinner();
        console.error("Erreur fetchActivityDetailsForSavoirs:", error);
        alert("Impossible de récupérer les détails de l'activité pour Proposer Savoirs");
      });
  }
  
  /**
   * Appelle l'IA pour proposer des savoirs (POST /savoirs/propose_savoirs),
   * Puis ouvre le modal savoirModal avec les options proposées.
   */
  function proposeSavoirs(activityData) {
    showSpinner();
    fetch("/propose_savoirs/propose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(activityData)
    })
    .then(async response => {
      if (!response.ok) {
        const text = await response.text();
          throw new Error(`Réponse invalide de /propose_savoirs/propose: ${text}`);
      }
      return response.json();
    })
    .then(data => {
      hideSpinner();
      console.log(data);
      if (data.error) {
        console.error("Erreur IA /savoirs/propose_savoirs:", data.error);
        alert("Erreur proposition Savoirs : " + data.error);
        return;
      }
      const lines = data.proposals;
      if (!lines || !Array.isArray(lines)) {
        alert("Aucune proposition retournée.");
        return;
      }
      showProposedSavoirs(lines, activityData.id);
      
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur lors de la proposition de savoirs:", err);
      alert("Impossible d'obtenir des propositions de savoirs (voir console).");
    });
  }
  



  function showProposedSavoirs(proposals, activityId) {
    let modal = document.getElementById('proposeSavoirsModal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'proposeSavoirsModal';
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
      <h4>Propositions de Savoirs</h4>
      <ul id="proposedSavoirsList" style="list-style:none; padding-left:0;"></ul>
      <div style="margin-top:10px;">
        <button id="validateProposedSavoirsBtn">Enregistrer</button>
        <button id="cancelProposedSavoirsBtn">Annuler</button>
      </div>
    `;
  
    const listEl = modal.querySelector('#proposedSavoirsList');
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
  

    // Bouton d'annulation
    modal.querySelector('#cancelProposedSavoirsBtn').onclick = () => {
      modal.style.display = 'none';
    };
    

    // Bouton d'Enregistrement
    modal.querySelector('#validateProposedSavoirsBtn').onclick = () => {
        const selected = listEl.querySelectorAll('input[type="checkbox"]:checked');
        if (!selected.length) {
            alert("Aucun savoir sélectionné.");
            return;
        }
        showSpinner();
        let addPromises = [];
        selected.forEach(ch => {
            const description = ch.getAttribute('data-description');
            let p = fetch('/savoirs/add', {
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
                console.error("Erreur ajout Savoirs:", d.error);
                }
            })
            .catch(err => {
                console.error("Erreur /savoirs/add:", err);
            });
            addPromises.push(p);
        });
               
        Promise.all(addPromises).then(() => {
            hideSpinner();
            modal.style.display = 'none';
            updateSavoirs(activityId);
        })
        .catch(err => {
            hideSpinner();
            alert("Erreur lors de l'ajout des savoirs.");
            console.error(err);
        });
    };
    
}


  