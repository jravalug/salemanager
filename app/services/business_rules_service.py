from app.extensions import db
from app.models import Business, Client, DailyIncome, Sale
from app.services.sale_service import SalesService


class BusinessRulesService:
    def __init__(self):
        self.sale_service = SalesService()

    @staticmethod
    def normalize_optional_text(value):
        if value is None:
            return None
        cleaned_value = value.strip()
        return cleaned_value or None

    @staticmethod
    def _is_blank(value):
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        return False

    @staticmethod
    def snapshot_parent_state(business: Business):
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
        fiscal_street = self.normalize_optional_text(form.fiscal_street.data)
        fiscal_number = self.normalize_optional_text(form.fiscal_number.data)
        fiscal_between_streets = self.normalize_optional_text(
            form.fiscal_between_streets.data
        )
        fiscal_apartment = self.normalize_optional_text(form.fiscal_apartment.data)
        fiscal_district = self.normalize_optional_text(form.fiscal_district.data)
        fiscal_municipality = self.normalize_optional_text(
            form.fiscal_municipality.data
        )
        fiscal_province = self.normalize_optional_text(form.fiscal_province.data)
        fiscal_postal_code = self.normalize_optional_text(form.fiscal_postal_code.data)

        if parent_business:
            fiscal_street = fiscal_street or parent_business.fiscal_street
            fiscal_number = fiscal_number or parent_business.fiscal_number
            fiscal_between_streets = (
                fiscal_between_streets or parent_business.fiscal_between_streets
            )
            fiscal_apartment = fiscal_apartment or parent_business.fiscal_apartment
            fiscal_district = fiscal_district or parent_business.fiscal_district
            fiscal_municipality = (
                fiscal_municipality or parent_business.fiscal_municipality
            )
            fiscal_province = fiscal_province or parent_business.fiscal_province
            fiscal_postal_code = (
                fiscal_postal_code or parent_business.fiscal_postal_code
            )

        return {
            "fiscal_street": fiscal_street,
            "fiscal_number": fiscal_number,
            "fiscal_between_streets": fiscal_between_streets,
            "fiscal_apartment": fiscal_apartment,
            "fiscal_district": fiscal_district,
            "fiscal_municipality": fiscal_municipality,
            "fiscal_province": fiscal_province,
            "fiscal_postal_code": fiscal_postal_code,
        }

    def sync_children_inherited_fields(self, parent_business, previous_parent_state):
        if not parent_business.is_general:
            return

        child_businesses = parent_business.sub_businesses.all()
        if not child_businesses:
            return

        inherited_fields = [
            "fiscal_street",
            "fiscal_number",
            "fiscal_between_streets",
            "fiscal_apartment",
            "fiscal_district",
            "fiscal_municipality",
            "fiscal_province",
            "fiscal_postal_code",
        ]

        updated_any_child = False

        for child in child_businesses:
            for field_name in inherited_fields:
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
        if not business:
            return

        if business.income_entry_mode != Business.INCOME_MODE_DETAILED:
            return

        sales_scope = self.sale_service.generate_monthly_totals_sales(
            business_id=(
                business.id if business.is_general else business.parent_business_id
            ),
            specific_business_id=None if business.is_general else business.id,
        )

        if not sales_scope:
            DailyIncome.query.filter_by(
                business_id=business.id,
                source=DailyIncome.SOURCE_SALES_SUMMARY,
            ).delete()
            db.session.commit()
            return

        sales_by_day_and_location = {}
        sales_query = Sale.query.filter(
            Sale.business_id
            == (business.id if business.is_general else business.parent_business_id)
        )
        if not business.is_general:
            sales_query = sales_query.filter(Sale.specific_business_id == business.id)

        for sale in sales_query.all():
            location = (
                DailyIncome.LOCATION_BANK
                if sale.payment_method in {"transfer", "card", "bank"}
                else DailyIncome.LOCATION_CASH
            )
            bucket_key = (sale.date, location)
            sales_by_day_and_location[bucket_key] = sales_by_day_and_location.get(
                bucket_key, 0.0
            ) + float(sale.total_amount or 0)

        DailyIncome.query.filter_by(
            business_id=business.id,
            source=DailyIncome.SOURCE_SALES_SUMMARY,
        ).delete()

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
