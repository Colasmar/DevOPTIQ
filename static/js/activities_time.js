// Code/static/js/activities_time.js
(() => {
  const $$ = (s, c=document) => Array.from(c.querySelectorAll(s));
  const toMn = (q,u)=> (parseFloat(q||0) * ({minutes:1, heures:60, jours:1440}[(u||'minutes').toLowerCase()]||1));

  function unitSelect(){
    const s = document.createElement('select');
    s.innerHTML = `<option>minutes</option><option>heures</option><option>jours</option>`;
    return s;
  }

  function show(el){ if (el) el.style.display = ''; }
  function hide(el){ if (el) el.style.display = 'none'; }

  function initOne(container){
    if (!container) return;

    // helpers scopés
    const q  = (sel) => container.querySelector(sel);
    const qq = (sel) => $$(sel, container);

    const activityId = parseInt(container.getAttribute('data-activity-id') || '0', 10);
    if (!activityId) return;

    const elGlobal = q('.at-global');
    const elTasks  = q('.at-tasks');
    const bodyRows = q('.at-task-rows');
    const sumEl    = q('.at-sum');

    // radios nommés par activité
    const getMode = () => container.querySelector(`input[name="at-mode-${activityId}"]:checked`)?.value || 'activity';

    function toggleMode(){
      const m = getMode();
      if (m === 'tasks'){ show(elTasks); }
      else { hide(elTasks); }
    }

    // listeners radio
    qq(`input[name="at-mode-${activityId}"]`).forEach(r => r.addEventListener('change', toggleMode));

    function recalcSum(){
      let s = 0;
      qq('.at-task-rows tr').forEach(tr=>{
        const qv = parseFloat(tr.querySelector('.t-dur')?.value || '0');
        const uv = tr.querySelector('.t-unit select')?.value || 'minutes';
        s += toMn(qv, uv);
      });
      if (sumEl) sumEl.textContent = String(Math.round(s));
    }

    async function loadState(){
      const r = await fetch(`/temps/api/activity_time/${activityId}`);
      const j = await r.json();

      // bloc global
      if (q('.at-dur'))      q('.at-dur').value = j.activity?.duration_minutes ?? 0;
      if (q('.at-dur-unit')) q('.at-dur-unit').value = 'minutes';
      const delay = j.activity?.delay_minutes ?? 0;
      if (q('.at-del'))      q('.at-del').value = delay;
      if (q('.at-del-unit')) q('.at-del-unit').value = 'minutes';

      // bloc tâches
      if (bodyRows){
        bodyRows.innerHTML = (j.tasks || []).map(t => `
          <tr data-task="${t.id}">
            <td>${t.name}</td>
            <td style="text-align:right;"><input type="number" class="t-dur" step="0.1" min="0" value="${t.duration_minutes ?? 0}"></td>
            <td class="t-unit"></td>
          </tr>
        `).join('');
        qq('.t-unit').forEach(td => {
          const s = unitSelect();
          td.appendChild(s);
          s.value = 'minutes'; // valeurs stockées en minutes
        });
      }

      if (q('.at-del2'))      q('.at-del2').value = delay;
      if (q('.at-del2-unit')) q('.at-del2-unit').value = 'minutes';

      recalcSum();

      // mode suggéré renvoyé par l’API
      const suggested = j.mode || 'activity';
      qq(`input[name="at-mode-${activityId}"]`).forEach(r => r.checked = (r.value === suggested));
      toggleMode();

      // écouteurs recalcul
      container.addEventListener('input', (e)=>{
        if (e.target.closest('.at-task-rows')) {
          if (e.target.classList.contains('t-dur') || e.target.closest('.t-unit')) recalcSum();
        }
      });
    }

    async function saveState(){
      const mode = getMode();
      let payload = {};
      if (mode === 'tasks'){
        payload = {
          mode,
          delay: parseFloat(q('.at-del2')?.value || '0'),
          delay_unit: q('.at-del2-unit')?.value || 'minutes',
          tasks: $$('.at-task-rows tr', container).map(tr => ({
            task_id: parseInt(tr.getAttribute('data-task')||'0',10),
            duration: parseFloat(tr.querySelector('.t-dur')?.value || '0'),
            duration_unit: tr.querySelector('.t-unit select')?.value || 'minutes'
          }))
        };
      } else {
        payload = {
          mode,
          duration: parseFloat(q('.at-dur')?.value || '0'),
          duration_unit: q('.at-dur-unit')?.value || 'minutes',
          delay: parseFloat(q('.at-del')?.value || '0'),
          delay_unit: q('.at-del-unit')?.value || 'minutes'
        };
      }

      const r = await fetch(`/temps/api/activity_time/${activityId}`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      const j = await r.json();
      if (j.ok){
        alert('Durée / délai enregistrés.');
        await loadState();
      } else {
        alert('Erreur lors de l’enregistrement.');
      }
    }

    async function resetState(){
      if (!window.confirm('Réinitialiser la durée/délai de cette activité (et ses tâches) ?')) return;
      const r = await fetch(`/temps/api/activity_time/${activityId}`, {method:'DELETE'});
      const j = await r.json();
      if (j.ok){
        await loadState();
      } else {
        alert('Réinitialisation impossible.');
      }
    }

    // boutons
    q('.at-save')?.addEventListener('click', saveState);
    q('.at-reset')?.addEventListener('click', resetState);

    // init
    loadState();
  }

  document.addEventListener('DOMContentLoaded', () => {
    $$('.activity-time[data-activity-id]').forEach(initOne);
  });
})();
