from typing import Dict, Optional
from datetime import date, datetime
from collections import defaultdict

from sqlalchemy import desc, func, inspect
from sqlalchemy.orm import joinedload
from dateutil.relativedelta import relativedelta

from app import db
from app.forms import (
    IncomeForm,
    IncomeDetailForm,
    UpdateIncomeDetailForm,
    RemoveIncomeDetailForm,
)
from app.models import (
    Sale,
    Product,
    SaleDetail,
    DailyIncome,
    IncomeEvent,
    CollectionReceipt,
)
from app.models.business import Business
from app.repositories.income_repository import IncomeRepository
from app.services.business_service import BusinessService
from app.services.income_posting_service import IncomePostingService
from app.utils.slug_utils import get_business_by_slugs
from app.utils.income_utils import calculate_month_totals, group_sales_by_month


class IncomeManagementService:
    """
    Servicio para manejar las operaciones relacionadas con ingresos detallados.
    """

    MONTH_NAMES = (
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    )

    def __init__(self):
        """Inicializa dependencias del servicio de ventas."""
        self.repository = IncomeRepository()
        self.business_service = BusinessService()

    # Métodos principales para operaciones CRUD de income

    def get_income(self, income_id, business_id):
        """Obtiene los detalles completos de un ingreso con sus relaciones."""
        return (
            Sale.query.options(joinedload(Sale.products).joinedload(SaleDetail.product))
            .filter(Sale.id == income_id, Sale.business_id == business_id)
            .first_or_404()
        )

    def get_sale(self, sale_id, business_id):
        """Alias temporal para compatibilidad retroactiva."""
        return self.get_income(sale_id, business_id)

    def resolve_business_and_filters(self, client_slug: str, business_slug: str):
        """Resuelve negocio por slugs y devuelve filtros de consulta asociados."""
        business = get_business_by_slugs(client_slug, business_slug)
        if not business:
            raise ValueError("Negocio no encontrado")

        filters = self.business_service.get_parent_filters(business=business)
        return business, filters

    def resolve_income_scope(
        self,
        client_slug: str,
        business_slug: str,
        income_id: int,
    ):
        """Resuelve negocio, filtros e ingreso concreto dentro del alcance válido."""
        business, filters = self.resolve_business_and_filters(
            client_slug, business_slug
        )
        income = self.get_income(income_id, filters["business_id"])
        return business, filters, income

    def resolve_sale_scope(self, client_slug: str, business_slug: str, sale_id: int):
        """Alias temporal para compatibilidad retroactiva."""
        return self.resolve_income_scope(client_slug, business_slug, sale_id)

    @staticmethod
    def get_incomes_api_data(business_id: int):
        """Devuelve ingresos serializados para consumo de endpoints API."""
        sales = Sale.query.filter_by(business_id=business_id).all()
        return [
            {
                "id": sale.id,
                "date": sale.date.strftime("%Y-%m-%d"),
                "total": sum(
                    (
                        sale_product.total_price
                        if sale_product.total_price is not None
                        else (sale_product.quantity or 0)
                        * (
                            (sale_product.product.price if sale_product.product else 0)
                            or 0
                        )
                    )
                    for sale_product in sale.products
                ),
            }
            for sale in sales
        ]

    def get_sales_api_data(self, business_id: int):
        """Alias temporal para compatibilidad retroactiva."""
        return self.get_incomes_api_data(business_id)

    def get_available_products(self, business_id):
        """Obtiene los productos disponibles para un negocio"""
        return (
            Product.query.filter_by(business_id=business_id)
            .order_by(Product.name.asc())
            .all()
        )

    def get_income_details(self, income_id):
        """Obtiene los productos de un ingreso específico."""
        return SaleDetail.query.filter_by(sale_id=income_id).join(Product).all()

    def get_sale_details(self, sale_id):
        """Alias temporal para compatibilidad retroactiva."""
        return self.get_income_details(sale_id)

    def get_income_detail_for_income(
        self, income_id: int, sale_detail_id: int
    ) -> SaleDetail:
        """Obtiene un detalle validando que pertenezca al ingreso indicado."""
        return SaleDetail.query.filter_by(
            id=sale_detail_id, sale_id=income_id
        ).first_or_404()

    def get_sale_detail_for_sale(self, sale_id: int, sale_detail_id: int) -> SaleDetail:
        """Alias temporal para compatibilidad retroactiva."""
        return self.get_income_detail_for_income(sale_id, sale_detail_id)

    def handle_remove_product_form(self, income: Sale, sale_detail_id: int) -> Product:
        """Procesa formulario para remover un producto de un ingreso."""
        sale_detail = self.get_income_detail_for_income(
            income_id=income.id,
            sale_detail_id=sale_detail_id,
        )
        return self.remove_product_from_income(income=income, sale_detail=sale_detail)

    def handle_add_product_form(
        self,
        income: Sale,
        product_id: int,
        quantity: int,
        discount: float,
    ) -> SaleDetail:
        """Procesa formulario para agregar un producto a un ingreso."""
        return self.add_product_to_income(
            income=income,
            product_id=product_id,
            quantity=quantity,
            discount=discount,
        )

    def handle_update_product_form(
        self,
        income: Sale,
        sale_detail_id: int,
        quantity: int,
        discount: float,
    ) -> SaleDetail:
        """Procesa formulario para actualizar cantidad/descuento de un producto vendido."""
        sale_detail = self.get_income_detail_for_income(
            income_id=income.id,
            sale_detail_id=sale_detail_id,
        )
        return self.update_income_detail(
            income=income,
            sale_detail=sale_detail,
            quantity=quantity,
            discount=discount,
        )

    @staticmethod
    def parse_month_range(month_param: str | None):
        """Resuelve mes seleccionado y su rango de fechas opcional."""
        selected_month = month_param if month_param else None
        date_range = None
        if not month_param:
            return selected_month, date_range

        selected = datetime.strptime(month_param, "%Y-%m").date()
        start_date = selected.replace(day=1)
        end_date = start_date + relativedelta(months=1, days=-1)
        return selected_month, (start_date, end_date)

    @staticmethod
    def build_months_display(months: list[str]):
        """Convierte meses `YYYY-MM` a etiquetas legibles para UI."""
        months_display = []
        for month in months:
            try:
                dt = datetime.strptime(month, "%Y-%m").date()
                label = f"{IncomeManagementService.MONTH_NAMES[dt.month - 1]} {dt.year}"
            except Exception:
                label = month
            months_display.append((month, label))
        return months_display

    @staticmethod
    def _resolve_month_navigation(selected_month: str | None, months: list[str]):
        """Calcula navegación de mes anterior/siguiente para la vista."""
        prev_month = None
        next_month = None
        display_month_name = "Todos"

        if not selected_month or selected_month not in months:
            return prev_month, next_month, display_month_name

        try:
            idx = months.index(selected_month)
            if idx + 1 < len(months):
                prev_month = months[idx + 1]
            if idx - 1 >= 0:
                next_month = months[idx - 1]
            display_month_name = IncomeManagementService.build_months_display(
                [selected_month]
            )[0][1]
        except Exception:
            display_month_name = selected_month

        return prev_month, next_month, display_month_name

    @staticmethod
    def _aggregate_daily_sales(sales_by_months: dict):
        """Consolida ventas diarias provenientes de múltiples meses."""
        daily_sales = {}
        for _, dates in sales_by_months.items():
            for date_key, data in dates.items():
                if date_key in daily_sales:
                    daily_sales[date_key]["total_products"] += data.get(
                        "total_products", 0
                    )
                    daily_sales[date_key]["total_income"] += data.get("total_income", 0)
                    daily_sales[date_key]["sales"].extend(data.get("sales", []))
                else:
                    daily_sales[date_key] = {
                        "total_products": data.get("total_products", 0),
                        "total_income": data.get("total_income", 0),
                        "sales": list(data.get("sales", [])),
                    }
        return daily_sales

    @staticmethod
    def _load_daily_income_context(business_id: int, date_range):
        """Carga ingresos diarios con y sin filtro mensual para el contexto."""
        daily_query = DailyIncome.query.filter_by(business_id=business_id)
        all_daily_income_unfiltered = daily_query.order_by(
            DailyIncome.date.desc(), DailyIncome.id.desc()
        ).all()
        months = sorted(
            {
                income.date.strftime("%Y-%m")
                for income in all_daily_income_unfiltered
                if income.date
            },
            reverse=True,
        )

        if date_range:
            all_daily_income = (
                daily_query.filter(
                    DailyIncome.date.between(date_range[0], date_range[1])
                )
                .order_by(DailyIncome.date.desc(), DailyIncome.id.desc())
                .all()
            )
        else:
            all_daily_income = all_daily_income_unfiltered

        return all_daily_income_unfiltered, all_daily_income, months

    @staticmethod
    def _load_sales_context(filters: dict, date_range):
        """Carga ventas con y sin filtro mensual para el contexto de listado."""
        all_sales_unfiltered = (
            Sale.query.options(joinedload(Sale.products))
            .filter_by(**filters)
            .order_by(Sale.date.desc())
            .all()
        )
        sales_by_months_unfiltered = group_sales_by_month(all_sales_unfiltered)
        months = sorted(list(sales_by_months_unfiltered.keys()), reverse=True)

        if date_range:
            all_sales = (
                Sale.query.options(joinedload(Sale.products))
                .filter_by(**filters)
                .filter(Sale.date.between(date_range[0], date_range[1]))
                .order_by(Sale.date.desc())
                .all()
            )
        else:
            all_sales = all_sales_unfiltered

        return all_sales_unfiltered, all_sales, months

    def create_daily_income(self, business: Business, form) -> DailyIncome:
        """Registra un ingreso diario manual para el negocio indicado."""
        income_type = (
            DailyIncome.TYPE_NON_TAXABLE
            if form.mark_non_taxable.data
            else DailyIncome.TYPE_INCOME_OBTAINED
        )
        new_income = DailyIncome(
            business_id=business.id,
            date=form.date.data,
            income_type=income_type,
            activity=form.activity.data,
            amount=float(form.amount.data or 0),
            description=(form.description.data or "").strip() or None,
            cash_location=form.cash_location.data,
            source=DailyIncome.SOURCE_MANUAL,
        )
        db.session.add(new_income)
        if inspect(db.session.get_bind()).has_table("income_event"):
            payment_channel = (
                IncomeEvent.CHANNEL_BANK_TRANSFER
                if form.cash_location.data == DailyIncome.LOCATION_BANK
                else IncomeEvent.CHANNEL_CASH
            )
            collection_status = (
                IncomeEvent.STATUS_PENDING
                if payment_channel == IncomeEvent.CHANNEL_BANK_TRANSFER
                else IncomeEvent.STATUS_IMMEDIATE
            )
            collected_date = (
                None
                if collection_status == IncomeEvent.STATUS_PENDING
                else form.date.data
            )
            income_event = IncomeEvent(
                business_id=business.id,
                event_date=form.date.data,
                amount=float(form.amount.data or 0),
                origin_type=IncomeEvent.ORIGIN_MANUAL,
                payment_channel=payment_channel,
                collection_status=collection_status,
                collected_date=collected_date,
                description=(form.description.data or "").strip() or None,
                source_ref=f"daily_income:manual:{form.date.data}",
            )
            db.session.add(income_event)
            db.session.flush()
            IncomePostingService().post_event(income_event, commit=False)
        db.session.commit()
        return new_income

    @staticmethod
    def get_pending_income_events(business_id: int) -> list[IncomeEvent]:
        """Devuelve ingresos pendientes por acreditar para un negocio."""
        return (
            IncomeEvent.query.filter_by(
                business_id=business_id,
                collection_status=IncomeEvent.STATUS_PENDING,
            )
            .order_by(IncomeEvent.event_date.asc(), IncomeEvent.id.asc())
            .all()
        )

    @staticmethod
    def _parse_collected_date(collected_date_value) -> date:
        if not collected_date_value:
            return datetime.today().date()

        if isinstance(collected_date_value, date):
            return collected_date_value

        return datetime.strptime(str(collected_date_value), "%Y-%m-%d").date()

    def reconcile_income_event(
        self,
        business_id: int,
        income_event_id: int,
        bank_operation_number: str,
        collected_date_value=None,
        reconciled_by: str | None = None,
        bank_name: str | None = None,
    ) -> IncomeEvent:
        """Concilia un ingreso pendiente y aplica posting contable según régimen."""
        operation_number = (bank_operation_number or "").strip()
        if not operation_number:
            raise ValueError("El número de operación bancaria es obligatorio.")

        income_event = IncomeEvent.query.filter_by(
            id=income_event_id,
            business_id=business_id,
        ).first()
        if not income_event:
            raise ValueError("Ingreso pendiente no encontrado.")

        if income_event.collection_status != IncomeEvent.STATUS_PENDING:
            raise ValueError("Solo se pueden conciliar ingresos pendientes.")

        collected_date = self._parse_collected_date(collected_date_value)

        income_event.collection_status = IncomeEvent.STATUS_COLLECTED
        income_event.collected_date = collected_date
        income_event.bank_operation_number = operation_number
        income_event.reconciled_by = (reconciled_by or "").strip() or None
        income_event.reconciled_at = datetime.utcnow()

        receipt = CollectionReceipt.query.filter_by(
            income_event_id=income_event.id
        ).first()
        if not receipt:
            receipt = CollectionReceipt(
                income_event_id=income_event.id,
                bank_operation_number=operation_number,
                collected_date=collected_date,
                bank_name=(bank_name or "").strip() or None,
                reconciled_by=income_event.reconciled_by,
            )
            db.session.add(receipt)
        else:
            receipt.bank_operation_number = operation_number
            receipt.collected_date = collected_date
            receipt.bank_name = (bank_name or "").strip() or None
            receipt.reconciled_by = income_event.reconciled_by

        IncomePostingService().post_event(income_event, commit=False)
        db.session.commit()

        return income_event

    @staticmethod
    def build_income_summaries(daily_sales: dict):
        """Construye resúmenes por ingreso agrupando productos y totales."""
        income_summaries = {}
        for _, data in daily_sales.items():
            for sale in data.get("sales", []):
                summary = {}
                for sale_detail in getattr(sale, "products", []):
                    try:
                        product_name = (
                            sale_detail.product.name
                            if sale_detail.product
                            else f"#{sale_detail.product_id}"
                        )
                    except Exception:
                        product_name = f"#{sale_detail.product_id}"

                    if product_name in summary:
                        summary[product_name]["quantity"] += sale_detail.quantity or 0
                        summary[product_name]["total_price"] += (
                            sale_detail.total_price or 0
                        )
                    else:
                        summary[product_name] = {
                            "quantity": sale_detail.quantity or 0,
                            "total_price": sale_detail.total_price or 0,
                            "unit_price": sale_detail.unit_price or 0,
                        }

                income_summaries[sale.id] = [
                    {
                        "name": key,
                        "quantity": value["quantity"],
                        "total_price": value["total_price"],
                        "unit_price": value["unit_price"],
                    }
                    for key, value in summary.items()
                ]
        return income_summaries

    def build_sale_summaries(self, daily_sales: dict):
        """Alias temporal para compatibilidad retroactiva."""
        return self.build_income_summaries(daily_sales)

    def build_income_list_context(
        self,
        business: Business,
        filters: dict,
        month_param: str | None,
    ):
        """Arma el contexto completo de la vista de listado de ingresos."""
        is_daily_mode = business.income_entry_mode == Business.INCOME_MODE_DAILY
        all_sales_unfiltered = []
        all_daily_income_unfiltered = []
        months = []

        selected_month, date_range = self.parse_month_range(month_param)
        all_sales = []
        all_daily_income = []

        if is_daily_mode:
            (
                all_daily_income_unfiltered,
                all_daily_income,
                months,
            ) = self._load_daily_income_context(
                business_id=business.id,
                date_range=date_range,
            )
        else:
            all_sales_unfiltered, all_sales, months = self._load_sales_context(
                filters=filters,
                date_range=date_range,
            )

        months_display = self.build_months_display(months)

        sales_by_months = group_sales_by_month(all_sales) if not is_daily_mode else {}
        month_totals = (
            calculate_month_totals(sales_by_months) if not is_daily_mode else {}
        )

        daily_income_by_month = defaultdict(float)
        if is_daily_mode:
            for income in all_daily_income_unfiltered:
                if income.date:
                    daily_income_by_month[income.date.strftime("%Y-%m")] += float(
                        income.amount or 0
                    )

        daily_sales = (
            self._aggregate_daily_sales(sales_by_months) if not is_daily_mode else {}
        )

        daily_sales_sorted = sorted(
            daily_sales.items(), key=lambda item: item[0], reverse=True
        )
        income_summaries = (
            self.build_income_summaries(daily_sales) if not is_daily_mode else {}
        )

        prev_month, next_month, display_month_name = self._resolve_month_navigation(
            selected_month=selected_month,
            months=months,
        )

        current_total = (
            sum(float(item.amount or 0) for item in all_daily_income)
            if is_daily_mode
            else (
                month_totals.get(selected_month, 0)
                if selected_month
                else sum(month_totals.values())
            )
        )

        return {
            "is_daily_mode": is_daily_mode,
            "sales_by_months": sales_by_months,
            "month_totals": month_totals,
            "daily_income_by_month": daily_income_by_month,
            "all_daily_income": all_daily_income,
            "months": months,
            "months_display": months_display,
            "all_sales": all_sales,
            "current_total": current_total,
            "selected_month": selected_month,
            "daily_sales_sorted": daily_sales_sorted,
            "prev_month": prev_month,
            "next_month": next_month,
            "display_month_name": display_month_name,
            "income_summaries": income_summaries,
            "sale_summaries": income_summaries,
        }

    def build_sales_list_context(
        self,
        business: Business,
        filters: dict,
        month_param: str | None,
    ):
        """Alias temporal para compatibilidad retroactiva."""
        return self.build_income_list_context(business, filters, month_param)

    def build_income_details_context(self, income: Sale, filters: dict):
        """Prepara formularios y detalles requeridos por la vista de un ingreso."""
        add_product_form = IncomeDetailForm(prefix="add_product")
        update_product_form = UpdateIncomeDetailForm(prefix="update_product")
        remove_product_form = RemoveIncomeDetailForm(prefix="remove_product")
        update_sale_form = IncomeForm(
            parent_business_id=filters["business_id"],
            obj=income,
            prefix="update_sale",
        )
        add_sale_form = IncomeForm(
            parent_business_id=filters["business_id"],
            prefix="add_sale",
        )

        add_product_form.set_product_choices(
            self.get_available_products(filters["business_id"])
        )

        sale_details = self.get_income_details(income.id)

        return {
            "add_product_form": add_product_form,
            "update_product_form": update_product_form,
            "remove_product_form": remove_product_form,
            "update_sale_form": update_sale_form,
            "add_sale_form": add_sale_form,
            "sale_details": sale_details,
            "income_details": sale_details,
        }

    def build_sale_details_context(self, sale: Sale, filters: dict):
        """Alias temporal para compatibilidad retroactiva."""
        return self.build_income_details_context(sale, filters)

    def add_income(self, business: Business, form: IncomeForm) -> Sale:
        """
        Crea una nueva venta asociada a un negocio.


        Args:
            business (Business): Id del negocio al que pertenece la venta.
            form (IncomeForm): Campos y valores para crear el ingreso.

        Returns:
            Sale: El objeto Venta recién generado.
        """
        business_filter = self.business_service.get_parent_filters(business)

        if business.is_general:
            specific_business_id = form.specific_business_id.data
        else:
            specific_business_id = business_filter["specific_business_id"]

        # Convertir el formulario en un diccionario
        data = {
            "sale_number": form.sale_number.data,
            "date": form.date.data,
            "payment_method": form.payment_method.data,
            "status": form.status.data,
            "excluded": form.excluded.data,
            "discount": form.discount.data or 0,
            "tax": form.tax.data or 0,
            "subtotal_amount": 0,
            "total_amount": 0,
            "specific_business_id": specific_business_id,
        }
        return self.repository.add_sale(business_filter["business_id"], **data)

    def add_sale(self, business: Business, form: IncomeForm) -> Sale:
        """Alias temporal para compatibilidad retroactiva."""
        return self.add_income(business, form)

    def update_income(self, income: Sale, form: IncomeForm):
        """
        Actualiza una venta existente con los datos proporcionados en el formulario.

        Args:
            sale (Sale): Instancia de Sale a actualizar
            form (IncomeForm): Formulario con los nuevos datos validados

        Returns:
            Sale: Instancia actualizada de Sale
        """
        # Convertir el formulario en un diccionario
        data = {
            "sale_number": form.sale_number.data,
            "date": form.date.data,
            "payment_method": form.payment_method.data,
            "status": form.status.data,
            "excluded": form.excluded.data,
            "discount": form.discount.data or 0,
            "tax": form.tax.data or 0,
            "specific_business_id": form.specific_business_id.data,
        }

        return self.repository.update_sale(income, **data)

    def update_sale(self, sale: Sale, form: IncomeForm):
        """Alias temporal para compatibilidad retroactiva."""
        return self.update_income(sale, form)

    def add_product_to_income(
        self, income: Sale, product_id: int, quantity: int, discount: float
    ) -> SaleDetail:
        """
        Agrega un producto a una venta existente

        Args:
            sale (Sale): Instancia de Sale a actualizar
            product_id (int): Id del producto
            quantity (int): Cantidad del producto
            discount (float): Descuento aplicado al producto en la venta
        Returns:
            SaleDetail: El objeto SaleDetail actualizado.
        """
        product = Product.query.get_or_404(product_id)

        return self.repository.add_sale_detail(
            sale_id=income.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price,
            discount=discount or 0.0,
            total_price=self._calculate_income_detail_total(
                product.price, quantity, discount
            ),
        )

    def add_product_to_sale(
        self, sale: Sale, product_id: int, quantity: int, discount: float
    ) -> SaleDetail:
        """Alias temporal para compatibilidad retroactiva."""
        return self.add_product_to_income(sale, product_id, quantity, discount)

    def update_income_detail(
        self,
        income: Sale,
        sale_detail: SaleDetail,
        quantity: int,
        discount: float,
    ) -> SaleDetail:
        """
        Actualiza un producto en una venta

        Args:
            sale (Sale): Instancia de Sale a actualizar
            sale_detail (SaleDetail): El objeto SaleDetail a actualizar
            quantity (int): Cantidad del producto
            discount (float): Descuento aplicado al producto en la venta

        Returns:
            SaleDetail: El objeto SaleDetail actualizado.
        """
        if sale_detail.unit_price and sale_detail.unit_price > 0:
            unit_price = sale_detail.unit_price
        else:
            unit_price = sale_detail.product.price

        return self.repository.update_sale_detail(
            sale_id=income.id,
            sale_detail_id=sale_detail.id,
            quantity=quantity,
            unit_price=unit_price,
            discount=discount or 0.0,
            total_price=self._calculate_income_detail_total(
                unit_price, quantity, discount
            ),
        )

    def update_sale_detail(
        self,
        sale: Sale,
        sale_detail: SaleDetail,
        quantity: int,
        discount: float,
    ) -> SaleDetail:
        """Alias temporal para compatibilidad retroactiva."""
        return self.update_income_detail(sale, sale_detail, quantity, discount)

    def remove_product_from_income(
        self, income: Sale, sale_detail: SaleDetail
    ) -> Product:
        """
        Elimina un producto de una venta

        Args:
            sale (Sale): Instancia de Sale a actualizar
            sale_detail (SaleDetail): El objeto SaleDetail a eliminar
        Returns:
            Product: El objeto Product que se eliminó de la venta.
        """
        removed_product = Product.query.get_or_404(sale_detail.product_id)
        self.repository.remove_sale_detail(income.id, sale_detail.id)
        return removed_product

    def remove_product_from_sale(self, sale: Sale, sale_detail: SaleDetail) -> Product:
        """Alias temporal para compatibilidad retroactiva."""
        return self.remove_product_from_income(sale, sale_detail)

    # Helper methods
    def _calculate_income_detail_total(
        self, unit_price: float, quantity: int, discount: float
    ) -> float:
        """
        Calcula el total por producto considerando descuentos

        Args:
            unit_price (float): Precio unitario del producto
            quantity (int): Cantidad del producto
            discount (float): Descuento aplicado al producto

        Returns:
            float: Total por producto
        """
        return round(unit_price * quantity * (1 - (discount or 0.0)), 2)

    def _calculate_sale_detail_total(
        self, unit_price: float, quantity: int, discount: float
    ) -> float:
        """Alias temporal para compatibilidad retroactiva."""
        return self._calculate_income_detail_total(unit_price, quantity, discount)

    @staticmethod
    def generate_monthly_income_totals(
        business_id: int,
        specific_business_id: Optional[int] = None,  # Parámetro opcional
    ) -> Dict[str, float]:
        """
        Genera totales mensuales de ventas para un negocio.

        Args:
            business_id (int): Id del negocio
            specific_business_id (int): Id del negocio específico

        Returns:
            Dict[str, float]: Ventas mensuales para el negocio.
        """
        try:
            # Construir la consulta base
            query = db.session.query(
                func.strftime("%Y-%m", Sale.date).label("month"),
                func.sum(Sale.total_amount).label("total"),
            ).filter(Sale.business_id == business_id)

            # Aplicar filtro de sub negocio si existe
            if specific_business_id is not None:
                query = query.filter(Sale.specific_business_id == specific_business_id)

            # Agrupar y ordenar
            return (
                query.group_by(func.strftime("%Y-%m", Sale.date))
                .order_by(desc(func.strftime("%Y-%m", Sale.date)))
                .all()
            )

        except Exception as e:
            raise RuntimeError(f"Error generando totales mensuales: {str(e)}")

    @staticmethod
    def generate_monthly_totals_sales(
        business_id: int,
        specific_business_id: Optional[int] = None,
    ) -> Dict[str, float]:
        """Alias temporal para compatibilidad retroactiva."""
        return IncomeManagementService.generate_monthly_income_totals(
            business_id=business_id,
            specific_business_id=specific_business_id,
        )
