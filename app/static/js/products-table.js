import { DataTable } from "../../../node_modules/simple-datatables/dist/module.js";

const clientSlug = document.getElementById("client-slug").value;
const businessSlug = document.getElementById("business-slug").value;

fetch(`/api/clients/${clientSlug}/business/${businessSlug}/product/products`)
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
