// static/js/propose_savoirs_faires.js

function fetchActivityDetailsForSavoirsFaires(activityId) {
  showSpinner();
  fetch(`/activities/${activityId}/details`)
    .then(r => {
      if (!r.ok) throw new Error("Erreur lors de la récupération des détails de l'activité");
      return r.json();
    })
    .then(activityData => {
      hideSpinner();
      proposeSavoirsFaires(activityData);
    })
    .catch(err => {
      hideSpinner();
      console.error("Erreur fetchActivityDetailsForSavoirsFaires:", err);
      alert("Impossible de récupérer les détails de l'activité (voir console).");
    });
}

async function proposeSavoirsFaires(activityData) {
  showSpinner();
  try {
    // 1) Savoir-Faire d'abord
    const resSF = await fetch("/propose_savoir_faires/propose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(activityData)
    });
    if (!resSF.ok) throw new Error(await resSF.text());
    const sfData = await resSF.json();
    if (sfData.error) throw new Error(sfData.error);
    const savoirFaires = Array.isArray(sfData.proposals) ? sfData.proposals : [];

    // 2) Puis Savoirs, en tenant compte des SF proposés
    const resS = await fetch("/propose_savoirs/propose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...activityData, savoir_faires: savoirFaires })
    });
    if (!resS.ok) throw new Error(await resS.text());
    const sData = await resS.json();
    if (sData.error) throw new Error(sData.error);
    const savoirs = Array.isArray(sData.proposals) ? sData.proposals : [];

    hideSpinner();
    showProposedSavoirsFairesModal(savoirFaires, savoirs, activityData.id);

  } catch (err) {
    hideSpinner();
    console.error("Erreur proposeSavoirsFaires:", err);
    alert("Impossible d'obtenir les propositions (voir console).");
  }
}

function showProposedSavoirsFairesModal(sfList, sList, activityId) {
  let modal = document.getElementById("proposeSavoirsFairesModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "proposeSavoirsFairesModal";
    modal.style.position = "fixed";
    modal.style.left = "10%";
    modal.style.top = "10%";
    modal.style.width = "80%";
    modal.style.maxHeight = "80vh";
    modal.style.overflow = "auto";
    modal.style.background = "#fff";
    modal.style.border = "1px solid #aaa";
    modal.style.padding = "16px";
    modal.style.zIndex = "9999";
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <h3>Propositions Savoir-Faire & Savoirs</h3>
    <div style="display:flex; gap:30px;">
      <div style="flex:1;">
        <h4>Savoir-Faire</h4>
        <ul id="sfList" style="list-style:none; padding-left:0;"></ul>
      </div>
      <div style="flex:1;">
        <h4>Savoirs</h4>
        <ul id="sList" style="list-style:none; padding-left:0;"></ul>
      </div>
    </div>
    <div style="margin-top:12px;">
      <button id="validateBtn">Enregistrer</button>
      <button id="cancelBtn">Annuler</button>
    </div>
  `;

  const sfEl = modal.querySelector("#sfList");
  const sEl = modal.querySelector("#sList");

  sfEl.innerHTML = "";
  sEl.innerHTML = "";

  sfList.forEach(p => {
    const li = document.createElement("li");
    li.style.marginBottom = "6px";
    li.innerHTML = `<label><input type="checkbox" data-type="sf" data-desc="${p}"> ${p}</label>`;
    sfEl.appendChild(li);
  });

  sList.forEach(p => {
    const li = document.createElement("li");
    li.style.marginBottom = "6px";
    li.innerHTML = `<label><input type="checkbox" data-type="s" data-desc="${p}"> ${p}</label>`;
    sEl.appendChild(li);
  });

  modal.querySelector("#cancelBtn").onclick = () => modal.style.display = "none";

  modal.querySelector("#validateBtn").onclick = () => {
    const selected = modal.querySelectorAll("input[type=checkbox]:checked");
    if (!selected.length) {
      alert("Aucun élément sélectionné.");
      return;
    }
    showSpinner();
    const promises = [];
    selected.forEach(ch => {
      const desc = ch.getAttribute("data-desc");
      const type = ch.getAttribute("data-type");
      if (type === "sf") {
        promises.push(fetch("/savoir_faires/add", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ activity_id: activityId, description: desc })
        }).then(r => r.json()));
      } else {
        promises.push(fetch("/savoirs/add", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ activity_id: activityId, description: desc })
        }).then(r => r.json()));
      }
    });

    Promise.all(promises)
      .then(() => {
        hideSpinner();
        modal.style.display = "none";
        // Rafraîchis les deux colonnes (fonctions déjà présentes dans ton code)
        updateSavoirs(activityId);
        updateSavoirFaires(activityId);
      })
      .catch(err => {
        hideSpinner();
        console.error("Erreur d'enregistrement:", err);
        alert("Erreur lors de l'enregistrement des propositions.");
      });
  };

  modal.style.display = "block";
}
