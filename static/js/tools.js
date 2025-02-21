// tools.js - Gestion des outils

function showToolForm(taskId) {
    document.getElementById('tool-form-' + taskId).style.display = 'block';
    fetch('/tools/all')
    .then(response => response.json())
    .then(data => {
      const selectElem = document.getElementById('existing-tools-' + taskId);
      selectElem.innerHTML = "";
      data.forEach(tool => {
        const option = document.createElement('option');
        option.value = tool.id;
        option.text = tool.name;
        selectElem.appendChild(option);
      });
    })
    .catch(error => {
      alert("Erreur lors du chargement des outils existants: " + error.message);
    });
  }
  
  function hideToolForm(taskId) {
    document.getElementById('tool-form-' + taskId).style.display = 'none';
  }
  
  function submitTools(taskId) {
    const selectElem = document.getElementById('existing-tools-' + taskId);
    const newToolsInput = document.getElementById('new-tools-' + taskId);
    const existingToolIds = Array.from(selectElem.selectedOptions).map(opt => parseInt(opt.value));
    const newTools = newToolsInput.value.split(",").map(item => item.trim()).filter(item => item.length > 0);
    const payload = {
      task_id: parseInt(taskId),
      existing_tool_ids: existingToolIds,
      new_tools: newTools
    };
    fetch('/tools/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
      const noToolsMsg = document.getElementById('no-tools-msg-' + taskId);
      if (noToolsMsg) {
        noToolsMsg.parentNode.removeChild(noToolsMsg);
      }
      const toolsContainer = document.getElementById('tools-for-task-' + taskId);
      let ul = toolsContainer.querySelector('ul');
      if (!ul) {
        ul = document.createElement('ul');
        toolsContainer.appendChild(ul);
      }
      let addBtn = ul.querySelector('li.add-tool-li');
      if (addBtn) {
        addBtn.parentNode.removeChild(addBtn);
      }
      data.added_tools.forEach(tool => {
        const li = document.createElement('li');
        li.setAttribute("data-tool-id", tool.id);
        li.innerHTML = tool.name + ` <button class="icon-btn" onclick="deleteToolFromTask('${taskId}', '${tool.id}')">
                                      <i class="fa-solid fa-trash"></i></button>`;
        ul.appendChild(li);
      });
      const newAddLi = document.createElement('li');
      newAddLi.className = 'add-tool-li';
      newAddLi.innerHTML = `<button class="icon-btn add-tool-btn" onclick="showToolForm('${taskId}')">
                              <i class="fa-solid fa-plus"></i>
                            </button>`;
      ul.appendChild(newAddLi);
      selectElem.selectedIndex = -1;
      newToolsInput.value = "";
      hideToolForm(taskId);
    })
    .catch(error => {
      alert(error.message);
    });
  }
  
  function deleteToolFromTask(taskId, toolId) {
    if (!confirm("Confirmez-vous la suppression de cet outil ?")) return;
    fetch(`/activities/tasks/${taskId}/tools/${toolId}`, { method: 'DELETE' })
    .then(response => response.json())
    .then(data => {
      const toolsContainer = document.getElementById('tools-for-task-' + taskId);
      const ul = toolsContainer.querySelector('ul');
      if (!ul) return;
      const realToolElem = ul.querySelector(`li[data-tool-id="${toolId}"]`);
      if (realToolElem) {
        realToolElem.parentNode.removeChild(realToolElem);
      }
      let addBtn = ul.querySelector('li.add-tool-li');
      if (!addBtn) {
        const newAddLi = document.createElement('li');
        newAddLi.className = 'add-tool-li';
        newAddLi.innerHTML = `<button class="icon-btn add-tool-btn" onclick="showToolForm('${taskId}')">
                                <i class="fa-solid fa-plus"></i>
                              </button>`;
        ul.appendChild(newAddLi);
      }
    })
    .catch(error => {
      alert(error.message);
    });
  }
  