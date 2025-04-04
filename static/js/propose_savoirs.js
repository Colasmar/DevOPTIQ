function proposeSavoirs(activityId) {
  const data = getActivityData(activityId);
  fetch("/propose_savoirs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ activity_data: data })
  })
  .then(r => r.json())
  .then(proposals => showProposalModal(activityId, proposals, 'savoir'))
  .catch(err => alert("Erreur proposition Savoirs : " + err));
}
