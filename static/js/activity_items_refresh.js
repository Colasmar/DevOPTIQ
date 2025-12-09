// static/js/activity_items_refresh.js
// Rafraîchissement UNIFIÉ de tout ce qui concerne une activité :
// - savoirs
// - savoir-faire
// - softskills (HSC)
// - aptitudes
// Peu importe quel bloc est présent sur la page, on met à jour ce qui existe.

async function refreshActivityItems(activityId) {
  // petit helper pour essayer de fetch un partial et l'injecter si le conteneur est là
  async function fetchAndInject(url, possibleIds) {
    try {
      const resp = await fetch(url);
      if (!resp.ok) {
        console.warn("refreshActivityItems: HTTP " + resp.status + " sur " + url);
        return;
      }
      const html = await resp.text();
      // on essaie tous les ids possibles
      for (const domId of possibleIds) {
        const el = document.getElementById(domId);
        if (el) {
          el.innerHTML = html;
          break; // on arrête dès qu'on a trouvé un conteneur
        }
      }
    } catch (e) {
      console.error("refreshActivityItems:", url, e);
    }
  }

  // 1) Savoirs
  await fetchAndInject(
    `/savoirs/${activityId}/render`,
    [
      `savoirs-container-${activityId}`,
      `savoirs-list-${activityId}`,      // ancien id
      `sf-sv-body-${activityId}`         // dans le bloc fusion
    ]
  );

  // 2) Savoir-faire
  await fetchAndInject(
    `/savoir_faires/${activityId}/render`,
    [
      `savoirs-faires-container-${activityId}`,
      `savoir-faires-list-${activityId}`,
      `sf-sv-body-${activityId}`
    ]
  );

  // 3) Softskills / HSC
  await fetchAndInject(
    `/softskills/${activityId}/render`,
    [
      `softskills-container-${activityId}`,
      `softskills-list-${activityId}`
    ]
  );

  // 4) Aptitudes
  await fetchAndInject(
    `/aptitudes/${activityId}/render`,
    [
      `aptitudes-container-${activityId}`,
      `aptitude-list-${activityId}`
    ]
  );
}

// on l'expose en global
window.refreshActivityItems = refreshActivityItems;
