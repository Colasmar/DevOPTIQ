document.addEventListener('DOMContentLoaded', () => {
    const addBtn = document.getElementById('addAnalysisBtn');
    const modal = document.getElementById('analysisModal');
    const closeBtn = document.getElementById('closeModal');
    const form = document.getElementById('timeAnalysisForm');

    if (addBtn) {
        addBtn.addEventListener('click', () => {
            modal.classList.remove('hidden');
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            modal.classList.add('hidden');
            form.reset();
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
            form.reset();
        }
    });

    const typeSelect = document.getElementById('analysisType');
    const activityContainer = document.getElementById('activitySelectContainer');
    const roleContainer = document.getElementById('roleSelectContainer');
    const userContainer = document.getElementById('userSelectContainer');
    const weightWarning = document.getElementById('weightWarning');
    const autoWeightCheckbox = document.getElementById('autoWeight');
    const userSearch = document.getElementById('userSearch');
    const userSelect = document.getElementById('userSelect');

    if (typeSelect) {
        typeSelect.addEventListener('change', () => {
            const val = typeSelect.value;
            activityContainer.classList.toggle('hidden', val !== 'activity');
            roleContainer.classList.toggle('hidden', val !== 'role');
            userContainer.classList.toggle('hidden', val !== 'user');
        });
    }

    if (autoWeightCheckbox && weightWarning) {
        autoWeightCheckbox.addEventListener('change', () => {
            weightWarning.classList.toggle('hidden', !autoWeightCheckbox.checked);
        });
    }

    if (userSearch && userSelect) {
        userSearch.addEventListener('input', () => {
            const search = userSearch.value.toLowerCase();
            Array.from(userSelect.options).forEach(option => {
                const text = option.textContent.toLowerCase();
                option.style.display = text.includes(search) ? '' : 'none';
            });
        });
    }
});
