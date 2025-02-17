from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter


def generate_excel_sales_by_date(business, sales_data, period):
    # Crear un archivo Excel
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Resumen de Ventas"

    # Definir estilos
    title_font = Font(size=16, bold=True, color="000000")
    subtitle_font = Font(size=14, bold=True, color="000000")
    header_font = Font(bold=True, color="FFFFFF")
    bold_font = Font(bold=True, size=12, color="000000")
    total_font = Font(bold=True, size=12, color="00B050")
    alignment_center = Alignment(horizontal="center", vertical="center")
    alignment_left = Alignment(horizontal="left", vertical="center")
    alignment_right = Alignment(horizontal="right", vertical="center")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    header_fill = PatternFill(
        start_color="4F81BD", end_color="4F81BD", fill_type="solid"
    )

    # Encabezado del reporte
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=3)
    sheet.cell(row=1, column=1, value=f"Reporte de Ventas - {business.name}").font = (
        title_font
    )
    sheet.cell(row=1, column=1).alignment = alignment_center

    sheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=3)
    sheet.cell(row=2, column=1, value=f"Mes: {period}").font = subtitle_font
    sheet.cell(row=2, column=1).alignment = alignment_center

    # Espacio en blanco
    sheet.append([])
    sheet.append([])

    # Resumen general
    total_products = sum(day["total_products"] for day in sales_data)
    total_income = sum(day["total_income"] for day in sales_data)

    sheet.append(["Resumen General"])
    sheet.append(["Total de Productos Vendidos:", total_products])
    sheet.append(["Total de Ingresos Generados:", total_income])

    # Aplicar formato de moneda al total de ingresos
    sheet.cell(row=5, column=1).font = subtitle_font
    sheet.cell(row=6, column=1).font = bold_font
    sheet.cell(row=7, column=1).font = bold_font
    sheet.cell(row=6, column=2).font = bold_font
    sheet.cell(row=7, column=2).number_format = '"$ "#,##0.00'  # Formato de moneda
    sheet.cell(row=7, column=2).font = total_font

    # Espacio en blanco
    sheet.append([])
    sheet.append([])

    # Encabezados de la tabla
    headers = ["FECHA", "TOTAL PRODUCTOS", "IMPORTE TOTAL"]
    sheet.append(headers)

    # Aplicar estilos a los encabezados
    for col_num, header in enumerate(headers, 1):
        cell = sheet.cell(row=10, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = alignment_center

    # Rellenar el archivo con los datos
    for idx, day in enumerate(sales_data, start=11):
        date = day["date"]
        total_products = day["total_products"]
        total_income = day["total_income"]

        row = [date, total_products, total_income]  # Mantener el valor numérico
        sheet.append(row)

        # Aplicar formato de moneda al importe total
        sheet.cell(row=idx, column=3).number_format = (
            '"$ "#,##0.00'  # Formato de moneda
        )
        sheet.cell(row=idx, column=3).font = bold_font

        # Aplicar bordes a las celdas
        for col_num, value in enumerate(row, 1):
            cell = sheet.cell(row=idx, column=col_num)
            cell.border = border
            cell.alignment = alignment_center
            if col_num == 3:
                cell.alignment = alignment_right

    # Ajustar el ancho de las columnas automáticamente
    for col in range(1, len(headers) + 1):
        column = get_column_letter(col)
        sheet.column_dimensions[column].width = 27

    # Guardar el archivo en memoria
    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)

    return excel_file
