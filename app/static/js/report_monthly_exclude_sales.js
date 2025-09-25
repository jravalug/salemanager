document.addEventListener("DOMContentLoaded", function () {
  // Inicializar DataTables en tablas con clase .sales-table (o fallback a #sales-table)
  var initialized = false;
  document.querySelectorAll(".sales-table").forEach(function (tbl) {
    try {
      new simpleDatatables.DataTable(tbl, {
        searchable: true,
        perPage: 10,
        perPageSelect: [5, 10, 15, 20],
        labels: {
          placeholder: "Buscar...",
          perPage: "{select} ventas por página",
          noRows: "No se encontraron ventas",
          info: "Mostrando {start} a {end} de {rows} ventas",
        },
      });
      initialized = true;
    } catch (e) {
      console.warn("dt init", e);
    }
  });

  if (!initialized) {
    var single = document.getElementById("sales-table");
    if (single) {
      try {
        new simpleDatatables.DataTable(single, {
          searchable: true,
          perPage: 10,
          perPageSelect: [5, 10, 15, 20],
          labels: {
            placeholder: "Buscar...",
            perPage: "{select} ventas por página",
            noRows: "No se encontraron ventas",
            info: "Mostrando {start} a {end} de {rows} ventas",
          },
        });
      } catch (e) {
        console.warn("dt init", e);
      }
    }
  }

  // Abrir Modal
  document
    .getElementById("open-modal-btn")
    .addEventListener("click", function () {
      const modal = document.getElementById("exclude-sales-modal");
      modal.classList.remove("hidden");
    });

  // Excluir Ventas
  document
    .getElementById("exclude-sales-btn")
    .addEventListener("click", function () {
      const selectedSales = Array.from(
        document.querySelectorAll(".sale-checkbox:checked"),
      ).map((cb) => cb.value);
      fetch("/exclude-sales", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sales: selectedSales }),
      }).then(() => {
        location.reload();
      });
    });
});
