if (
      document.getElementById("product_filter-table") &&
      typeof simpleDatatables.DataTable !== "undefined"
    ) {
      const dataTable = new simpleDatatables.DataTable("#product_filter-table", {
        paging: true,
        perPage: 5,
        perPageSelect: [5, 10, 15, 20, 25],
        sortable: true,
        template: (options, dom) => `<div class='${options.classes.top}'>
            ${
            options.paging && options.perPageSelect ?
                `<div class='${options.classes.dropdown}'>
                    <label>
                        <select class='${options.classes.selector}'></select> ${options.labels.perPage}
                    </label>
                </div>` :
                ""
        }
            ${
            options.searchable ?
                `<div class='${options.classes.search}'>
                    <input class='${options.classes.input}' placeholder='${options.labels.placeholder}' type='search' title='${options.labels.searchTitle}'${dom.id ? ` aria-controls="${dom.id}"` : ""}>
                </div>` :
                ""
        }
        </div>
        <div class='${options.classes.container}'${options.scrollY.length ? ` style='height: ${options.scrollY}; overflow-Y: auto;'` : ""}></div>
        <div class='${options.classes.bottom}'>
            ${
            options.paging ?
                `<div class='${options.classes.info}'></div>` :
                ""
        }
            <nav class='${options.classes.pagination}'></nav>
        </div>`,
    });
    }