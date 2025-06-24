document.getElementById("user-select").addEventListener("change", function () {
  const userId = this.value;
  if (!userId) return;

  fetch(`/projection_metier/analyze_user/${userId}`)
    .then((res) => res.json())
    .then((data) => {
      const fullList = document.getElementById("full-list");
      const partialList = document.getElementById("partial-list");

      fullList.innerHTML = "";
      partialList.innerHTML = "";

      data.full.forEach((m) => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${m.libelle}</strong> (${m.code}) — ${m.total_required} compétences requises`;
        fullList.appendChild(li);
      });

      data.partial.forEach((m) => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${m.libelle}</strong> (${m.code}) — ${m.match_count}/${m.total_required} compétences déjà acquises <br><em>Compétences manquantes :</em> ${m.missing.join(", ")}`;
        partialList.appendChild(li);
      });
    });
});
