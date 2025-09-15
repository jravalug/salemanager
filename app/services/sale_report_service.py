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
