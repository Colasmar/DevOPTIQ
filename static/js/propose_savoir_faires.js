function proposeSavoirFaires(activityId) {
  const data = getActivityData(activityId);
  fetch("/propose_savoir_faires", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ activity_data: data })
  })
  .then(r => r.json())
  .then(proposals => showProposalModal(activityId, proposals, 'savoir_faire'))
  .catch(err => alert("Erreur proposition Savoir-Faire : " + err));
}
