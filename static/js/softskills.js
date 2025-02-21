// softskills.js - Gestion des habiletés socio-cognitives (HSC)

// Convertit un niveau numérique (1..4) en label
function translateLevelToText(level) {
    switch(level) {
      case "1": return "Aptitude";
      case "2": return "Acquisition";
      case "3": return "Maîtrise";
      case "4": return "Excellence";
      default:  return "Inconnu";
    }
  }
  
  // Lancement de l'IA pour définir les HSC via le bouton "Définir HSC"
  $(document).on('click', '.define-hsc-btn', function() {
    const activityId = $(this).data('activity-id');
    proposeSoftskills(activityId);
  });
  
  /**
   * Appel à l'endpoint /softskills/propose pour récupérer 3-4 habiletés socio-cognitives via l'IA.
   */
  function proposeSoftskills(activityId) {
      var activityData = getActivityDetails(activityId);
      var competenciesData = getCompetenciesData(activityId);
      $.ajax({
          url: '/softskills/propose',
          method: 'POST',
          contentType: 'application/json',
          data: JSON.stringify({
              activity: activityData,
              competencies: competenciesData
          }),
          success: function(response) {
              renderSoftskills(activityId, response);
          },
          error: function() {
              alert("Erreur lors de la récupération des habiletés socio-cognitives.");
          }
      });
  }
  
  function renderSoftskills(activityId, softskills) {
      var container = document.getElementById('softskills-list-' + activityId);
      container.innerHTML = "";
      softskills.forEach(function(item) {
          addSoftskillItemToDOM(activityId, item.habilete, item.niveau);
      });
  }
  
  // Gestion manuelle des HSC (ajout, édition, suppression)
  function showSoftskillForm(activityId) {
    document.getElementById('softskill-form-' + activityId).style.display = 'block';
  }
  function hideSoftskillForm(activityId) {
    document.getElementById('softskill-form-' + activityId).style.display = 'none';
  }
  function submitSoftskill(activityId) {
    let nameInput = document.getElementById('softskill-name-' + activityId);
    let levelInput = document.getElementById('softskill-level-' + activityId);
    let hscName = nameInput.value.trim();
    let hscLevel = levelInput.value.trim();
    if(!hscName) {
      alert("Veuillez saisir un nom d'habileté.");
      return;
    }
    if(!hscLevel || !["1","2","3","4"].includes(hscLevel)) {
      alert("Le niveau doit être 1, 2, 3 ou 4.");
      return;
    }
    addSoftskillItemToDOM(activityId, hscName, hscLevel);
    nameInput.value = "";
    levelInput.value = "";
    hideSoftskillForm(activityId);
  }
  
  function addSoftskillItemToDOM(activityId, hscName, hscLevel) {
    let container = document.getElementById('softskills-list-' + activityId);
    let index = container.children.length;
    let softskillItem = document.createElement('div');
    softskillItem.className = 'softskill-item';
    softskillItem.setAttribute('data-index', index);
    let levelLabel = translateLevelToText(hscLevel);
    softskillItem.innerHTML = `
      <span class="softskill-text">${hscName} (Niveau: <span class="softskill-level">${levelLabel}</span>)</span>
      <i class="fas fa-pencil-alt edit-softskill" title="Modifier"></i>
      <i class="fas fa-trash delete-softskill" title="Supprimer"></i>
      <div class="edit-softskill-form" id="edit-softskill-form-${activityId}-${index}" style="display:none;">
        <label>Habileté :</label>
        <input type="text" id="edit-softskill-name-${activityId}-${index}" value="${hscName}" />
        <label>Niveau (1..4) :</label>
        <input type="number" min="1" max="4" id="edit-softskill-level-${activityId}-${index}" value="${hscLevel}" />
        <button onclick="submitEditSoftskill('${activityId}', ${index})">Enregistrer</button>
        <button onclick="hideEditSoftskillForm('${activityId}', ${index})">Annuler</button>
      </div>
    `;
    container.appendChild(softskillItem);
  }
  
  $(document).on('click', '.edit-softskill', function() {
    let itemElem = $(this).closest('.softskill-item');
    let index = itemElem.data('index');
    let parentId = itemElem.parent().attr('id'); // format: "softskills-list-<activityId>"
    let activityId = parentId.split('-')[2];
    showEditSoftskillForm(activityId, index);
  });
  function showEditSoftskillForm(activityId, index) {
    document.getElementById(`edit-softskill-form-${activityId}-${index}`).style.display = 'block';
  }
  function hideEditSoftskillForm(activityId, index) {
    document.getElementById(`edit-softskill-form-${activityId}-${index}`).style.display = 'none';
  }
  function submitEditSoftskill(activityId, index) {
    let nameInput = document.getElementById(`edit-softskill-name-${activityId}-${index}`);
    let levelInput = document.getElementById(`edit-softskill-level-${activityId}-${index}`);
    let newName = nameInput.value.trim();
    let newLevel = levelInput.value.trim();
    if(!newName) {
      alert("Veuillez saisir un nom d'habileté.");
      return;
    }
    if(!["1","2","3","4"].includes(newLevel)) {
      alert("Le niveau doit être 1, 2, 3 ou 4.");
      return;
    }
    let container = document.getElementById('softskills-list-' + activityId);
    let itemElem = container.querySelector(`.softskill-item[data-index="${index}"]`);
    let textElem = itemElem.querySelector('.softskill-text');
    let levelLabel = translateLevelToText(newLevel);
    textElem.innerHTML = `${newName} (Niveau: <span class="softskill-level">${levelLabel}</span>)`;
    hideEditSoftskillForm(activityId, index);
  }
  
  $(document).on('click', '.delete-softskill', function() {
    if(!confirm("Voulez-vous supprimer cette habileté ?")) return;
    $(this).closest('.softskill-item').remove();
  });
  