// Front ROME 4.0 — pagination serveur + mini spinners (global + dans les boutons)
(() => {
  const select = document.getElementById('user-select');
  const fullList = document.getElementById('full-list');
  const partialList = document.getElementById('partial-list');
  const alertBox = document.getElementById('alert');
  const spinner = document.getElementById('spinner');
  const baseUrl = document.getElementById('base-url');

  const fullCount = document.getElementById('full-count');
  const partialCount = document.getElementById('partial-count');

  const fullMoreBtn = document.getElementById('full-more');
  const partialMoreBtn = document.getElementById('partial-more');

  // Chargement initial 30, puis +20
  const INITIAL_LIMIT = 30;
  const MORE_CHUNK = 20;

  let currentUserId = null;
  let fullOffset = 0;
  let partialOffset = 0;
  let fullTotal = 0;
  let partialTotal = 0;

  function showAlert(msg) {
    if (!alertBox) return;
    alertBox.textContent = msg || '';
    alertBox.style.display = msg ? 'block' : 'none';
  }

  // Spinner global (haut de page)
  function setLoading(isLoading) {
    if (spinner) spinner.classList.toggle('show', isLoading);
  }

  // Spinner sur un bouton donné (ajoute une roue dans le bouton)
  function setButtonLoading(btn, loading) {
    if (!btn) return;
    if (loading) {
      btn.classList.add('is-loading');
      btn.setAttribute('disabled', 'disabled');
    } else {
      btn.classList.remove('is-loading');
      btn.removeAttribute('disabled');
    }
  }

  function clearLists() {
    if (fullList) fullList.innerHTML = '';
    if (partialList) partialList.innerHTML = '';
    if (fullCount) fullCount.textContent = '0/0';
    if (partialCount) partialCount.textContent = '0/0';
    fullOffset = 0; partialOffset = 0;
    fullTotal = 0; partialTotal = 0;
    if (fullMoreBtn) fullMoreBtn.style.display = 'none';
    if (partialMoreBtn) partialMoreBtn.style.display = 'none';
  }

  function scoreClass(p) {
    if (p >= 100) return 'badge-green';
    if (p >= 60) return 'badge-lime';
    if (p >= 30) return 'badge-amber';
    if (p > 0)   return 'badge-orange';
    return 'badge-gray';
  }

  function makeList(items, kind) {
    const frag = document.createDocumentFragment();

    items.forEach(item => {
      const li = document.createElement('li');
      li.className = 'job-card';

      const header = document.createElement('div');
      header.className = 'job-row';

      const title = document.createElement('strong');
      title.className = 'job-title';
      title.textContent = `${item.label || 'Métier'}${item.code ? ' (' + item.code + ')' : ''}`;

      const score = document.createElement('span');
      score.className = `badge ${scoreClass(item.score)}`;
      score.textContent = `${item.score}%`;

      header.appendChild(title);
      header.appendChild(score);

      li.appendChild(header);

      // Bandeau métriques
      const metrics = document.createElement('div');
      metrics.className = 'metrics';
      metrics.innerHTML = `<span class="met ok">En commun: <b>${item.owned_count ?? (item.owned?.length || 0)}</b></span>
                           <span class="met miss">À développer: <b>${item.missing_count ?? (item.missing?.length || 0)}</b></span>
                           <span class="met tot">Total: <b>${item.total ?? ((item.owned?.length||0)+(item.missing?.length||0))}</b></span>`;
      li.appendChild(metrics);

      // Détails (en commun / à développer)
      const details = document.createElement('div');
      details.className = 'lists-wrap';

      if (Array.isArray(item.owned) && item.owned.length) {
        const d1 = document.createElement('details');
        d1.className = 'job-details owned';
        const s1 = document.createElement('summary');
        s1.textContent = `En commun (${item.owned.length})`;
        d1.appendChild(s1);

        const ul1 = document.createElement('ul');
        ul1.className = 'owned-list';
        item.owned.slice(0, 10).forEach(v => {
          const li1 = document.createElement('li');
          li1.textContent = v;
          ul1.appendChild(li1);
        });
        if (item.owned.length > 10) {
          const more = document.createElement('em');
          more.textContent = `… et ${item.owned.length - 10} autres`;
          d1.appendChild(more);
        }
        d1.appendChild(ul1);
        details.appendChild(d1);
      }

      if (Array.isArray(item.missing) && item.missing.length) {
        const d2 = document.createElement('details');
        d2.className = 'job-details missing';
        const s2 = document.createElement('summary');
        s2.textContent = `À développer (${item.missing.length})`;
        d2.appendChild(s2);

        const ul2 = document.createElement('ul');
        ul2.className = 'missing-list';
        item.missing.slice(0, 10).forEach(v => {
          const li2 = document.createElement('li');
          li2.textContent = v;
          ul2.appendChild(li2);
        });
        if (item.missing.length > 10) {
          const more = document.createElement('em');
          more.textContent = `… et ${item.missing.length - 10} autres`;
          d2.appendChild(more);
        }
        d2.appendChild(ul2);
        details.appendChild(d2);
      }

      li.appendChild(details);

      if (kind === 'partial') {
        li.classList.add('is-partial');
      }

      frag.appendChild(li);
    });

    return frag;
  }

  function updateCounters() {
    if (fullCount)   fullCount.textContent   = `${Math.min(fullOffset, fullTotal)}/${fullTotal}`;
    if (partialCount) partialCount.textContent = `${Math.min(partialOffset, partialTotal)}/${partialTotal}`;
  }

  async function fetchPage({ userId, fullLim = 0, fullOff = 0, partialLim = 0, partialOff = 0 }) {
    const url = new URL(window.location.origin + `/projection_metier/analyze_user/${encodeURIComponent(userId)}`);
    if (fullLim !== null)    url.searchParams.set('full_limit', fullLim);
    if (fullOff !== null)    url.searchParams.set('full_offset', fullOff);
    if (partialLim !== null) url.searchParams.set('partial_limit', partialLim);
    if (partialOff !== null) url.searchParams.set('partial_offset', partialOff);

    const res = await fetch(url.toString(), { headers: { 'Accept': 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function initialLoad(userId) {
    setLoading(true);         // spinner global ON
    showAlert('');
    clearLists();
    try {
      const data = await fetchPage({
        userId,
        fullLim: INITIAL_LIMIT, fullOff: 0,
        partialLim: INITIAL_LIMIT, partialOff: 0
      });

      // Full
      const full = Array.isArray(data.full) ? data.full : [];
      fullTotal = data?.page?.full?.total || full.length;
      fullOffset = (data?.page?.full?.offset || 0) + full.length;

      if (full.length) {
        fullList.appendChild(makeList(full, 'full'));
      }
      if (data?.page?.full?.has_more && fullMoreBtn) {
        fullMoreBtn.style.display = 'inline-flex';
      } else if (fullMoreBtn) {
        fullMoreBtn.style.display = 'none';
      }

      // Partial
      const partial = Array.isArray(data.partial) ? data.partial : [];
      partialTotal = data?.page?.partial?.total || partial.length;
      partialOffset = (data?.page?.partial?.offset || 0) + partial.length;

      if (partial.length) {
        partialList.appendChild(makeList(partial, 'partial'));
      }
      if (data?.page?.partial?.has_more && partialMoreBtn) {
        partialMoreBtn.style.display = 'inline-flex';
      } else if (partialMoreBtn) {
        partialMoreBtn.style.display = 'none';
      }

      if (fullTotal === 0 && partialTotal === 0) {
        showAlert("Aucun métier trouvé avec les données actuelles.");
      }
      updateCounters();
    } catch (e) {
      console.error(e);
      showAlert("Une erreur est survenue lors de l'analyse.");
    } finally {
      setLoading(false);      // spinner global OFF
    }
  }

  async function loadMore(kind) {
    if (!currentUserId) return;
    // Spinner bouton ON
    if (kind === 'full') setButtonLoading(fullMoreBtn, true);
    else setButtonLoading(partialMoreBtn, true);

    try {
      let params;
      if (kind === 'full') {
        params = {
          userId: currentUserId,
          fullLim: MORE_CHUNK, fullOff: fullOffset,
          partialLim: 0, partialOff: 0
        };
      } else {
        params = {
          userId: currentUserId,
          fullLim: 0, fullOff: 0,
          partialLim: MORE_CHUNK, partialOff: partialOffset
        };
      }
      const data = await fetchPage(params);

      if (kind === 'full') {
        const arr = Array.isArray(data.full) ? data.full : [];
        if (arr.length) {
          fullList.appendChild(makeList(arr, 'full'));
          fullOffset += arr.length;
        }
        if (!(data?.page?.full?.has_more) && fullMoreBtn) fullMoreBtn.style.display = 'none';
      } else {
        const arr = Array.isArray(data.partial) ? data.partial : [];
        if (arr.length) {
          partialList.appendChild(makeList(arr, 'partial'));
          partialOffset += arr.length;
        }
        if (!(data?.page?.partial?.has_more) && partialMoreBtn) partialMoreBtn.style.display = 'none';
      }

      updateCounters();
    } catch (e) {
      console.error(e);
      showAlert("Impossible de charger plus d'éléments.");
    } finally {
      // Spinner bouton OFF
      if (kind === 'full') setButtonLoading(fullMoreBtn, false);
      else setButtonLoading(partialMoreBtn, false);
    }
  }

  if (fullMoreBtn) fullMoreBtn.addEventListener('click', () => loadMore('full'));
  if (partialMoreBtn) partialMoreBtn.addEventListener('click', () => loadMore('partial'));

  if (select) {
    select.addEventListener('change', (e) => {
      const val = e.target.value;
      if (!val || val === '0') {
        currentUserId = null;
        clearLists();
        showAlert('');
        return;
      }
      currentUserId = val;
      initialLoad(currentUserId);
    });
  }

  // Optionnel: affiche la base URL (si serveur l’expose via /_config)
  (async () => {
    try {
      const r = await fetch('/projection_metier/_config');
      if (r.ok) {
        const j = await r.json();
        if (baseUrl) baseUrl.textContent = j.ROME_BASE_URL || '';
      }
    } catch {}
  })();
})();
