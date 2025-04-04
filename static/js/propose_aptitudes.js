function proposeAptitudes(activityId) {
  const data = getActivityData(activityId);
  fetch("/propose_aptitudes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ activity_data: data })
  })
  .then(r => r.json())
  .then(proposals => showProposalModal(activityId, proposals, 'aptitude'))
  .catch(err => alert("Erreur proposition Aptitudes : " + err));
}
