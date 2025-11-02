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

      const sfData = await resSF.json().catch(() => ({}));
      if (!resSF.ok) {
        // on ne jette plus → on continue avec un fallback vide
        console.warn("Réponse non OK /propose_savoir_faires/propose:", sfData);
      }
      const savoirFaires = Array.isArray(sfData.proposals) ? sfData.proposals : [];

      // 2) proposer S en tenant compte des SF proposés
      const resS = await fetch("/propose_savoirs/propose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...activityData, savoir_faires: savoirFaires })
      });

      const sData = await resS.json().catch(() => ({}));
      if (!resS.ok) {
        console.warn("Réponse non OK /propose_savoirs/propose:", sData);
      }
      const savoirs = Array.isArray(sData.proposals) ? sData.proposals : [];

      safeHideSpinner();
      showProposedSavoirsFairesModal(savoirFaires, savoirs, activityData.id);
    } catch (err) {
      safeHideSpinner();
      console.error("Erreur proposeSavoirsFaires:", err);
      alert("Impossible d'obtenir les propositions (voir console).");
    }
  }

  function ensureModal() {
    let modal = document.getElementById("proposeSavoirsFairesModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "proposeSavoirsFairesModal";
      Object.assign(modal.style, {
        position: "fixed",
        left: "10%",
        top: "10%",
        width: "80%",
        maxHeight: "80vh",
        overflow: "auto",
        background: "#fff",
        border: "1px solid #aaa",
        padding: "16px",
        zIndex: "9999",
        boxShadow: "0 10px 25px rgba(0,0,0,0.15)",
        borderRadius: "10px",
      });
      document.body.appendChild(modal);
    }
    return modal;
  }

  function showProposedSavoirsFairesModal(sfList, sList, activityId) {
    const modal = ensureModal();

    modal.innerHTML = `
      <h3 style="margin-top:0">Propositions Savoir-Faire & Savoirs</h3>
      <p style="color:#888;font-size:0.85rem;">(Si vous voyez des propositions “génériques”, c’est que la clé OpenAI n’est pas définie côté serveur.)</p>
      <div style="display:flex; gap:30px; align-items:flex-start; flex-wrap:wrap;">
        <div style="flex:1; min-width:280px;">
          <h4 style="margin:6px 0 10px;">Savoir-Faire</h4>
          <ul id="sfList" style="list-style:none; padding-left:0; margin:0;"></ul>
        </div>
        <div style="flex:1; min-width:280px;">
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

    const fill = (container, items, type) => {
      if (!items || !items.length) {
        container.innerHTML = `<li style="color:#999;">Aucune proposition</li>`;
        return;
      }
      container.innerHTML = items.map(desc => `
        <li style="margin-bottom:4px;">
          <label style="display:flex; gap:6px; align-items:flex-start;">
            <input type="checkbox" data-type="${type}" data-desc="${escapeHtml(desc)}" checked />
            <span>${escapeHtml(desc)}</span>
          </label>
        </li>
      `).join("");
    };

    fill(sfEl, sfList, "sf");
    fill(sEl, sList, "s");

    modal.querySelector("#cancelBtn").onclick = () => {
      modal.style.display = "none";
    };

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
        if (selectedSF.length > 0) {
          // essai batch
          const r = await fetch("/savoir_faires/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ activity_id: activityId, savoir_faires: selectedSF }),
          });
          if (!r.ok) {
            // fallback unitaire
            await Promise.all(selectedSF.map(desc =>
              fetch("/savoir_faires/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ activity_id: activityId, description: desc }),
              })
            ));
          }
        }

        if (selectedS.length > 0) {
          await Promise.all(selectedS.map(desc =>
            fetch("/savoirs/add", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ activity_id: activityId, description: desc }),
            })
          ));
        }

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
