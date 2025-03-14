// Fonction pour ajouter une performance
function addPerformance(dataId) {
    // Demander à l'utilisateur de saisir le nom et la description via des prompts simples
    let name = prompt("Entrez le nom de la performance :");
    if (!name) return; // Annuler si aucun nom n'est saisi
    let description = prompt("Entrez une description (optionnelle) :");
  
    fetch("/performance/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        data_id: dataId,
        name: name,
        description: description
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        // Mise à jour de l'UI en rechargeant la page
        location.reload();
      }
    })
    .catch(error => {
      console.error("Erreur lors de l'ajout de la performance :", error);
      alert("Une erreur est survenue lors de l'ajout.");
    });
  }
  
  // Fonction pour modifier une performance existante
  function editPerformance(perfId) {
    let newName = prompt("Entrez le nouveau nom de la performance :");
    if (!newName) return;
    let newDescription = prompt("Entrez la nouvelle description (optionnelle) :");
  
    fetch(`/performance/${perfId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: newName,
        description: newDescription
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        location.reload();
      }
    })
    .catch(error => {
      console.error("Erreur lors de la modification de la performance :", error);
      alert("Une erreur est survenue lors de la modification.");
    });
  }
  
  // Fonction pour supprimer une performance existante
  function deletePerformance(perfId, dataId) {
    if (!confirm("Confirmez-vous la suppression de cette performance ?")) return;
  
    fetch(`/performance/${perfId}`, {
      method: "DELETE"
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert("Erreur : " + data.error);
      } else {
        // Réaffichage du bouton "Performance" en rechargeant la page
        location.reload();
      }
    })
    .catch(error => {
      console.error("Erreur lors de la suppression de la performance :", error);
      alert("Une erreur est survenue lors de la suppression.");
    });
  }
  