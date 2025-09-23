from datetime import datetime
from typing import List
from dateutil.relativedelta import relativedelta

from app import db
from app.models import Sale, Product, SaleDetail
from app.repositories.sales_repository import SalesRepository
from app.utils import (
    group_products,
    calculate_sale_detail_totals,
    format_daily_sales,
    calculate_sales_totals,
)


class SalesReportService:
    def __init__(self):
        self.repository = SalesRepository()

    def get_daily_sales(self, month_str, business_id, specific_business_id=None):
        """Obtiene las ventas diarias agrupadas y procesadas."""
        # Validar el formato del mes
        try:
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
        except ValueError:
            raise ValueError("El mes debe estar en formato YYYY-MM.")

        start_date = selected_month.replace(day=1)
        end_date = start_date + relativedelta(months=1, days=-1)

        # Obtener las ventas del repositorio
        all_daily_sales = self.repository.get_sales_for_month(
            business_id, specific_business_id, start_date, end_date
        )

        # Procesar las ventas
        grouped_sales_by_day = self._group_sales_by_day(all_daily_sales)
        formated_daily_sales = format_daily_sales(grouped_sales_by_day)
        return all_daily_sales, formated_daily_sales

    def get_monthly_totals(self, daily_sales: List[Sale]) -> dict:
        """
        Calcula el total de productos y el importe total para un conjunto de ventas diarias.

        :param daily_sales: Lista de objetos Sale que contienen las ventas diarias.
        :return: Un diccionario con los totales mensuales:
                - total_products: Total de productos vendidos en el período.
                - total_income: Total de ingresos generados en el período.
        """
        total_products = 0
        total_income = 0.0

        for sale in daily_sales:
            # Sumar las cantidades y los ingresos de cada venta
            total_products += sum(detail.quantity for detail in sale.products)
            total_income += sale.total_amount

        return {
            "total_products": total_products,
            "total_income": round(
                total_income, 2
            ),  # Redondear a 2 decimales para moneda
        }

    # Helpers Methods

    def _group_sales_by_day(self, sales):
        """Agrupa las ventas por día."""
        from collections import defaultdict

        sales_by_day = defaultdict(list)
        for sale in sales:
            date_key = sale.date.strftime("%Y-%m-%d")
            sales_by_day[date_key].append(sale)
        return sales_by_day

    def get_inventory_consumption(
        self, month_str: str, business_id: int, specific_business_id: int | None = None
    ) -> dict:
        """
        Calcula el consumo de materias primas (InventoryItem) derivado de las ventas de productos
        durante el mes indicado. Utiliza la relación Product -> ProductDetail (raw_materials)
        para saber cuánta materia prima consume cada unidad vendida.

        Retorna un diccionario donde la clave es el id de InventoryItem y el valor contiene
        nombre, unidad, total_consumed (float) y optionally product_usages (mapping product->qty).
        """
        from collections import defaultdict
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        # Validar y calcular rango de fechas
        try:
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
        except ValueError:
            raise ValueError("El mes debe estar en formato YYYY-MM.")

        start_date = selected_month.replace(day=1)
        end_date = start_date + relativedelta(months=1, days=-1)

        # Obtener ventas del repositorio
        sales = self.repository.get_sales_for_month(
            business_id, specific_business_id, start_date, end_date
        )

        # Estructuras de acumulación
        consumption = defaultdict(
            lambda: {
                "inventory_item_id": None,
                "name": "",
                "unit": "",
                "total_consumed": 0.0,
                "product_usages": defaultdict(float),
            }
        )

        # Para cada venta y cada detalle, multiplicar la cantidad vendida por la cantidad
        # de materia prima requerida por unidad (ProductDetail.quantity)
        for sale in sales:
            for sd in sale.products:
                product = sd.product
                qty_sold = sd.quantity
                # Cada product.raw_materials describe el uso de inventory_item por unidad de producto
                for pd in getattr(product, "raw_materials", []):
                    inv = pd.raw_material
                    if inv is None:
                        continue
                    inv_id = inv.id
                    used_amount = pd.quantity * qty_sold
                    entry = consumption[inv_id]
                    entry["inventory_item_id"] = inv_id
                    entry["name"] = inv.name
                    entry["unit"] = inv.unit
                    entry["total_consumed"] += float(used_amount)
                    entry["product_usages"][product.name] += float(used_amount)

        # Convertir defaultdicts a dicts y product_usages a dict
        result = {}
        for inv_id, data in consumption.items():
            data_copy = dict(data)
            # product_usages es un defaultdict -> convertir
            data_copy["product_usages"] = dict(data_copy["product_usages"])
            # Redondear total_consumed a 4 decimales
            data_copy["total_consumed"] = round(data_copy["total_consumed"], 4)
            result[inv_id] = data_copy

        return result

    def get_inventory_consumption_by_day(
        self, month_str: str, business_id: int, specific_business_id: int | None = None
    ) -> list:
        """
        Calcula el consumo de materias primas por cada día del mes.

        Devuelve una lista de días donde cada día es un dict:
            {"date": "YYYY-MM-DD", "items": [{inventory_item_id, name, unit, total_consumed, product_usages}]}

        Los días con consumo cero no se incluyen.
        """
        from collections import defaultdict
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        # Validar y calcular rango de fechas
        try:
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
        except ValueError:
            raise ValueError("El mes debe estar en formato YYYY-MM.")

        start_date = selected_month.replace(day=1)
        end_date = start_date + relativedelta(months=1, days=-1)

        # Obtener ventas del repositorio
        sales = self.repository.get_sales_for_month(
            business_id, specific_business_id, start_date, end_date
        )

        # Estructura: day_str -> inv_id -> entry
        days = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "inventory_item_id": None,
                    "name": "",
                    "unit": "",
                    "total_consumed": 0.0,
                    "product_usages": defaultdict(float),
                }
            )
        )

        for sale in sales:
            day_key = sale.date.strftime("%Y-%m-%d")
            for sd in sale.products:
                product = sd.product
                qty_sold = sd.quantity
                for pd in getattr(product, "raw_materials", []):
                    inv = pd.raw_material
                    if inv is None:
                        continue
                    inv_id = inv.id
                    used_amount = pd.quantity * qty_sold
                    entry = days[day_key][inv_id]
                    entry["inventory_item_id"] = inv_id
                    entry["name"] = inv.name
                    entry["unit"] = inv.unit
                    entry["total_consumed"] += float(used_amount)
                    entry["product_usages"][product.name] += float(used_amount)

        # Convertir a lista ordenada por fecha
        result = []
        for day, items_map in sorted(days.items()):
            items_list = []
            for inv_id, data in items_map.items():
                data_copy = dict(data)
                data_copy["product_usages"] = dict(data_copy["product_usages"])
                data_copy["total_consumed"] = round(data_copy["total_consumed"], 4)
                items_list.append(data_copy)

            # Ordenar items por nombre
            items_list.sort(key=lambda x: x.get("name") or "")
            result.append({"date": day, "items": items_list})

        return result
