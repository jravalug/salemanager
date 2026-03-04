from app.extensions import db
from app.models import Business, Client, DailyIncome, Sale
from app.services.sale_service import SalesService


class BusinessRulesService:
    INHERITED_FISCAL_FIELDS = (
        "fiscal_street",
        "fiscal_number",
        "fiscal_between_streets",
        "fiscal_apartment",
        "fiscal_district",
        "fiscal_municipality",
        "fiscal_province",
        "fiscal_postal_code",
    )

    def __init__(self):
        """Inicializa dependencias usadas por las reglas de negocio."""
        self.sale_service = SalesService()

    @staticmethod
    def normalize_optional_text(value):
        """Normaliza texto opcional devolviendo `None` cuando está vacío."""
        if value is None:
            return None
        cleaned_value = value.strip()
        return cleaned_value or None

    @staticmethod
    def _is_blank(value):
        """Indica si un valor debe considerarse vacío para herencia de campos."""
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        return False

    @staticmethod
    def snapshot_parent_state(business: Business):
        """Toma una instantánea de campos heredables del negocio padre."""
        if not business.is_general:
            return None

        return {
            "fiscal_street": business.fiscal_street,
            "fiscal_number": business.fiscal_number,
            "fiscal_between_streets": business.fiscal_between_streets,
            "fiscal_apartment": business.fiscal_apartment,
            "fiscal_district": business.fiscal_district,
            "fiscal_municipality": business.fiscal_municipality,
            "fiscal_province": business.fiscal_province,
            "fiscal_postal_code": business.fiscal_postal_code,
            "logo": business.logo,
        }

    def resolve_business_income_defaults(
        self, client: Client | None, business: Business
    ):
        """Resuelve modo y actividad de ingreso por defecto según reglas del cliente."""
        if not client:
            return Business.INCOME_MODE_DAILY, Business.INCOME_ACTIVITY_SALE

        if client.client_type == Client.TYPE_MIPYME:
            default_mode = Business.INCOME_MODE_DETAILED
        elif (
            client.client_type == Client.TYPE_TCP
            and client.accounting_regime == Client.REGIME_FINANCIAL
        ):
            default_mode = Business.INCOME_MODE_DETAILED
        else:
            default_mode = Business.INCOME_MODE_DAILY

        default_activity = (
            business.default_income_activity or Business.INCOME_ACTIVITY_SALE
        )
        return default_mode, default_activity

    def resolve_fiscal_values_from_form(
        self, form, parent_business: Business | None = None
    ):
        """Resuelve valores fiscales del formulario aplicando herencia del padre."""
        fiscal_values = {
            field_name: self.normalize_optional_text(getattr(form, field_name).data)
            for field_name in self.INHERITED_FISCAL_FIELDS
        }

        if parent_business:
            for field_name in self.INHERITED_FISCAL_FIELDS:
                fiscal_values[field_name] = (
                    fiscal_values[field_name] or getattr(parent_business, field_name)
                )

        return fiscal_values

    @staticmethod
    def _resolve_business_scope_ids(business: Business):
        """Devuelve IDs de negocio principal y específico según el alcance."""
        if business.is_general:
            return business.id, None
        return business.parent_business_id, business.id

    @staticmethod
    def _income_location_by_payment_method(payment_method: str | None):
        """Mapea método de pago a ubicación de efectivo/banco en ingresos diarios."""
        return (
            DailyIncome.LOCATION_BANK
            if payment_method in {"transfer", "card", "bank"}
            else DailyIncome.LOCATION_CASH
        )

    @staticmethod
    def _delete_sales_summary_entries_for_business(business_id: int):
        """Elimina ingresos automáticos de resumen de ventas para un negocio."""
        DailyIncome.query.filter_by(
            business_id=business_id,
            source=DailyIncome.SOURCE_SALES_SUMMARY,
        ).delete()

    def _build_sales_by_day_and_location(self, business: Business):
        """Agrupa ventas por día y ubicación de caja/banco para el resumen."""
        sales_by_day_and_location = {}
        main_business_id, specific_business_id = self._resolve_business_scope_ids(business)

        sales_query = Sale.query.filter(Sale.business_id == main_business_id)
        if specific_business_id is not None:
            sales_query = sales_query.filter(Sale.specific_business_id == specific_business_id)

        for sale in sales_query.all():
            location = self._income_location_by_payment_method(sale.payment_method)
            bucket_key = (sale.date, location)
            sales_by_day_and_location[bucket_key] = sales_by_day_and_location.get(
                bucket_key, 0.0
            ) + float(sale.total_amount or 0)

        return sales_by_day_and_location

    def sync_children_inherited_fields(self, parent_business, previous_parent_state):
        """Sincroniza en hijos los campos heredables modificados en el negocio padre."""
        if not parent_business.is_general:
            return

        child_businesses = parent_business.sub_businesses.all()
        if not child_businesses:
            return

        updated_any_child = False

        for child in child_businesses:
            for field_name in self.INHERITED_FISCAL_FIELDS:
                child_value = getattr(child, field_name)
                old_parent_value = previous_parent_state.get(field_name)
                new_parent_value = getattr(parent_business, field_name)

                should_inherit = (
                    self._is_blank(child_value) or child_value == old_parent_value
                )
                if should_inherit and child_value != new_parent_value:
                    setattr(child, field_name, new_parent_value)
                    updated_any_child = True

            old_parent_logo = previous_parent_state.get("logo")
            new_parent_logo = parent_business.logo
            should_inherit_logo = (
                self._is_blank(child.logo) or child.logo == old_parent_logo
            )
            if should_inherit_logo and child.logo != new_parent_logo:
                child.logo = new_parent_logo
                updated_any_child = True

        if updated_any_child:
            db.session.commit()

    def sync_sales_summary_daily_income(self, business):
        """Regenera ingresos diarios automáticos a partir de ventas detalladas."""
        if not business:
            return

        if business.income_entry_mode != Business.INCOME_MODE_DETAILED:
            return

        main_business_id, specific_business_id = self._resolve_business_scope_ids(business)
        sales_scope = self.sale_service.generate_monthly_totals_sales(
            business_id=main_business_id,
            specific_business_id=specific_business_id,
        )

        if not sales_scope:
            self._delete_sales_summary_entries_for_business(business.id)
            db.session.commit()
            return

        sales_by_day_and_location = self._build_sales_by_day_and_location(business)

        self._delete_sales_summary_entries_for_business(business.id)

        for (day, location), amount in sales_by_day_and_location.items():
            db.session.add(
                DailyIncome(
                    business_id=business.id,
                    date=day,
                    income_type=DailyIncome.TYPE_INCOME_OBTAINED,
                    activity=business.default_income_activity
                    or DailyIncome.ACTIVITY_SALE,
                    amount=round(amount, 2),
                    description="Resumen automático de ventas del día",
                    cash_location=location,
                    source=DailyIncome.SOURCE_SALES_SUMMARY,
                )
            )

        db.session.commit()
