// main.js – Fonctions globales et gestion modale proposition IA

if (!window.OPTIQ_MAIN_LOADED) {
  window.OPTIQ_MAIN_LOADED = true;

  window.currentActivityId = null;
  window.currentType = "";

  window.toggleDetails = function (detailsId, headerElem) {
    const detailsElem = document.getElementById(detailsId);
    const iconElem = headerElem.querySelector('.toggle-icon');
    const currentDisplay = window.getComputedStyle(detailsElem).display;

    if (currentDisplay === "none") {
      detailsElem.style.display = "block";
      iconElem.textContent = "▼";
    } else {
      detailsElem.style.display = "none";
      iconElem.textContent = "▶";
    }
  };

  function getProposeUrl(type) {
    return `/propose_${type}/propose`;
  }

  window.getActivityData = function (activityId) {
    const detailsElem = document.getElementById(`details-${activityId}`);
    return detailsElem ? detailsElem.innerText : "";
  };

  window.showProposalModal = function (activityId, proposals, type) {
    window.currentType = type;
    window.currentActivityId = activityId;
    $("#proposal-title").text(`Propositions ${type}`);
    $("#proposal-list").html("");
    proposals.forEach(p => {
      $("#proposal-list").append(`<li><input type='checkbox' value="${p}"> ${p}</li>`);
    });
    $("#proposal-modal").show();
  };

  window.validateProposal = function () {
    const selected = [];
    $("#proposal-list input:checked").each((_, el) => selected.push(el.value));

    selected.forEach(val => {
      fetch(`/${window.currentType}/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ activity_id: window.currentActivityId, name: val }),
      });
    });

    alert(`${selected.length} ${window.currentType}(s) ajouté(s) !`);
    window.closeProposalModal();
    location.reload();
  };

  window.closeProposalModal = function () {
    $("#proposal-modal").hide();
  };

  window.proposeSavoirs = function (activityId) {
    const text = window.getActivityData(activityId);
    fetch(getProposeUrl("savoirs"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activity_data: { name: "", description: text, tasks: "", tools: "" } })
    })
    .then(resp => resp.json())
    .then(data => window.showProposalModal(activityId, data.proposals, "savoirs"))
    .catch(err => console.error("Erreur proposition Savoirs :", err));
  };

  window.proposeSavoirFaires = function (activityId) {
    const text = window.getActivityData(activityId);
    fetch(getProposeUrl("savoir_faires"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activity_data: { name: "", description: text, tasks: "", tools: "" } })
    })
    .then(resp => resp.json())
    .then(data => window.showProposalModal(activityId, data.proposals, "savoir_faires"))
    .catch(err => console.error("Erreur proposition Savoir-Faire :", err));
  };

  window.proposeAptitudes = function (activityId) {
    const text = window.getActivityData(activityId);
    fetch(getProposeUrl("aptitudes"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activity_data: { name: "", description: text, tasks: "", tools: "" } })
    })
    .then(resp => resp.json())
    .then(data => window.showProposalModal(activityId, data.proposals, "aptitudes"))
    .catch(err => console.error("Erreur proposition Aptitudes :", err));
  };
}
function fetchActivityDetailsForProposeSavoirs(activityId) {
  const activityBlock = document.getElementById(`activity-block-${activityId}`) || document;
  const nameElem = activityBlock.querySelector(`.activity-name`);
  const descElem = activityBlock.querySelector(`.activity-desc`);
  const taskElems = activityBlock.querySelectorAll(`.task-name`);
  const toolElems = activityBlock.querySelectorAll(`.tool-name`);

  const tasks = Array.from(taskElems).map(el => el.textContent.trim());
  const tools = Array.from(toolElems).map(el => el.textContent.trim());

  const payload = {
    activity_data: {
      name: nameElem ? nameElem.textContent.trim() : '',
      description: descElem ? descElem.textContent.trim() : '',
      tasks: tasks,
      tools: tools
    }
  };

  fetch('/propose_savoirs/propose', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      alert("Erreur: " + data.error);
    } else {
      alert("Propositions de savoirs :\n" + data.proposals.join("\n"));
    }
  })
  .catch(err => {
    console.error("Erreur:", err);
    alert("Une erreur est survenue lors de la génération des savoirs.");
  });
}
document.addEventListener("DOMContentLoaded", function () {
  const cartoButton = document.getElementById("update-cartography-button");

  if (cartoButton) {
    cartoButton.addEventListener("click", function () {
      if (typeof showSpinner === "function") showSpinner();

      fetch("/activities/update-cartography")
        .then((response) => response.json())
        .then((data) => {
          if (typeof hideSpinner === "function") hideSpinner();

          if (data.error) {
            alert("Erreur : " + data.error);
          } else {
            alert(data.message + "\n\nRésumé :\n" + data.summary);
            location.reload();  // CETTE LIGNE AJOUTE LE RAFRAÎCHISSEMENT AUTOMATIQUE
          }
        })
        .catch((err) => {
          if (typeof hideSpinner === "function") hideSpinner();

          console.error("Erreur update-cartography:", err);
          alert("Erreur de mise à jour de la cartographie.");
        });
    });
  }
});
