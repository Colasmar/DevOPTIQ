// Code/static/js/propose_aptitudes.js
(function () {
  const API_PROPOSE = "/propose_aptitudes/propose";
  const API_ADD     = "/aptitudes/add";
  const API_RENDER  = (activityId) => `/aptitudes/${activityId}/render`;

  const safeShowSpinner = () => (typeof showSpinner === "function" ? showSpinner() : void 0);
  const safeHideSpinner = () => (typeof hideSpinner === "function" ? hideSpinner()  : void 0);

  function $(sel, ctx = document) { return ctx.querySelector(sel); }
  function $all(sel, ctx = document) { return Array.from(ctx.querySelectorAll(sel)); }

  // fetch avec timeout (par défaut 60s) pour éviter attente infinie, mais laisser le temps d'une analyse
  async function fetchWithTimeout(url, opts = {}, timeoutMs = 60000) {
    const ctl = new AbortController();
    const id  = setTimeout(() => ctl.abort(), timeoutMs);
    try {
      const resp = await fetch(url, { signal: ctl.signal, ...opts });
      return resp;
    } finally {
      clearTimeout(id);
    }
  }

  // -------- Parsing des propositions (version anti-titres, anti-contexte) --------
// Ne garde QUE les lignes d'aptitudes de la "Section A", jamais les titres/groupes.
function parseAptitudesFromText(input) {
  const groups = [];
  if (!input) return groups;

  // Si l’API renvoie déjà un tableau -> groupe unique
  if (Array.isArray(input)) {
    const cleaned = input.map(s => (s || "").toString().trim()).filter(Boolean);
    if (cleaned.length) groups.push({ group: "Aptitudes", items: cleaned });
    return groups;
  }

  // Normalisation de base
  const norm = String(input)
    // remplacer tirets longs/means par un simple "-"
    .replace(/[–—]/g, "-")
    // enlever doubles espaces
    .replace(/[ \t]+/g, " ");

  // Isoler Section A uniquement
  const idxA = norm.toLowerCase().indexOf("section a");
  if (idxA === -1) return groups;
  let sectionA = norm.slice(idxA);
  const idxB = sectionA.toLowerCase().indexOf("section b");
  if (idxB !== -1) sectionA = sectionA.slice(0, idxB);

  const lines = sectionA
    .split(/\r?\n/)
    .map(l => l.trim())
    .filter(Boolean);

  // Helpers
  const stripMd = (s) =>
    s.replace(/\*\*/g, "")       // gras
     .replace(/`/g, "")          // code
     .replace(/\s+/g, " ")
     .trim();

  const isSectionHeader = (l) => /^#{1,6}\s*section\s+[ab]\b/i.test(stripMd(l));
  const isExample       = (l) => /^(\*{0,2})?exemple\b/i.test(stripMd(l));

  // Titres groupe type: "1. **Aptitudes physiques :**" (ou sans "**")
  const isGroupHeader = (l) => {
    const s = stripMd(l);
    // commence par chiffre + point
    if (!/^\d+\.\s+/.test(s)) return false;
    // ne doit PAS contenir d'info après le ":" (ou pas de ":" du tout)
    // ex: "1. Aptitudes physiques :" ou "1. Aptitudes physiques"
    const afterNum = s.replace(/^\d+\.\s+/, "");
    // on considère que c'est un header si le libellé commence par "Aptitudes"
    if (!/^Aptitudes\b/i.test(afterNum)) return false;
    // s'il y a un ":", il ne doit rien y avoir d'utile après
    const parts = afterNum.split(":");
    return parts.length === 1 || (parts.length === 2 && parts[1].trim() === "");
  };

  // Une ligne sélectionnable = "libellé : valeur ..." qui:
  // - n'est pas une section, ni un exemple
  // - n'est pas un header de groupe
  // - n'est pas une ligne de contexte "Aptitudes ... :" (pas d'info après le ':')
  // - ne commence pas par "<num>. " (titres numérotés)
  // - a bien du texte avant ET après le ":" (pas juste un libellé)
  const isCandidate = (l) => {
    const s = stripMd(l);
    if (isSectionHeader(l) || isExample(l) || isGroupHeader(l)) return false;
    if (/^\d+\.\s+/.test(s)) return false;                // titres numérotés
    if (!s.includes(":")) return false;                   // doit contenir un ':'
    const [left, right] = s.split(/:(.+)/).map(x => (x || "").trim());
    if (!left || !right) return false;                    // rien après ':'
    if (/^Aptitudes\b/i.test(left)) return false;         // contexte "Aptitudes … :"
    return true;
  };

  let currentGroup = null;

  for (const raw of lines) {
    // ignorer sections/exemples
    if (isSectionHeader(raw) || isExample(raw)) continue;

    // en-tête de groupe ?
    if (isGroupHeader(raw)) {
      const name = stripMd(raw)
        .replace(/^\d+\.\s+/, "")
        .replace(/\s*:$/, "")
        .trim(); // ex: "Aptitudes physiques"
      currentGroup = { group: name, items: [] };
      groups.push(currentGroup);
      continue;
    }

    // item d’aptitude
    if (isCandidate(raw)) {
      const label = stripMd(raw).replace(/^[-•]\s*/, "").trim();
      if (!label) continue;
      if (!currentGroup) currentGroup = { group: "Aptitudes", items: [] }, groups.push(currentGroup);
      if (!currentGroup.items.includes(label)) currentGroup.items.push(label);
    }
  }

  // supprimer groupes vides
  return groups.filter(g => g.items.length > 0);
}



  // -------- UI modale (overlay inline, pas de CSS externe requis) --------
  function ensureModal() {
    let modal = $("#proposeAptitudesModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "proposeAptitudesModal";
      Object.assign(modal.style, {
        position: "fixed",
        inset: "0",
        background: "rgba(0,0,0,0.35)",
        zIndex: "9999",
        display: "none",
      });

      const dialog = document.createElement("div");
      Object.assign(dialog.style, {
        position: "absolute",
        left: "50%",
        top: "8%",
        transform: "translateX(-50%)",
        width: "min(900px, 92vw)",
        maxHeight: "84vh",
        overflow: "auto",
        background: "#fff",
        border: "1px solid #aaa",
        borderRadius: "10px",
        boxShadow: "0 10px 25px rgba(0,0,0,0.15)",
        padding: "16px",
      });
      dialog.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <h3 style="margin:0;">Propositions d'aptitudes</h3>
          <button id="apt-close" title="Fermer" style="font-size:20px; line-height:1;">&times;</button>
        </div>
        <div id="aptitudes-groups"></div>
        <div style="margin-top:16px; display:flex; gap:10px; justify-content:space-between; align-items:center;">
          <div>
            <label><input type="checkbox" id="apt-select-all"> Tout sélectionner</label>
          </div>
          <div>
            <button id="btn-validate-aptitudes" class="btn btn-primary">Enregistrer</button>
            <button id="btn-cancel-aptitudes" class="btn">Annuler</button>
          </div>
        </div>
      `;
      modal.appendChild(dialog);
      document.body.appendChild(modal);

      $("#apt-close", modal).onclick = () => hideModal();
      $("#btn-cancel-aptitudes", modal).onclick = () => hideModal();
      modal.addEventListener("click", (e) => { if (e.target === modal) hideModal(); });
      $("#apt-select-all", modal).addEventListener("change", (e) => {
        const checked = e.target.checked;
        $all('input[type="checkbox"][data-apt="1"]', modal).forEach(cb => cb.checked = checked);
      });
    }
    return modal;
  }
  function showModal() { const m = ensureModal(); m.style.display = "block"; }
  function hideModal() { const m = $("#proposeAptitudesModal"); if (m) m.style.display = "none"; }

  function renderGroupsInModal(groups) {
    const container = $("#aptitudes-groups");
    container.innerHTML = "";

    if (!groups.length) {
      container.innerHTML = `<p>Aucune aptitude sélectionnable n'a été trouvée dans la Section A.</p>`;
      return;
    }

    groups.forEach(g => {
      const block = document.createElement("div");
      block.style.marginBottom = "14px";
      const title = document.createElement("h4");
      title.textContent = g.group;
      title.style.margin = "6px 0 8px";
      block.appendChild(title);

      const ul = document.createElement("ul");
      ul.style.listStyle = "none";
      ul.style.paddingLeft = "0";
      g.items.forEach(item => {
        const li = document.createElement("li");
        li.style.marginBottom = "6px";
        li.innerHTML = `
          <label>
            <input type="checkbox" data-apt="1" value="${item}">
            ${item}
          </label>`;
        ul.appendChild(li);
      });
      block.appendChild(ul);
      container.appendChild(block);
    });
  }

  // -------- Flux principal --------
  async function showProposedAptitudes(activityId) {
    safeShowSpinner();
    try {
      const modal = ensureModal();
      $("#aptitudes-groups", modal).innerHTML = "<p>Chargement...</p>";
      showModal();

      // (Optionnel) on récupère les détails d'activité, comme pour les autres propositions
      let activityData = null;
      try {
        const rd = await fetchWithTimeout(`/activities/${activityId}/details`, {}, 15000);
        if (rd.ok) activityData = await rd.json();
      } catch (e) {
        // pas bloquant : si on ne récupère pas les détails, on enverra juste l'ID
        console.warn("Récupération détails activité ignorée :", e);
      }

      // On envoie l'ID + (si dispo) les détails d’activité
      const proposeBody = activityData ? { activity_id: activityId, ...activityData }
                                       : { activity_id: activityId };

      let r;
      try {
        r = await fetchWithTimeout(API_PROPOSE, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(proposeBody)
        }, 60000);
      } catch (e) {
        if (e?.name === "AbortError") {
          throw new Error("Temps dépassé (60s) pour la génération des aptitudes.");
        }
        throw e;
      }

      if (!r.ok) throw new Error(`HTTP ${r.status}`);

      let data;
      try { data = await r.json(); }
      catch { throw new Error("Réponse invalide du serveur (JSON attendu)."); }

      const groups = parseAptitudesFromText(data.proposals);
      renderGroupsInModal(groups);

      // Enregistrer (insertion unitaire { activity_id, description })
      $("#btn-validate-aptitudes", modal).onclick = async () => {
        const selected = $all('input[type="checkbox"][data-apt="1"]:checked', modal).map(cb => cb.value);
        if (!selected.length) {
          alert("Sélectionne au moins une aptitude.");
          return;
        }

        safeShowSpinner();
        try {
          await Promise.all(selected.map(desc =>
            fetchWithTimeout(API_ADD, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ activity_id: activityId, description: desc })
            }, 60000).then(resp => {
              if (!resp.ok) return resp.text().then(t => { throw new Error(`HTTP ${resp.status} ${t||""}`); });
            })
          ));

          // Refresh du bloc aptitudes si un conteneur est prévu
          try {
            const r2 = await fetchWithTimeout(API_RENDER(activityId), {}, 15000);
            if (r2.ok) {
              const html = await r2.text();
              const container = document.getElementById(`aptitudes-container-${activityId}`)
                             || document.querySelector(`[data-aptitudes-container="${activityId}"]`);
              if (container) container.innerHTML = html;
            }
          } catch (e) {
            console.warn("Refresh aptitudes non appliqué :", e);
          }

          hideModal();
        } catch (e) {
          console.error("Erreur lors de l'ajout des aptitudes :", e);
          alert(e.message || "Erreur lors de l'ajout des aptitudes.");
        } finally {
          safeHideSpinner();
        }
      };

    } catch (err) {
      console.error("Erreur showProposedAptitudes:", err);
      alert(err.message || "Erreur lors de la proposition d'aptitudes.");
    } finally {
      safeHideSpinner();
    }
  }

  // Aliases globaux (compat onclick)
  window.showProposedAptitudes = showProposedAptitudes;
  window.openProposeAptitudes  = showProposedAptitudes;
  window.proposeAptitudes      = showProposedAptitudes;

  // Délégation (si utilisation data-attributes)
  document.addEventListener("click", (e) => {
    const btn = e.target.closest('[data-action="propose-aptitudes"]');
    if (btn) {
      const activityId = parseInt(btn.dataset.activityId, 10);
      if (!isNaN(activityId)) showProposedAptitudes(activityId);
    }
  });
})();
