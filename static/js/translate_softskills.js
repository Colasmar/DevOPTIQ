// Code/static/js/translate_softskills.js

let translationProposals = [];
let translationActivityId = null;

function openTranslateSoftskillsModal(activityId) {
  translationActivityId = activityId;
  document.getElementById('translateSoftskillsModal').style.display = 'block';
}

function closeTranslateSoftskillsModal() {
  document.getElementById('translateSoftskillsModal').style.display = 'none';
  translationActivityId = null;
}

// On ferme le second modal
function closeTranslatedHscModal() {
  document.getElementById('translateResultsModal').style.display = 'none';
}

function submitSoftskillsTranslation() {
  if (!translationActivityId) {
    alert("Erreur : activityId introuvable.");
    return;
  }
  const userInputElem = document.getElementById('translateSoftskillsInput');
  const userInput = userInputElem.value.trim();
  if (!userInput) {
    alert("Veuillez saisir du texte.");
    return;
  }
  showSpinner();
  fetch('/translate_softskills/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_input: userInput,
      activity_data: {}
    })
  })
  .then(r => r.json())
  .then(resp => {
    hideSpinner();
    if (resp.error) {
      alert("Erreur traduction : " + resp.error);
      return;
    }
    if (!resp.proposals || !Array.isArray(resp.proposals)) {
      alert("Réponse inattendue : pas de 'proposals' !");
      return;
    }
    translationProposals = resp.proposals;
    // on ferme la 1ère modale
    document.getElementById('translateSoftskillsModal').style.display = 'none';
    showTranslationProposals(translationProposals);
  })
  .catch(err => {
    hideSpinner();
    console.error("Erreur /translate_softskills/translate:", err);
    alert("Erreur lors de la traduction des softskills.");
  });
}

function showTranslationProposals(proposals) {
  const container = document.getElementById('translatedHscList');
  container.innerHTML = "";
  proposals.forEach((item, idx) => {
    const li = document.createElement('li');
    li.style.marginBottom = '5px';
    const justifSafe = (item.justification || "").replace(/'/g, "\\'");
    li.innerHTML = `
      <label style="cursor:pointer;">
        <input type="checkbox" data-habilete="${item.habilete}" data-niveau="${item.niveau}" data-justif="${justifSafe}" />
        <strong>${item.habilete}</strong> [${item.niveau}]<br/>
        <em>${item.justification}</em>
      </label>
    `;
    container.appendChild(li);
  });
  document.getElementById('translateResultsModal').style.display = 'block';
}

function validateTranslatedHSC() {
  if (!translationActivityId) {
    alert("Erreur : activityId introuvable.");
    return;
  }
  const container = document.getElementById('translatedHscList');
  const checked = container.querySelectorAll('input[type="checkbox"]:checked');
  if (!checked.length) {
    alert("Aucune HSC sélectionnée.");
    return;
  }

  showSpinner();
  let addPromises = [];
  checked.forEach(ch => {
    const habilete = ch.getAttribute('data-habilete');
    const niveau = ch.getAttribute('data-niveau');
    const justification = ch.getAttribute('data-justif') || "";
    let p = fetch('/softskills/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        activity_id: translationActivityId,
        habilete,
        niveau,
        justification
      })
    })
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        console.error("Erreur ajout HSC:", data.error);
      }
    })
    .catch(err => {
      console.error("Erreur /softskills/add:", err);
    });
    addPromises.push(p);
  });

  Promise.all(addPromises).then(() => {
    hideSpinner();
    document.getElementById('translateResultsModal').style.display = 'none';
    updateSoftskillsList(translationActivityId); 
  });
}
