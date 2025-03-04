import { DataTable } from "../../../node_modules/simple-datatables/dist/module.js";

const businessId = document.getElementById("business-id").value;

fetch(`/api/business/${businessId}/product/products`)
  .then((response) => response.json())
  .then((data) => {
    window.dt = new DataTable("#demo-table", {
      data: {
        headings: [
          {
            text: "ID",
            data: "id",
          },
          {
            text: "NOMBRE",
            data: "name",
          },
          {
            text: "PRECIO",
            data: "price",
          },
          {
            text: "CATEGORIA",
            data: "category",
          },
        ],
        data,
      },
    });
  });
