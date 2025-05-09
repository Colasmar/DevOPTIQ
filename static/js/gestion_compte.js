document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const roleFilter = document.getElementById('roleFilter');
    const searchBtn = document.getElementById('searchButton');
    const resultContainer = document.getElementById('filteredList');
  
    const allUsers = Array.from(document.querySelectorAll('.role-section li')).map(li => ({
      name: li.textContent.toLowerCase(),
      email: li.querySelector('span.email')?.innerText || '',
      role: li.getAttribute('data-role'),
      status: li.getAttribute('data-status'),
      html: li.outerHTML
    }));
  
    searchBtn.addEventListener('click', () => {
      const searchTerm = searchInput.value.toLowerCase();
      const statusVal = statusFilter.value;
      const roleVal = roleFilter.value;
  
      const results = allUsers.filter(user =>
        user.name.includes(searchTerm) &&
        (statusVal === '' || user.status === statusVal) &&
        (roleVal === '' || user.role === roleVal)
      );
  
      resultContainer.innerHTML = results.map(r => r.html).join('') || "<li>Aucun résultat</li>";
    });
  });
  