document.addEventListener("DOMContentLoaded", function () {
  // Inicializar DataTables
  const table = new simpleDatatables.DataTable("#sales-table", {
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

  // Abrir Modal
  document.getElementById("open-modal-btn").addEventListener("click", function () {
    const modal = document.getElementById("exclude-sales-modal");
    modal.classList.remove("hidden");
  });

  // Excluir Ventas
  document.getElementById("exclude-sales-btn").addEventListener("click", function () {
    const selectedSales = Array.from(document.querySelectorAll(".sale-checkbox:checked")).map(cb => cb.value);
    fetch("/exclude-sales", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sales: selectedSales }),
    }).then(() => {
      location.reload();
    });
  });
});