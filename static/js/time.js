// Code/static/js/time.js
(() => {
  const $ = (s, c=document) => c.querySelector(s);
  const $$ = (s, c=document) => Array.from(c.querySelectorAll(s));
  const v = (sel) => $(sel)?.value;
  const n = (sel) => parseFloat(v(sel) || "0");
  const confirmDel = (msg)=> window.confirm(msg || 'Confirmer la suppression ?');

  let currentActivityEditId = null;
  let calendarParams = {hours_per_day:7, days_per_week:5, weeks_per_year:47};

  // ---------- Tabs ----------
  $$('.tab').forEach(b=>{
    b.onclick = () => {
      $$('.tab').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      const which = b.dataset.tab;
      $$('.tab-panel').forEach(p=>p.classList.remove('active'));
      $('#tab-' + which).classList.add('active');
    }
  });
  $$('.subtab').forEach(b=>{
    b.onclick = () => {
      $$('.subtab').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      const which = b.dataset.subtab;
      $$('.subtab-panel').forEach(p=>p.classList.remove('active'));
      $('#subtab-' + which).classList.add('active');
    }
  });

  // ---------- Utils ----------
  function toMinutes(qty, unit){
    const k={minutes:1, heures:60, jours:1440};
    return (parseFloat(qty||0)*(k[(unit||'minutes').toLowerCase()]||1));
  }
  function unitSelect(){
    const s=document.createElement('select');
    s.className='input';
    s.innerHTML=`<option>minutes</option><option>heures</option><option>jours</option>`;
    return s;
  }

  async function loadCalendarParams(){
    try{
      const r = await fetch('/temps/api/calendar_params');
      const j = await r.json();
      if (j.ok) calendarParams = {hours_per_day:j.hours_per_day, days_per_week:j.days_per_week, weeks_per_year:j.weeks_per_year};
    }catch(_){}
  }

  // =====================================================
  // ===============  FAIBLESSE (SOUS-ONGLET) ============
  // =====================================================
  const fwGlobal = $('#fw-global');
  const fwTasks = $('#fw-tasks');
  const fwTaskBody = $('#fw-task-rows');
  const fwTaskSum = $('#fw-task-sum');

  function toggleFwMode() {
    const mode = $$('input[name="fw-mode"]:checked')[0].value;
    if (mode === 'tasks') {
      fwGlobal?.classList.remove('hidden');
      fwTasks?.classList.remove('hidden');
      $('#fw-dur')?.setAttribute('readonly', 'readonly');
    } else {
      fwTasks?.classList.add('hidden');
      $('#fw-dur')?.removeAttribute('readonly');
    }
  }
  $$('input[name="fw-mode"]').forEach(r => r.onchange = toggleFwMode);

  function activitySelectFromTemplate(selectId='#act-activity'){
    const s=document.createElement('select');
    s.className='input';
    const base = $$(selectId+' option');
    s.innerHTML = base.map(o=>`<option value="${o.value}">${o.textContent}</option>`).join('');
    return s;
  }

  async function refreshWeaknessDefaults() {
    const actSel = $('#fw-activity');
    if (!actSel) return;
    const act = actSel.value;
    const r = await fetch(`/temps/api/activity_defaults/${act}`);
    const j = await r.json();
    $('#fw-dur').value = j.duration_minutes ?? 0;
    $('#fw-dur-unit').value = 'minutes';
    $('#fw-del').value = j.delay_minutes ?? 0;
    $('#fw-del-unit').value = 'minutes';
    fwTaskBody.innerHTML = (j.tasks||[]).map(t=>{
      return `<tr data-task="${t.id}">
        <td>${t.name}</td>
        <td><input type="number" class="input t-dur" step="0.1" min="0" value="${t.duration_minutes??0}" /></td>
        <td class="td-unit"></td>
        <td><input type="number" class="input t-del" step="0.1" min="0" value="${t.delay_minutes??0}" /></td>
        <td class="td-dunit"></td>
      </tr>`;
    }).join('');
    $$('#fw-task-rows tr').forEach(tr=>{
      const u1 = unitSelect(); tr.querySelector('.td-unit').appendChild(u1); u1.value='minutes';
      const u2 = unitSelect(); tr.querySelector('.td-dunit').appendChild(u2); u2.value='minutes';
    });
    recalcTaskSum();
  }

  function recalcTaskSum() {
    if (!fwTaskBody) return;
    let sum = 0;
    $$('#fw-task-rows tr').forEach(tr=>{
      const d = parseFloat(tr.querySelector('.t-dur').value || '0');
      const u = tr.querySelector('.td-unit select').value;
      sum += toMinutes(d, u);
    });
    if (fwTaskSum) fwTaskSum.textContent = Math.round(sum);
    if ($('#fw-dur')) { $('#fw-dur').value = Math.round(sum); $('#fw-dur-unit').value = 'minutes'; }
  }

  $('#fw-activity')?.addEventListener('change', refreshWeaknessDefaults);
  $('#fw-tasks')?.addEventListener('input', (e)=> {
    if (e.target.classList.contains('t-dur')) recalcTaskSum();
  });
  toggleFwMode();

  async function sendWeakness(save=false){
    const mode = $$('input[name="fw-mode"]:checked')[0].value;
    const payload = {
      mode,
      activity_id: parseInt($('#fw-activity').value,10),
      recurrence: $('#fw-rec').value,
      frequency: parseInt($('#fw-freq').value || '1', 10),
      weakness: $('#fw-k').value,
      L_work_added: n('#fw-l'), L_unit: v('#fw-l-unit'),
      M_wait_added: n('#fw-m'), M_unit: v('#fw-m-unit'),
      N_prob_denom: parseInt(n('#fw-n') || 1, 10),
      delay_std: n('#fw-del'), delay_unit: v('#fw-del-unit'),
      save
    };
    if (mode === 'tasks') {
      payload.tasks = $$('#fw-task-rows tr').map(tr => ({
        task_id: parseInt(tr.dataset.task,10),
        duration_std: parseFloat(tr.querySelector('.t-dur').value || '0'),
        duration_unit: tr.querySelector('.td-unit select').value,
        delay_std: parseFloat(tr.querySelector('.t-del').value || '0'),
        delay_unit: tr.querySelector('.td-dunit select').value
      }));
    } else {
      payload.duration_std = n('#fw-dur');
      payload.duration_unit = v('#fw-dur-unit');
    }

    const r = await fetch('/temps/api/weakness', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    const j = await r.json();
    if (!j.ok) return alert('Erreur de calcul/enregistrement');

    const m = j.calc || {};
    ['S','T','U','V','W','X','Y','Z','AA'].forEach(k=>{
      const val = m[k] != null ? Math.round(m[k]) : '—';
      const el = document.getElementById(k);
      if (el) el.textContent = val;
    });
    if (save) alert('Analyse faiblesse enregistrée.');
  }

  $('#btn-fw-calc')?.addEventListener('click', ()=> sendWeakness(false));
  $('#btn-fw-save')?.addEventListener('click', ()=> sendWeakness(true));

  // =====================================================
  // =================== CHARGES - PROJET ================
  // =====================================================
  const projectBody = $('#project-rows');
  const addLineBtn = $('#btn-add-line'), saveProjBtn = $('#btn-save-project');

  function activitySelectFromAll(){
    const s=document.createElement('select');
    s.className='input';
    s.innerHTML = [...$$('#act-activity option')].map(o=>`<option value="${o.value}">${o.textContent}</option>`).join('');
    return s;
  }

  function addProjectRow() {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="cell-act"></td>
      <td><input type="number" min="0" step="0.1" class="input cell-dur" /></td>
      <td class="cell-du"></td>
      <td><input type="number" min="0" step="0.1" class="input cell-del" /></td>
      <td class="cell-deu"></td>
      <td><input type="number" min="1" step="1" class="input cell-nbp" value="1" /></td>
      <td class="cell-chg">0</td>
      <td><button class="icon-btn danger btn-del" title="Supprimer">🗑</button></td>
    `;
    const act = activitySelectFromAll(); tr.querySelector('.cell-act').appendChild(act);
    const du = unitSelect(); tr.querySelector('.cell-du').appendChild(du);
    const deu = unitSelect(); tr.querySelector('.cell-deu').appendChild(deu);

    async function prefillDefaults(){
      const id = act.value;
      const r = await fetch(`/temps/api/activity_defaults/${id}`);
      const j = await r.json();
      tr.querySelector('.cell-dur').value = j.duration_minutes ?? 0;
      tr.querySelector('.cell-del').value = j.delay_minutes ?? 0;
      du.value = 'minutes'; deu.value = 'minutes';
      recalc();
    }
    act.onchange = prefillDefaults;
    prefillDefaults();

    function recalc(){
      const d = parseFloat(tr.querySelector('.cell-dur').value || '0');
      const duV = du.value;
      const nbp = parseInt(tr.querySelector('.cell-nbp').value || '1', 10);
      const durMin = toMinutes(d, duV);
      const charge = durMin * Math.max(1, nbp);
      tr.querySelector('.cell-chg').textContent = Math.round(charge);
      recalcProjectTotals();
    }
    tr.addEventListener('input', recalc);
    tr.querySelector('.btn-del').onclick = ()=> { tr.remove(); recalcProjectTotals(); };
    projectBody?.appendChild(tr);
  }

  function updateKpi(id, val){ const el = document.getElementById(id); if (el) el.textContent = String(val); }

  function recalcProjectTotals() {
    const rows = $$('#project-rows tr');
    let nb = 0, sumD = 0, sumDelay = 0, sumC = 0;
    rows.forEach(tr=>{
      nb++;
      const d = parseFloat(tr.querySelector('.cell-dur').value || '0');
      const du = tr.querySelector('.cell-du select').value;
      const del = parseFloat(tr.querySelector('.cell-del').value || '0');
      const delu = tr.querySelector('.cell-deu select').value;
      sumD += toMinutes(d, du);
      sumDelay += toMinutes(del, delu);
      sumC += parseFloat(tr.querySelector('.cell-chg').textContent || '0');
    });
    const avgDelay = nb ? Math.round(sumDelay/nb) : 0;

    updateKpi('kpi-proj-nb', nb);
    updateKpi('kpi-proj-dur', Math.round(sumD));
    updateKpi('kpi-proj-del', avgDelay);
    updateKpi('kpi-proj-charge', Math.round(sumC));
  }

  addLineBtn?.addEventListener('click', ()=> addProjectRow());
  saveProjBtn?.addEventListener('click', async ()=>{
    const rows = $$('#project-rows tr').map(tr=>({
      activity_id: parseInt(tr.querySelector('.cell-act select').value, 10),
      duration: parseFloat(tr.querySelector('.cell-dur').value || '0'),
      duration_unit: tr.querySelector('.cell-du select').value,
      delay: parseFloat(tr.querySelector('.cell-del').value || '0'),
      delay_unit: tr.querySelector('.cell-deu select').value,
      nb_people: parseInt(tr.querySelector('.cell-nbp').value || '1', 10)
    }));
    const payload = { name: $('#project-name').value || 'Projet', lines: rows };
    const r = await fetch('/temps/api/project', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    const j = await r.json();
    if (j.ok) {
      alert(`Projet enregistré (id ${j.project_id})`);
      projectBody.innerHTML = '';
      $('#project-name').value = '';
      await refreshProjectList();
      addProjectRow(); recalcProjectTotals();
    } else {
      alert('Erreur d’enregistrement');
    }
  });

  async function refreshProjectList(){
    const list = $('#project-list');
    if (!list) return;
    list.innerHTML = '<div class="muted">Chargement…</div>';
    const r = await fetch('/temps/api/projects');
    const j = await r.json();
    if (!j.ok) { list.innerHTML = '<div class="muted">Erreur de chargement</div>'; return; }
    if (!j.projects.length) { list.innerHTML = '<div class="muted">Aucun projet enregistré.</div>'; return; }

    list.innerHTML = j.projects.map(p => `
      <div class="acc-item" data-id="${p.id}">
        <div class="acc-head">
          <div class="acc-title">
            <b class="proj-name">${p.name || 'Sans titre'}</b>
            <input class="proj-name-input hidden input" value="${(p.name || '').replace(/"/g,'&quot;')}" />
            <span class="badge">${p.nb_activites} act.</span>
            <span class="badge">${Math.round(p.charge_globale_minutes)} min</span>
          </div>
          <div class="acc-meta">Durée ${Math.round(p.tot_duree_minutes)} min · Délai ${Math.round(p.delais_optimum_minutes)} min</div>
          <div class="acc-actions">
            <button class="icon-btn edit-proj" title="Renommer">✎</button>
            <button class="icon-btn success save-proj hidden" title="Enregistrer">✔</button>
            <button class="icon-btn cancel-proj hidden" title="Annuler">✖</button>
            <button class="icon-btn danger del-proj" title="Supprimer">🗑</button>
          </div>
          <div class="acc-toggle">▼</div>
        </div>
        <div class="acc-body"></div>
      </div>
    `).join('');

    $$('#project-list .acc-item').forEach(item=>{
      const id = item.dataset.id;
      const head = item.querySelector('.acc-head');
      const nameEl = item.querySelector('.proj-name');
      const inputEl = item.querySelector('.proj-name-input');
      const editBtn = item.querySelector('.edit-proj');
      const saveBtn = item.querySelector('.save-proj');
      const cancelBtn = item.querySelector('.cancel-proj');

      function setEditing(on){
        if (on){
          inputEl.value = nameEl.textContent.trim();
          nameEl.classList.add('hidden');
          inputEl.classList.remove('hidden');
          editBtn.classList.add('hidden');
          saveBtn.classList.remove('hidden');
          cancelBtn.classList.remove('hidden');
          inputEl.focus(); inputEl.select();
        } else {
          nameEl.classList.remove('hidden');
          inputEl.classList.add('hidden');
          editBtn.classList.remove('hidden');
          saveBtn.classList.add('hidden');
          cancelBtn.classList.add('hidden');
        }
      }

      editBtn.onclick = (e)=>{ e.stopPropagation(); setEditing(true); };
      cancelBtn.onclick = (e)=>{ e.stopPropagation(); setEditing(false); };
      saveBtn.onclick = async (e)=>{
        e.stopPropagation();
        const newName = inputEl.value.trim();
        const r = await fetch(`/temps/api/project/${id}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name:newName})});
        const j = await r.json();
        if (j.ok) { nameEl.textContent = j.name; setEditing(false); }
        else alert('Erreur de renommage');
      };

      head.onclick = async (ev)=>{
        if (ev.target.closest('.acc-actions')) return;
        const body = item.querySelector('.acc-body');
        const opened = item.classList.toggle('open');
        if (opened) {
          const rr = await fetch(`/temps/api/project/${id}`);
          const jj = await rr.json();
          if (!jj.ok) { body.innerHTML = '<div class="muted">Erreur</div>'; return; }
          const rows = jj.lines || [];
          body.innerHTML = `
            <div class="table-wrap">
              <table class="grid">
                <colgroup>
                  <col class="col-activity"><col class="col-num"><col class="col-num"><col class="col-num-xs"><col class="col-num"><col class="col-actions">
                </colgroup>
                <thead>
                  <tr>
                    <th>Activité</th><th>Durée (min)</th><th>Délai (min)</th><th>Nb</th><th>Charge (min)</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  ${rows.map(r => `<tr data-line="${r.id}">
                    <td>${r.activity}</td>
                    <td>${Math.round(r.duration_minutes)}</td>
                    <td>${Math.round(r.delay_minutes)}</td>
                    <td>${r.nb_people}</td>
                    <td>${Math.round(r.charge)}</td>
                    <td><button class="icon-btn danger del-line" title="Supprimer la ligne">🗑</button></td>
                  </tr>`).join('')}
                </tbody>
              </table>
            </div>
          `;
          body.querySelectorAll('.del-line').forEach(btn=>{
            btn.onclick = async ()=>{
              const tr = btn.closest('tr');
              const lineId = tr.dataset.line;
              if (!confirmDel('Supprimer cette activité du projet ?')) return;
              const rr2 = await fetch(`/temps/api/project_line/${lineId}`, {method:'DELETE'});
              const resp = await rr2.json();
              if (resp.ok) {
                if (resp.project_deleted) {
                  item.remove();
                  if (!$('#project-list').children.length) $('#project-list').innerHTML='<div class="muted">Aucun projet enregistré.</div>';
                } else {
                  item.classList.remove('open'); head.click();
                }
              } else alert('Suppression impossible');
            };
          });
        }
      };

      item.querySelector('.del-proj').onclick = async (e)=>{
        e.stopPropagation();
        if (!confirmDel('Supprimer ce projet ?')) return;
        const r = await fetch(`/temps/api/project/${id}`, {method:'DELETE'});
        const j = await r.json();
        if (j.ok) {
          item.remove();
          if (!$('#project-list').children.length) $('#project-list').innerHTML='<div class="muted">Aucun projet enregistré.</div>';
        } else alert('Erreur de suppression');
      };
    });
  }

  // =====================================================
  // =================== CHARGES - ACTIVITÉ ==============
  // =====================================================
  async function refreshActivityDefaults() {
    const act = $('#act-activity')?.value;
    if (!act) return;
    const r = await fetch(`/temps/api/activity_defaults/${act}`);
    const j = await r.json();
    $('#act-duration').value = j.duration_minutes ?? 0;
    $('#act-duration-unit').value = 'minutes';
    const total = toMinutes(n('#act-duration'), v('#act-duration-unit')) * parseInt(v('#act-frequency')||'1',10) * parseInt(v('#act-people')||'1',10);
    $('#act-total').textContent = Math.round(total);
  }
  $('#act-activity')?.addEventListener('change', refreshActivityDefaults);

  $('#btn-act-save')?.addEventListener('click', async ()=>{
    const payload = {
      activity_id: parseInt(v('#act-activity'),10),
      duration: n('#act-duration'),
      duration_unit: v('#act-duration-unit'),
      recurrence: v('#act-recurrence'),
      frequency: parseInt(v('#act-frequency')||'1',10),
      nb_people: parseInt(v('#act-people')||'1',10)
    };

    let j;
    if (currentActivityEditId) {
      const r = await fetch(`/temps/api/activity_workload/${currentActivityEditId}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      j = await r.json();
      if (!j.ok) return alert('Erreur de mise à jour');
      alert('Analyse activité mise à jour.');
    } else {
      const r = await fetch('/temps/api/activity_workload', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      j = await r.json();
      if (!j.ok) return alert('Erreur d’enregistrement');
      alert('Analyse activité enregistrée.');
    }

    $('#act-total').textContent = Math.round(j.total_minutes || 0);
    currentActivityEditId = null;
    $('#act-editing')?.classList.add('hidden');
    await refreshActivityWorkloadList();
    await refreshActivityDefaults();
  });

  async function refreshActivityWorkloadList(){
    const list = $('#activity-list');
    if (!list) return;
    list.innerHTML = '<div class="muted">Chargement…</div>';
    const r = await fetch('/temps/api/activity_workloads');
    const j = await r.json();
    if (!j.ok) { list.innerHTML = '<div class="muted">Erreur de chargement</div>'; return; }
    if (!j.items.length) { list.innerHTML = '<div class="muted">Aucune analyse enregistrée.</div>'; return; }

    list.innerHTML = j.items.map(it => `
      <div class="acc-item" data-id="${it.id}">
        <div class="acc-head">
          <div class="acc-title">
            <b>${it.activity || 'Activité'}</b>
            <span class="badge">${it.recurrence}</span>
            <span class="badge">freq ${it.frequency}</span>
            <span class="badge">nb ${it.nb_people}</span>
          </div>
          <div class="acc-meta">Durée ${Math.round(it.duration_minutes)} min · Total ${Math.round(it.total_minutes)} min</div>
          <div class="acc-actions">
            <button class="icon-btn edit-aw" title="Éditer">✎</button>
            <button class="icon-btn danger del-aw" title="Supprimer">🗑</button>
          </div>
          <div class="acc-toggle">▼</div>
        </div>
        <div class="acc-body">
          <div class="table-wrap">
            <table class="grid">
              <colgroup>
                <col class="col-activity"><col class="col-num"><col class="col-rec"><col class="col-num-xs"><col class="col-num-xs"><col class="col-num"><col class="col-num">
              </colgroup>
              <thead>
                <tr><th>Activité</th><th>Durée (min)</th><th>Récurrence</th><th>Fréq.</th><th>Nb</th><th>Total (min)</th><th>Délai (min)</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>${it.activity || ''}</td>
                  <td>${Math.round(it.duration_minutes)}</td>
                  <td>${it.recurrence}</td>
                  <td>${it.frequency}</td>
                  <td>${it.nb_people}</td>
                  <td>${Math.round(it.total_minutes)}</td>
                  <td>${it.delay_minutes != null ? Math.round(it.delay_minutes) : '—'}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `).join('');

    $$('#activity-list .acc-item').forEach(item=>{
      const id = parseInt(item.dataset.id,10);

      item.querySelector('.edit-aw').onclick = async (e)=>{
        e.stopPropagation();
        const r = await fetch(`/temps/api/activity_workload/${id}`);
        const j = await r.json();
        if (!j.ok) return alert('Erreur de chargement');
        const it = j.item;
        $('#act-activity').value = it.activity_id;
        $('#act-duration').value = it.duration_minutes;
        $('#act-duration-unit').value = 'minutes';
        $('#act-recurrence').value = it.recurrence;
        $('#act-frequency').value = it.frequency;
        $('#act-people').value = it.nb_people;
        $('#act-total').textContent = Math.round(it.total_minutes || 0);
        currentActivityEditId = id;
        $('#act-editing')?.classList.remove('hidden');
        window.scrollTo({top: $('#subtab-activite').offsetTop - 60, behavior:'smooth'});
      };

      item.querySelector('.del-aw').onclick = async (e)=>{
        e.stopPropagation();
        if (!confirmDel('Supprimer cette analyse activité ?')) return;
        const r = await fetch(`/temps/api/activity_workload/${id}`, {method:'DELETE'});
        const j = await r.json();
        if (j.ok) {
          if (currentActivityEditId === id) {
            currentActivityEditId = null;
            $('#act-editing')?.classList.add('hidden');
          }
          await refreshActivityWorkloadList();
        } else alert('Suppression impossible');
      };

      const head = item.querySelector('.acc-head');
      head.onclick = (ev)=>{
        if (ev.target.closest('.acc-actions')) return;
        item.classList.toggle('open');
      };
    });
  }

  // =====================================================
  // =================== CHARGES - RÔLE ==================
  // =====================================================
  const roleBody = $('#role-rows');

  // Cache des activités filtrées pour le rôle courant
  let roleActivitiesOptions = []; // [{id, name}, ...]

  function buildRoleActivitySelect(){
    const s=document.createElement('select');
    s.className='input';
    if (roleActivitiesOptions.length) {
      s.innerHTML = roleActivitiesOptions.map(a=>`<option value="${a.id}">${a.name}</option>`).join('');
    } else {
      // fallback (ne devrait pas arriver si /role_activities marche)
      s.innerHTML = [...$$('#act-activity option')].map(o=>`<option value="${o.value}">${o.textContent}</option>`).join('');
    }
    return s;
  }

  function addRoleRow(activityId=null, duration=0, _unit='minutes', recurrence='journalier', frequency=1){
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="r-act"></td>
      <td><input type="number" min="0" step="0.1" class="input r-dur" /></td>
      <td class="r-rec"></td>
      <td><input type="number" min="1" step="1" class="input r-freq" value="1" /></td>
      <td class="r-weight">0</td>
      <td class="r-actions"><button class="icon-btn danger r-del" title="Supprimer">🗑</button></td>
    `;
    const actSel = buildRoleActivitySelect();
    tr.querySelector('.r-act').appendChild(actSel);

    const recSel = document.createElement('select');
    recSel.className='input';
    recSel.innerHTML = `<option value="journalier">Journalier</option><option value="hebdomadaire">Hebdomadaire</option><option value="mensuel">Mensuel</option><option value="annuel">Annuel</option>`;
    tr.querySelector('.r-rec').appendChild(recSel);

    if (activityId) actSel.value = String(activityId);
    tr.querySelector('.r-dur').value = duration || 0;
    recSel.value = recurrence || 'journalier';
    tr.querySelector('.r-freq').value = frequency || 1;

    async function prefillDuration(){
      const id = actSel.value;
      const r = await fetch(`/temps/api/activity_defaults/${id}`);
      const j = await r.json();
      tr.querySelector('.r-dur').value = j.duration_minutes ?? 0;
      recalc();
    }

    if (!duration) prefillDuration();

    function recalc(){
      const durMin = parseFloat(tr.querySelector('.r-dur').value || '0');
      const freq = parseInt(tr.querySelector('.r-freq').value || '1', 10);
      const weight = durMin * Math.max(1, freq);
      tr.querySelector('.r-weight').textContent = Math.round(weight);
      recalcRoleTotals();
    }
    tr.addEventListener('input', recalc);
    actSel.onchange = prefillDuration;
    tr.querySelector('.r-del').onclick = ()=>{ tr.remove(); recalcRoleTotals(); };
    roleBody?.appendChild(tr);
  }

  function recalcRoleTotals(){
    let sumD=0, sumW=0, sumM=0, sumA=0;
    $$('#role-rows tr').forEach(tr=>{
      const weight = parseFloat(tr.querySelector('.r-weight').textContent || '0');
      const rec = tr.querySelector('.r-rec select').value;
      if (rec.startsWith('jour')) sumD += weight;
      else if (rec.startsWith('hebdo')) sumW += weight;
      else if (rec.startsWith('mens')) sumM += weight;
      else sumA += weight;
    });

    const dpw = calendarParams.days_per_week || 5;
    const wpy = calendarParams.weeks_per_year || 47;
    const annual = sumD*(dpw*wpy) + sumW*wpy + sumM*12 + sumA;
    const monthly = sumD*(dpw*wpy/12) + sumW*(wpy/12) + sumM + sumA/12;

    updateKpi('kpi-role-d', Math.round(sumD));
    updateKpi('kpi-role-w', Math.round(sumW));
    updateKpi('kpi-role-m', Math.round(sumM));
    updateKpi('kpi-role-a', Math.round(sumA));
    updateKpi('kpi-role-monthly', Math.round(monthly));
    updateKpi('kpi-role-annual', Math.round(annual));
  }

  async function loadRoleActivities(roleId){
    roleBody.innerHTML = '';
    roleActivitiesOptions = [];
    const r = await fetch(`/temps/api/role_activities/${roleId}`);
    const j = await r.json();
    if (!j.ok) { roleBody.innerHTML = '<tr><td colspan="6" class="muted">Erreur de chargement</td></tr>'; return; }
    roleActivitiesOptions = j.activities || [];
    if (!roleActivitiesOptions.length) {
      roleBody.innerHTML = '<tr><td colspan="6" class="muted">Aucune activité pour ce rôle.</td></tr>'; 
      return;
    }
    // Pré-remplir une ligne par activité du rôle (comme avant)
    for (const a of roleActivitiesOptions){
      addRoleRow(a.id, 0, 'minutes', 'journalier', 1);
    }
    setTimeout(recalcRoleTotals, 0);
  }

  $('#role-select')?.addEventListener('change', (e)=> loadRoleActivities(e.target.value));
  $('#btn-role-add-line')?.addEventListener('click', ()=> addRoleRow());

  $('#btn-role-save')?.addEventListener('click', async ()=>{
    const lines = $$('#role-rows tr').map(tr=>({
      activity_id: parseInt(tr.querySelector('.r-act select').value,10),
      duration: parseFloat(tr.querySelector('.r-dur').value || '0'),
      duration_unit: 'minutes',
      recurrence: tr.querySelector('.r-rec select').value,
      frequency: parseInt(tr.querySelector('.r-freq').value || '1',10)
    }));
    const payload = {
      role_id: parseInt($('#role-select').value,10),
      name: $('#role-name').value || 'Analyse rôle',
      lines
    };
    const r = await fetch('/temps/api/role_analysis', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    const j = await r.json();
    if (j.ok){
      alert('Analyse rôle enregistrée.');
      $('#role-name').value='';
      await refreshRoleAnalyses();
    } else alert('Erreur d’enregistrement');
  });

  async function refreshRoleAnalyses(){
    const list = $('#role-list');
    if (!list) return;
    list.innerHTML = '<div class="muted">Chargement…</div>';
    const r = await fetch('/temps/api/role_analyses');
    const j = await r.json();
    if (!j.ok){ list.innerHTML = '<div class="muted">Erreur de chargement</div>'; return; }
    if (!j.items.length){ list.innerHTML = '<div class="muted">Aucune analyse enregistrée.</div>'; return; }

    list.innerHTML = j.items.map(it => `
      <div class="acc-item" data-id="${it.id}">
        <div class="acc-head">
          <div class="acc-title">
            <b class="role-name">${it.name || 'Analyse rôle'}</b>
            <input class="role-name-input hidden input" value="${(it.name || '').replace(/"/g,'&quot;')}" />
            <span class="badge">${it.role}</span>
          </div>
          <div class="acc-meta">
            J:${Math.round(it.sum_daily_minutes)} · H:${Math.round(it.sum_weekly_minutes)} · M:${Math.round(it.sum_monthly_minutes)} · A:${Math.round(it.sum_yearly_minutes)} ·
            Mensuel:${Math.round(it.monthly_minutes)} min · Annuel:${Math.round(it.annual_minutes)} min
          </div>
          <div class="acc-actions">
            <button class="icon-btn edit-role" title="Renommer">✎</button>
            <button class="icon-btn success save-role hidden" title="Enregistrer">✔</button>
            <button class="icon-btn cancel-role hidden" title="Annuler">✖</button>
            <button class="icon-btn danger del-role" title="Supprimer">🗑</button>
          </div>
          <div class="acc-toggle">▼</div>
        </div>
        <div class="acc-body"></div>
      </div>
    `).join('');

    $$('#role-list .acc-item').forEach(item=>{
      const id = item.dataset.id;
      const head = item.querySelector('.acc-head');
      const nameEl = item.querySelector('.role-name');
      const inputEl = item.querySelector('.role-name-input');
      const editBtn = item.querySelector('.edit-role');
      const saveBtn = item.querySelector('.save-role');
      const cancelBtn = item.querySelector('.cancel-role');

      function setEditing(on){
        if (on){
          inputEl.value = nameEl.textContent.trim();
          nameEl.classList.add('hidden');
          inputEl.classList.remove('hidden');
          editBtn.classList.add('hidden');
          saveBtn.classList.remove('hidden');
          cancelBtn.classList.remove('hidden');
          inputEl.focus(); inputEl.select();
        } else {
          nameEl.classList.remove('hidden');
          inputEl.classList.add('hidden');
          editBtn.classList.remove('hidden');
          saveBtn.classList.add('hidden');
          cancelBtn.classList.add('hidden');
        }
      }

      editBtn.onclick = (e)=>{ e.stopPropagation(); setEditing(true); };
      cancelBtn.onclick = (e)=>{ e.stopPropagation(); setEditing(false); };
      saveBtn.onclick = async (e)=>{
        e.stopPropagation();
        const newName = inputEl.value.trim();
        const r = await fetch(`/temps/api/role_analysis/${id}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name:newName})});
        const j = await r.json();
        if (j.ok) { nameEl.textContent = j.name; setEditing(false); }
        else alert('Erreur de renommage');
      };

      head.onclick = async (ev)=>{
        if (ev.target.closest('.acc-actions')) return;
        const body = item.querySelector('.acc-body');
        const opened = item.classList.toggle('open');
        if (opened){
          const rr = await fetch(`/temps/api/role_analysis/${id}`);
          const jj = await rr.json();
          if (!jj.ok){ body.innerHTML = '<div class="muted">Erreur</div>'; return; }
          const rows = jj.lines || [];
          body.innerHTML = `
            <div class="table-wrap">
              <table class="grid">
                <colgroup>
                  <col class="col-activity"><col class="col-num"><col class="col-rec"><col class="col-num-xs"><col class="col-num"><col class="col-actions">
                </colgroup>
                <thead>
                  <tr><th>Activité</th><th>Durée (min)</th><th>Récurrence</th><th>Fréq.</th><th>Pesée (min)</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  ${rows.map(r => `<tr data-line="${r.id}">
                    <td>${r.activity}</td>
                    <td>${Math.round(r.duration_minutes)}</td>
                    <td>${r.recurrence}</td>
                    <td>${r.frequency}</td>
                    <td>${Math.round(r.weight_minutes)}</td>
                    <td><button class="icon-btn danger del-role-line" title="Supprimer la ligne">🗑</button></td>
                  </tr>`).join('')}
                </tbody>
              </table>
            </div>
          `;
          body.querySelectorAll('.del-role-line').forEach(btn=>{
            btn.onclick = async ()=>{
              const tr = btn.closest('tr');
              const lineId = tr.dataset.line;
              if (!confirmDel('Supprimer cette activité de l’analyse ?')) return;
              const rr2 = await fetch(`/temps/api/role_line/${lineId}`, {method:'DELETE'});
              const resp = await rr2.json();
              if (resp.ok){
                if (resp.analysis_deleted){
                  item.remove();
                  if (!$('#role-list').children.length) $('#role-list').innerHTML = '<div class="muted">Aucune analyse enregistrée.</div>';
                }else{
                  item.classList.remove('open'); head.click();
                }
              }else alert('Suppression impossible');
            };
          });
        }
      };

      item.querySelector('.del-role').onclick = async (e)=>{
        e.stopPropagation();
        if (!confirmDel('Supprimer cette analyse rôle ?')) return;
        const r = await fetch(`/temps/api/role_analysis/${id}`, {method:'DELETE'});
        const j = await r.json();
        if (j.ok){
          item.remove();
          if (!$('#role-list').children.length) $('#role-list').innerHTML = '<div class="muted">Aucune analyse enregistrée.</div>';
        }else alert('Suppression impossible');
      };
    });
  }

  // ---------------------- INIT ------------------------
  (async () => {
    await loadCalendarParams();

    // Weakness: si la sous-page existe dans le DOM, init
    if ($('#subtab-faiblesse')) {
      // Construire le select activité de la faiblesse depuis la liste principale
      const fwAct = $('#fw-activity');
      if (fwAct && !fwAct.children.length) {
        fwAct.innerHTML = $$('#act-activity option').map(o=>`<option value="${o.value}">${o.textContent}</option>`).join('');
      }
      await refreshWeaknessDefaults();
    }

    await refreshProjectList();
    await refreshActivityWorkloadList();

    // Prefill bloc Activité
    if ($('#act-activity')) {
      const r0 = await fetch(`/temps/api/activity_defaults/${$('#act-activity').value}`);
      const j0 = await r0.json();
      $('#act-duration').value = j0.duration_minutes ?? 0;
      $('#act-duration-unit').value = 'minutes';
      const total = toMinutes(n('#act-duration'), v('#act-duration-unit')) * parseInt(v('#act-frequency')||'1',10) * parseInt(v('#act-people')||'1',10);
      $('#act-total').textContent = Math.round(total);
    }

    // Projet : une ligne par défaut au démarrage
    if ($$('#project-rows tr').length === 0 && $('#project-rows')) { addProjectRow(); recalcProjectTotals(); }

    // Rôle
    if ($('#role-select')) {
      await loadRoleActivities($('#role-select').value);
      setTimeout(recalcRoleTotals, 0);
    }
    await refreshRoleAnalyses();
  })();

})();
