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

  rows.forEach((row, rIdx) => {
    const rowData = [];
    row.querySelectorAll("th, td").forEach((cell, cIdx) => {
      const isHeader = cell.tagName === "TH";
      const text = cell.innerText.trim();
      const cellValue = isHeader || cIdx === 0 ? text : (text === "-" ? "-" : "");

      rowData.push(cellValue);
    });
    worksheet.addRow(rowData);
  });

  // Appliquer les couleurs de fond uniquement pour les notations (sans texte)
  table.querySelectorAll("tbody tr").forEach((tr, rIdx) => {
    tr.querySelectorAll("td").forEach((td, cIdx) => {
      const noteClass = [...td.classList].find(cls => ['green', 'orange', 'red'].includes(cls));
      if (noteClass) {
        const excelCell = worksheet.getRow(rIdx + 2).getCell(cIdx + 2); // +2 : une ligne header + nom utilisateur
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

  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  });

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

  rows.forEach((row, rIdx) => {
    const rowData = [];
    row.querySelectorAll("th, td").forEach((cell, cIdx) => {
      if (cell.tagName === "TH") {
        rowData.push(cell.innerText.trim());
      } else if (cIdx === 0) {
        rowData.push(cell.innerText.trim());
      } else {
        const cls = [...cell.classList];
        const note = cls.includes("green") ? "green"
                   : cls.includes("orange") ? "orange"
                   : cls.includes("red") ? "red" : "-";
        rowData.push(note);
      }
    });
    body.push(rowData);
  });

  doc.autoTable({
    head: [body[0]],
    body: body.slice(1),
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

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("tr.user-row").forEach(row => {
    row.style.cursor = "pointer";
    row.addEventListener("click", () => {
      const userId = row.querySelector(".user-name").dataset.userId;
      const managerId = row.dataset.managerId;
      if (userId && managerId) {
        window.location.href = `/competences/view`;
      }
    });
  });
});



