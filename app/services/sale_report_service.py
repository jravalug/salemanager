from datetime import datetime
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

    def get_daily_sales(self, business_id, month_str, excluded_sales):
        """Obtiene las ventas diarias agrupadas y procesadas."""
        # Validar el formato del mes
        try:
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
        except ValueError:
            raise ValueError("El mes debe estar en formato YYYY-MM.")

        start_date = selected_month.replace(day=1)
        end_date = start_date + relativedelta(months=1, days=-1)

        # Obtener las ventas del repositorio
        all_dayly_sales = self.repository.get_sales_for_month(
            business_id, start_date, end_date
        )
        filtered_sales = [
            sale for sale in all_dayly_sales if sale.id not in excluded_sales
        ]

        # Procesar las ventas
        filtered_sales_by_day = self._group_sales_by_day(filtered_sales)
        filtered_daily_sales = format_daily_sales(filtered_sales_by_day)
        return all_dayly_sales, filtered_daily_sales

    def get_monthly_totals(self, business_id, month_str, excluded_sales):
        """
        Calcula el total de productos y el importe total para un mes específico.

        :param business_id: ID del negocio.
        :param month_str: Mes en formato YYYY-MM.
        :param excluded_sales: Lista de IDs de ventas excluidas.
        :return: Un diccionario con los totales mensuales:
                 - total_products: Total de productos vendidos en el mes.
                 - total_income: Total de ingresos generados en el mes.
        """
        # Validar el formato del mes
        try:
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
        except ValueError:
            raise ValueError("El mes debe estar en formato YYYY-MM.")

        start_date = selected_month.replace(day=1)
        end_date = start_date + relativedelta(months=1, days=-1)

        # Obtener todas las ventas del mes
        all_sales = self.repository.get_sales_for_month(
            business_id, start_date, end_date
        )

        # Filtrar las ventas excluidas
        filtered_sales = [sale for sale in all_sales if sale.id not in excluded_sales]

        # Calcular totales
        totals = calculate_sales_totals(filtered_sales)

        return {
            "total_products": totals["total_products"],
            "total_income": totals["total_income"],
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
