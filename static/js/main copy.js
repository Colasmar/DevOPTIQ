// main.js – Fonctions globales et gestion modale proposition IA

// Vérification préalable pour éviter redéclaration
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
}
