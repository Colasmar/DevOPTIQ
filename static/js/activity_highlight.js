// Code/static/js/activity_highlight.js

document.addEventListener("DOMContentLoaded", () => {
  const url = new URL(window.location.href);
  const activityId = url.searchParams.get("activity_id") || url.searchParams.get("highlight");
  if (!activityId) return;

  // On cherche d'abord le container principal de l'activité
  let container =
    document.querySelector(`.activity-container[data-activity-id="${activityId}"]`) ||
    null;

  // Fallback : si besoin, on peut rechercher via la div de détails
  if (!container) {
    const details = document.getElementById(`details-${activityId}`);
    if (details) {
      container = details.closest(".activity-container");
    }
  }

  if (!container) {
    return;
  }

  // Ajout de la classe de highlight
  container.classList.add("highlighted-activity");

  // On ouvre les détails si possible
  const header = container.querySelector(".activity-header");
  if (header && typeof header.click === "function") {
    header.click();
  }

  // Scroll au centre de l'écran
  container.scrollIntoView({ behavior: "smooth", block: "center" });
});
