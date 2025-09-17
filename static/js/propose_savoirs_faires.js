// static/js/propose_savoirs_faires.js

(function () {
  const safeShowSpinner = () => (typeof showSpinner === "function" ? showSpinner() : void 0);
  const safeHideSpinner  = () => (typeof hideSpinner === "function" ? hideSpinner()  : void 0);

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async function fetchActivityDetailsForSavoirsFaires(activityId) {
    safeShowSpinner();
    try {
      const r = await fetch(`/activities/${activityId}/details`);
      if (!r.ok) throw new Error("Erreur lors de la récupération des détails de l'activité");
      const activityData = await r.json();
      safeHideSpinner();
      await proposeSavoirsFaires(activityData);
    } catch (err) {
      safeHideSpinner();
      console.error("Erreur fetchActivityDetailsForSavoirsFaires:", err);
      alert("Impossible de récupérer les détails de l'activité (voir console).");
    }
  }

  async function proposeSavoirsFaires(activityData) {
    safeShowSpinner();
    try {
      // 1) proposer SF
      const resSF = await fetch("/propose_savoir_faires/propose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(activityData)
      });
      if (!resSF.ok) throw new Error(await resSF.text());
      const sfData = await resSF.json();
      if (sfData.error) throw new Error(sfData.error);
      const savoirFaires = Array.isArray(sfData.proposals) ? sfData.proposals : [];

      // 2) proposer S en tenant compte des SF proposés
      const resS = await fetch("/propose_savoirs/propose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...activityData, savoir_faires: savoirFaires })
      });
      if (!resS.ok) throw new Error(await resS.text());
      const sData = await resS.json();
      if (sData.error) throw new Error(sData.error);
      const savoirs = Array.isArray(sData.proposals) ? sData.proposals : [];

      safeHideSpinner();
      showProposedSavoirsFairesModal(savoirFaires, savoirs, activityData.id);
    } catch (err) {
      safeHideSpinner();
      console.error("Erreur proposeSavoirsFaires:", err);
      alert("Impossible d'obtenir les propositions (voir console).");
    }
  }

  function showProposedSavoirsFairesModal(sfList, sList, activityId) {
    let modal = document.getElementById("proposeSavoirsFairesModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "proposeSavoirsFairesModal";
      Object.assign(modal.style, {
        position: "fixed", left: "10%", top: "10%", width: "80%", maxHeight: "80vh",
        overflow: "auto", background: "#fff", border: "1px solid #aaa",
        padding: "16px", zIndex: "9999", boxShadow: "0 10px 25px rgba(0,0,0,0.15)", borderRadius: "10px",
      });
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <h3 style="margin-top:0">Propositions Savoir-Faire & Savoirs</h3>
      <div style="display:flex; gap:30px; align-items:flex-start;">
        <div style="flex:1;">
          <h4 style="margin:6px 0 10px;">Savoir-Faire</h4>
          <ul id="sfList" style="list-style:none; padding-left:0; margin:0;"></ul>
        </div>
        <div style="flex:1;">
          <h4 style="margin:6px 0 10px;">Savoirs</h4>
          <ul id="sList" style="list-style:none; padding-left:0; margin:0;"></ul>
        </div>
      </div>
      <div style="margin-top:16px; display:flex; gap:10px; justify-content:flex-end;">
        <button id="validateBtn" class="btn btn-primary">Enregistrer</button>
        <button id="cancelBtn" class="btn">Annuler</button>
      </div>
    `;

    const sfEl = modal.querySelector("#sfList");
    const sEl  = modal.querySelector("#sList");

    sfEl.innerHTML = "";
    sEl.innerHTML  = "";

    sfList.forEach(p => {
      const li = document.createElement("li");
      li.style.marginBottom = "6px";
      li.innerHTML = `<label><input type="checkbox" data-type="sf" data-desc="${escapeHtml(p)}"> ${escapeHtml(p)}</label>`;
      sfEl.appendChild(li);
    });

    sList.forEach(p => {
      const li = document.createElement("li");
      li.style.marginBottom = "6px";
      li.innerHTML = `<label><input type="checkbox" data-type="s" data-desc="${escapeHtml(p)}"> ${escapeHtml(p)}</label>`;
      sEl.appendChild(li);
    });

    modal.querySelector("#cancelBtn").onclick = () => { modal.style.display = "none"; };

    modal.querySelector("#validateBtn").onclick = async () => {
      const checked = modal.querySelectorAll('input[type="checkbox"]:checked');
      if (!checked.length) {
        alert("Aucun élément sélectionné.");
        return;
      }

      const selectedSF = [];
      const selectedS  = [];
      checked.forEach(ch => {
        const desc = ch.getAttribute("data-desc");
        const type = ch.getAttribute("data-type");
        if (type === "sf") selectedSF.push(desc);
        else if (type === "s") selectedS.push(desc);
      });

      safeShowSpinner();
      try {
        // 1) SF : batch -> fallback unitaire si nécessaire
        if (selectedSF.length > 0) {
          try {
            const r = await fetch("/savoir_faires/add", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ activity_id: activityId, savoir_faires: selectedSF }),
            });
            if (!r.ok) throw new Error(await r.text());
          } catch (e) {
            // Fallback unitaire
            await Promise.all(selectedSF.map(desc =>
              fetch("/savoir_faires/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ activity_id: activityId, description: desc }),
              }).then(rr => { if (!rr.ok) return rr.text().then(t => { throw new Error(t); }); })
            ));
          }
        }

        // 2) Savoirs : unitaire (à batcher si tu ajoutes la route)
        if (selectedS.length > 0) {
          await Promise.all(selectedS.map(desc =>
            fetch("/savoirs/add", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ activity_id: activityId, description: desc }),
            }).then(rr => { if (!rr.ok) return rr.text().then(t => { throw new Error(t); }); })
          ));
        }

        // ⤵️ Rafraîchit le fragment unique
        if (typeof refreshSavoirsEtSavoirFaires === "function") {
          await refreshSavoirsEtSavoirFaires(activityId);
        }

        modal.style.display = "none";
      } catch (err) {
        console.error("Erreur d'enregistrement:", err);
        alert("Erreur lors de l'enregistrement des propositions (voir console).");
      } finally {
        safeHideSpinner();
      }
    };

    modal.style.display = "block";
  }

  // Exposer globalement
  window.fetchActivityDetailsForSavoirsFaires = fetchActivityDetailsForSavoirsFaires;
  window.proposeSavoirsFaires = proposeSavoirsFaires;
  window.showProposedSavoirsFairesModal = showProposedSavoirsFairesModal;
})();
