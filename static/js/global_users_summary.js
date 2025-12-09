/**
 * Code/static/js/global_users_summary.js
 * Script pour le filtrage du tableau récapitulatif des utilisateurs
 */

function filterGlobalTable() {
  var roleFilter = document.getElementById('global-role-filter');
  var onlyWithNotes = document.getElementById('filter-with-notes');
  var table = document.getElementById('global-users-table');
  
  if (!table) {
    console.log('Table non trouvée');
    return;
  }
  
  var selectedRole = roleFilter ? roleFilter.value : '';
  var showOnlyWithNotes = onlyWithNotes ? onlyWithNotes.checked : false;
  
  // Gérer les en-têtes de colonnes
  var headerCells = table.querySelectorAll('thead th');
  headerCells.forEach(function(th, index) {
    if (index === 0) {
      th.style.display = '';
    } else {
      var role = th.getAttribute('data-role');
      if (!selectedRole || role === selectedRole) {
        th.style.display = '';
      } else {
        th.style.display = 'none';
      }
    }
  });
  
  // Gérer les lignes du tableau
  var rows = table.querySelectorAll('tbody tr');
  rows.forEach(function(row) {
    var cells = row.querySelectorAll('td');
    var hasNote = false;
    var hasNoteForRole = false;
    
    cells.forEach(function(td, index) {
      if (index === 0) {
        td.style.display = '';
      } else {
        var role = td.getAttribute('data-role');
        var note = td.getAttribute('data-note');
        
        if (note && note !== '') {
          hasNote = true;
          if (role === selectedRole) {
            hasNoteForRole = true;
          }
        }
        
        if (!selectedRole || role === selectedRole) {
          td.style.display = '';
        } else {
          td.style.display = 'none';
        }
      }
    });
    
    // Décider si la ligne est visible
    var showRow = true;
    if (showOnlyWithNotes) {
      if (selectedRole) {
        showRow = hasNoteForRole;
      } else {
        showRow = hasNote;
      }
    }
    
    row.style.display = showRow ? '' : 'none';
  });
}

// Exposer la fonction globalement
window.filterGlobalTable = filterGlobalTable;