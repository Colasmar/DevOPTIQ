function applyFilter() {
  const selectedRole = document.getElementById("role-filter").value;
  document.querySelectorAll("[data-role]").forEach(el => {
    el.style.display = (selectedRole === "all" || el.dataset.role === selectedRole) ? "" : "none";
  });
}

function openExportModal() {
  document.getElementById("exportModal").style.display = "block";
}

function closeExportModal() {
  document.getElementById("exportModal").style.display = "none";
}

async function exportToExcel() {
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet("Aperçu");

  const table = document.getElementById("user-summary-table");
  const rows = table.querySelectorAll("tr");

  // Ajouter toutes les lignes du tableau HTML à Excel
  rows.forEach((row, rIdx) => {
    const excelRow = worksheet.addRow([]);
    row.querySelectorAll("th, td").forEach((cell, cIdx) => {
      const isHeader = cell.tagName === "TH";
      const text = cell.innerText.trim();

      // Cellule d'en-tête ou nom d'utilisateur
      if (isHeader || (cIdx === 0 && text !== "")) {
        excelRow.getCell(cIdx + 1).value = text;
      }
      // Cellule de note
      else if (text === "-") {
        excelRow.getCell(cIdx + 1).value = "-";
      } else {
        excelRow.getCell(cIdx + 1).value = "";
      }
    });
  });

  // Appliquer les couleurs de fond aux cellules de notation
  table.querySelectorAll("tbody tr").forEach((tr, rIdx) => {
    tr.querySelectorAll("td").forEach((td, cIdx) => {
      const noteClass = [...td.classList].find(cls => ['green', 'orange', 'red'].includes(cls));
      if (noteClass) {
        const excelCell = worksheet.getRow(rIdx + 4).getCell(cIdx + 2); // +4 car 3 lignes d’en-tête + Excel = 1-based
        const colorMap = {
          green: 'A0E6A0',
          orange: 'FFE0A3',
          red: 'F5A7A7'
        };
        excelCell.fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: colorMap[noteClass] }
        };
      }
    });
  });

  // Génération du fichier .xlsx
  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "Apercu_Utilisateurs.xlsx";
  a.click();
}




function exportToPDF() {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF("landscape");
  const table = document.getElementById("user-summary-table");

  doc.text("Aperçu global des utilisateurs", 14, 14);

  const body = [];
  const rows = table.querySelectorAll("tr");
  rows.forEach(row => {
    const rowData = [];
    row.querySelectorAll("th, td").forEach(cell => {
      const text = cell.innerText.trim();
      rowData.push(text === "" ? cell.classList[1] || "-" : text);
    });
    body.push(rowData);
  });

  doc.autoTable({
    head: [body[0], body[1]],
    body: body.slice(2),
    startY: 20,
    theme: 'grid',
    styles: {
      cellWidth: 'wrap',
      halign: 'center',
      valign: 'middle'
    },
    headStyles: { fillColor: [200, 200, 200] }
  });

  doc.save("Apercu_Utilisateurs.pdf");
}

