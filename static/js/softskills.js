// Code/static/js/softskills.js

/*******************************************
 * UTILITAIRE : récupérer activityId depuis un élément
 * (cherche le parent .softskills-section le plus proche)
 *******************************************/
function getActivityIdFromElement(element) {
    const section = element.closest(".softskills-section");
    return section ? section.dataset.activityId : null;
}

/*******************************************
 * JUSTIFICATION (toggle)
 *******************************************/
function toggleSoftskillJustification(ssId) {
    const div = document.getElementById("softskill-justif-" + ssId);
    if (!div) return;

    div.style.display = (div.style.display === "none" || !div.style.display)
        ? "block"
        : "none";
}

/*******************************************
 * AJOUT MANUEL
 *******************************************/
function showAddSoftskillForm(activityId) {
    document.getElementById("add-softskill-form-" + activityId).style.display = "block";
}

function hideAddSoftskillForm(activityId) {
    document.getElementById("add-softskill-form-" + activityId).style.display = "none";

    document.getElementById("new-softskill-name-" + activityId).value = "";
    document.getElementById("new-softskill-level-" + activityId).value = "2 (Acquisition)"; // Valeur par défaut
    document.getElementById("new-softskill-justif-" + activityId).value = "";
}

function submitAddSoftskill(activityId) {
    const habilete = document.getElementById("new-softskill-name-" + activityId).value.trim();
    const niveau = document.getElementById("new-softskill-level-" + activityId).value.trim();
    const justification = document.getElementById("new-softskill-justif-" + activityId).value.trim();

    if (!habilete || !niveau) {
        alert("Veuillez renseigner au moins habileté et niveau.");
        return;
    }

    showSpinner();
    fetch("/softskills/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            activity_id: activityId,
            habilete,
            niveau,
            justification
        })
    })
    .then(r => r.json())
    .then(d => {
        hideSpinner();
        if (d.error) {
            alert("Erreur ajout HSC : " + d.error);
        } else {
            updateSoftskillsList(activityId);
            hideAddSoftskillForm(activityId);
        }
    })
    .catch(err => {
        hideSpinner();
        console.error("Erreur ajout HSC:", err);
        alert("Erreur ajout HSC : " + err.message);
    });
}

/*******************************************
 * RAFRAÎCHIR PARTIAL
 *******************************************/
async function updateSoftskillsList(activityId) {
    try {
        const resp = await fetch(`/softskills/${activityId}/render`);
        if (!resp.ok) throw new Error("Erreur lors du rafraîchissement des softskills");

        const html = await resp.text();
        const container = document.getElementById("softskills-list-" + activityId);

        if (container) {
            container.innerHTML = html;

            // 🔥 FORCER LE RE-ATTACHEMENT DES ÉCOUTEURS
            // (la même technique que pour savoirs / performances)
            const newScripts = container.querySelectorAll("script");
            newScripts.forEach(scr => eval(scr.innerHTML));
        }
    } catch (err) {
        console.error("Erreur updateSoftskillsList:", err);
        alert("Erreur updateSoftskillsList : " + err.message);
    }
}

/*******************************************
 * EDITION : ouvrir / fermer
 * 🔥 CORRECTION : accepte maintenant activityId en paramètre
 *******************************************/
function openEditSoftskill(activityId, ssId) {
    const disp = document.getElementById(`softskill-display-${ssId}`);
    const edit = document.getElementById(`softskill-edit-${ssId}`);

    if (!disp || !edit) {
        console.error("openEditSoftskill : éléments manquants", ssId);
        return;
    }

    disp.style.display = "none";
    edit.style.display = "block"; // 🔥 Block au lieu de flex pour disposition verticale
}

function cancelEditSoftskill(ssId) {
    const disp = document.getElementById(`softskill-display-${ssId}`);
    const edit = document.getElementById(`softskill-edit-${ssId}`);

    if (!disp || !edit) return;

    edit.style.display = "none";
    disp.style.display = "flex"; // Le mode affichage reste en flex (horizontal)
}

/*******************************************
 * EDITION : enregistrer
 *******************************************/
function submitEditSoftskill(activityId, ssId) {

    const hab = document.getElementById(`softskill-edit-input-${ssId}`)?.value.trim();
    const niv = document.getElementById(`softskill-edit-level-${ssId}`)?.value.trim();
    const jus = document.getElementById(`softskill-edit-justif-${ssId}`)?.value.trim();

    if (!hab || !niv) {
        alert("Veuillez renseigner habileté et niveau.");
        return;
    }

    showSpinner();
    fetch(`/softskills/${activityId}/${ssId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            habilete: hab,
            niveau: niv,
            justification: jus
        })
    })
    .then(r => r.json())
    .then(async d => {
        hideSpinner();
        if (d.error) {
            alert("Erreur mise à jour HSC : " + d.error);
        } else {
            await updateSoftskillsList(activityId);
        }
    })
    .catch(err => {
        hideSpinner();
        console.error("Erreur maj HSC:", err);
    });
}


/*******************************************
 * SUPPRESSION 
 * 🔥 CORRECTION MAJEURE : activityId passé en paramètre
 *******************************************/
async function deleteSoftskill(activityId, ssId) {

    if (!confirm("Voulez-vous vraiment supprimer cette HSC ?")) return;

    if (!activityId) {
        alert("Impossible de déterminer l'activité.");
        return;
    }

    showSpinner();

    try {
        const resp = await fetch(`/softskills/${activityId}/${ssId}`, {
            method: "DELETE"
        });
        const data = await resp.json();

        hideSpinner();

        if (data.error) {
            alert("Erreur suppression HSC : " + data.error);
            return;
        }

        // 🔥 SUPER IMPORTANT :
        // Attendre un cycle complet avant de rafraîchir
        await new Promise(resolve => setTimeout(resolve, 30));

        // 🔥 Rafraîchir la liste et forcer le DOM update
        await updateSoftskillsList(activityId);

    } catch (err) {
        hideSpinner();
        console.error("Erreur suppression HSC:", err);
        alert("Erreur suppression HSC : " + err.message);
    }
}