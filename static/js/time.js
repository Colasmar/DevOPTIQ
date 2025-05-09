document.addEventListener('DOMContentLoaded', () => {
    const addBtn = document.getElementById('addAnalysisBtn');
    const formContainer = document.getElementById('analysisFormContainer');
    const cancelBtn = document.getElementById('cancelBtn');
    const analysisTypeSelect = document.getElementById('analysisType');
    const activityContainer = document.getElementById('activitySelectContainer');
    const taskContainer = document.getElementById('taskSelectContainer');
    const form = document.getElementById('timeAnalysisForm');

    // Ajoute une info pour l'utilisateur
    const formInfo = document.createElement('p');
    formInfo.innerText = "Les dates de début et de fin définissent la période concernée.";
    form.insertBefore(formInfo, form.firstChild);

    if (addBtn) {
        addBtn.addEventListener('click', () => {
            formContainer.classList.remove('hidden');
        });
    }
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            formContainer.classList.add('hidden');
            form.reset();
            // Réinitialiser l'affichage
            activityContainer.classList.add('hidden');
            taskContainer.classList.add('hidden');
        });
    }

    if (analysisTypeSelect) {
        analysisTypeSelect.addEventListener('change', () => {
            const val = analysisTypeSelect.value;
            if (val === 'activity') {
                activityContainer.classList.remove('hidden');
                taskContainer.classList.add('hidden');
            } else if (val === 'task') {
                activityContainer.classList.add('hidden');
                taskContainer.classList.remove('hidden');
            } else {
                activityContainer.classList.add('hidden');
                taskContainer.classList.add('hidden');
            }
            // Mettre à jour le champ caché
            document.getElementById('analysis_type').value = val;
        });
    }
});