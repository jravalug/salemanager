from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Business, Client, Product, Sale
from app.models.daily_income import DailyIncome
from app.services.business_rules_service import BusinessRulesService


class ClientService:
    def __init__(self):
        self.business_rules_service = BusinessRulesService()

    @staticmethod
    def split_list_values(raw_value: str | None) -> list[str]:
        if not raw_value:
            return []
        return [item.strip() for item in raw_value.split(",") if item.strip()]

    @staticmethod
    def normalize_optional_text(value):
        if value is None:
            return None
        cleaned_value = value.strip()
        return cleaned_value or None

    def get_client_by_slug(self, client_slug: str) -> Client | None:
        clients = Client.query.order_by(Client.id.asc()).all()
        return next((item for item in clients if item.slug == client_slug), None)

    def build_default_business_name(self, client_name: str) -> str:
        base_name = client_name.strip()
        exact_match = Business.query.filter(
            func.lower(Business.name) == base_name.lower()
        ).first()
        if not exact_match:
            return base_name

        index = 1
        while True:
            candidate = f"{base_name} ({index})"
            found = Business.query.filter(
                func.lower(Business.name) == candidate.lower()
            ).first()
            if not found:
                return candidate
            index += 1

    def create_client_with_default_business(self, form) -> Client:
        try:
            client = Client(
                name=form.name.data.strip(),
                identity_number=self.normalize_optional_text(form.identity_number.data),
                nit=self.normalize_optional_text(form.nit.data),
                legal_street=self.normalize_optional_text(form.legal_street.data),
                legal_number=self.normalize_optional_text(form.legal_number.data),
                legal_between_streets=self.normalize_optional_text(
                    form.legal_between_streets.data
                ),
                legal_apartment=self.normalize_optional_text(form.legal_apartment.data),
                legal_district=self.normalize_optional_text(form.legal_district.data),
                legal_municipality=self.normalize_optional_text(
                    form.legal_municipality.data
                ),
                legal_province=self.normalize_optional_text(form.legal_province.data),
                legal_postal_code=self.normalize_optional_text(
                    form.legal_postal_code.data
                ),
                phone_numbers=self.split_list_values(form.phone_numbers_input.data),
                primary_phone_number=self.normalize_optional_text(
                    form.primary_phone_number.data
                ),
                email_addresses=self.split_list_values(form.email_addresses_input.data),
                primary_email_address=self.normalize_optional_text(
                    form.primary_email_address.data
                ),
                fiscal_account_number=self.normalize_optional_text(
                    form.fiscal_account_number.data
                ),
                fiscal_account_card_number=self.normalize_optional_text(
                    form.fiscal_account_card_number.data
                ),
                client_type=form.client_type.data,
                accounting_regime=form.accounting_regime.data,
                is_active=bool(form.is_active.data),
            )

            db.session.add(client)
            db.session.flush()

            business = Business(
                name=self.build_default_business_name(client.name),
                description=f"Negocio principal de {client.name}",
                is_general=True,
                client_id=client.id,
            )
            db.session.add(business)
            db.session.commit()
            return client
        except SQLAlchemyError:
            db.session.rollback()
            raise

    def update_client_from_form(self, client: Client, form) -> Client:
        try:
            client.name = form.name.data.strip()
            client.identity_number = self.normalize_optional_text(
                form.identity_number.data
            )
            client.nit = self.normalize_optional_text(form.nit.data)
            client.legal_street = self.normalize_optional_text(form.legal_street.data)
            client.legal_number = self.normalize_optional_text(form.legal_number.data)
            client.legal_between_streets = self.normalize_optional_text(
                form.legal_between_streets.data
            )
            client.legal_apartment = self.normalize_optional_text(
                form.legal_apartment.data
            )
            client.legal_district = self.normalize_optional_text(
                form.legal_district.data
            )
            client.legal_municipality = self.normalize_optional_text(
                form.legal_municipality.data
            )
            client.legal_province = self.normalize_optional_text(
                form.legal_province.data
            )
            client.legal_postal_code = self.normalize_optional_text(
                form.legal_postal_code.data
            )
            client.phone_numbers = self.split_list_values(form.phone_numbers_input.data)
            client.primary_phone_number = self.normalize_optional_text(
                form.primary_phone_number.data
            )
            client.email_addresses = self.split_list_values(
                form.email_addresses_input.data
            )
            client.primary_email_address = self.normalize_optional_text(
                form.primary_email_address.data
            )
            client.fiscal_account_number = self.normalize_optional_text(
                form.fiscal_account_number.data
            )
            client.fiscal_account_card_number = self.normalize_optional_text(
                form.fiscal_account_card_number.data
            )
            client.client_type = form.client_type.data
            client.accounting_regime = form.accounting_regime.data
            client.is_active = bool(form.is_active.data)

            db.session.commit()
            return client
        except SQLAlchemyError:
            db.session.rollback()
            raise

    def get_clients_overview(self):
        clients = Client.query.order_by(Client.name.asc()).all()

        client_cards = []
        total_businesses = 0
        total_sub_businesses = 0
        total_products = 0
        total_sales = 0
        total_revenue = 0.0
        clients_with_activity = 0
        financial_clients = 0
        fiscal_clients = 0
        current_month = date.today().strftime("%Y-%m")

        for client in clients:
            parent_businesses = (
                Business.query.filter_by(client_id=client.id, is_general=True)
                .order_by(Business.name.asc())
                .all()
            )
            parent_business_ids = [business.id for business in parent_businesses]
            business_count = len(parent_businesses)

            sub_businesses = []
            businesses_with_children = []
            for business in parent_businesses:
                children = business.sub_businesses.order_by(Business.name.asc()).all()
                sub_businesses.extend(children)
                businesses_with_children.append(
                    {
                        "business": business,
                        "children": children,
                        "children_count": len(children),
                    }
                )

            sub_business_count = len(sub_businesses)
            all_business_ids = parent_business_ids + [
                item.id for item in sub_businesses
            ]

            product_count = 0
            sales_count = 0
            month_sales_count = 0
            revenue_total = 0.0
            last_sale_date = None

            if all_business_ids:
                product_count = Product.query.filter(
                    Product.business_id.in_(all_business_ids)
                ).count()

            sales_conditions = []
            if parent_business_ids:
                sales_conditions.append(Sale.business_id.in_(parent_business_ids))
            if all_business_ids:
                sales_conditions.append(Sale.specific_business_id.in_(all_business_ids))

            if sales_conditions:
                sale_query = Sale.query.filter(or_(*sales_conditions))
                sales_count = sale_query.count()
                month_sales_count = sale_query.filter(
                    func.strftime("%Y-%m", Sale.date) == current_month
                ).count()

                revenue_value = sale_query.with_entities(
                    func.coalesce(func.sum(Sale.total_amount), 0.0)
                ).scalar()
                revenue_total = float(revenue_value or 0.0)
                last_sale_date = sale_query.with_entities(func.max(Sale.date)).scalar()

            total_businesses += business_count
            total_sub_businesses += sub_business_count
            total_products += product_count
            total_sales += sales_count
            total_revenue += revenue_total

            if sales_count > 0:
                clients_with_activity += 1

            if client.accounting_regime == Client.REGIME_FINANCIAL:
                financial_clients += 1
            else:
                fiscal_clients += 1

            client_cards.append(
                {
                    "client": client,
                    "businesses": parent_businesses,
                    "businesses_with_children": businesses_with_children,
                    "business_count": business_count,
                    "sub_business_count": sub_business_count,
                    "product_count": product_count,
                    "sales_count": sales_count,
                    "month_sales_count": month_sales_count,
                    "revenue_total": revenue_total,
                    "last_sale_date": last_sale_date,
                    "primary_business": (
                        parent_businesses[0] if parent_businesses else None
                    ),
                }
            )

        summary = {
            "total_clients": len(clients),
            "clients_with_activity": clients_with_activity,
            "total_businesses": total_businesses,
            "total_sub_businesses": total_sub_businesses,
            "total_products": total_products,
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "fiscal_clients": fiscal_clients,
            "financial_clients": financial_clients,
        }
        return client_cards, summary

    def get_business_groups_for_client(self, client: Client):
        client_businesses = (
            Business.query.filter_by(client_id=client.id, is_general=True)
            .order_by(Business.name.asc())
            .all()
        )
        business_groups = []
        total_sub_businesses = 0
        for business in client_businesses:
            children = business.sub_businesses.order_by(Business.name.asc()).all()
            total_sub_businesses += len(children)
            business_groups.append(
                {
                    "business": business,
                    "children": children,
                    "children_count": len(children),
                }
            )

        return client_businesses, business_groups, total_sub_businesses

    def build_client_dashboard_context(
        self,
        client: Client,
        selected_business_slug: str | None = None,
    ):
        all_businesses = Business.query.filter_by(client_id=client.id).all()
        if not all_businesses:
            return None

        primary_businesses = [item for item in all_businesses if item.is_general]
        if not primary_businesses:
            primary_businesses = all_businesses

        for item in primary_businesses:
            self.business_rules_service.sync_sales_summary_daily_income(item)

        selected_business = None
        if selected_business_slug:
            selected_business = next(
                (
                    item
                    for item in all_businesses
                    if item.slug == selected_business_slug
                ),
                None,
            )

        primary_business = primary_businesses[0] if primary_businesses else None
        business = selected_business

        business_ids = [item.id for item in primary_businesses]
        monthly_totals_raw = (
            DailyIncome.query.filter(
                DailyIncome.business_id.in_(business_ids),
                DailyIncome.income_type == DailyIncome.TYPE_INCOME_OBTAINED,
            )
            .with_entities(
                func.strftime("%Y-%m", DailyIncome.date).label("month"),
                func.sum(DailyIncome.amount).label("total"),
            )
            .group_by("month")
            .order_by(func.strftime("%Y-%m", DailyIncome.date).desc())
            .all()
        )

        monthly_totals_desc = [
            (month, float(total or 0)) for month, total in monthly_totals_raw
        ]

        month_abbr = {
            1: "ENE",
            2: "FEB",
            3: "MAR",
            4: "ABR",
            5: "MAY",
            6: "JUN",
            7: "JUL",
            8: "AGO",
            9: "SEP",
            10: "OCT",
            11: "NOV",
            12: "DIC",
        }

        def _format_month(month_value):
            try:
                parsed = datetime.strptime(month_value, "%Y-%m")
                return f"{month_abbr.get(parsed.month, 'N/D')}/{parsed.year}"
            except Exception:
                return month_value

        monthly_totals_ordered = list(reversed(monthly_totals_desc))
        monthly_totals_display = [
            (_format_month(month), total) for month, total in monthly_totals_ordered
        ]
        monthly_totals_last_12 = monthly_totals_display[-12:]
        chart_months = [month for month, _ in monthly_totals_last_12]
        chart_totals = [total for _, total in monthly_totals_last_12]

        if monthly_totals_last_12:
            best_month_label, best_month_total = max(
                monthly_totals_last_12, key=lambda item: item[1]
            )
            lowest_month_label, lowest_month_total = min(
                monthly_totals_last_12, key=lambda item: item[1]
            )
        else:
            best_month_label, best_month_total = "N/D", 0
            lowest_month_label, lowest_month_total = "N/D", 0

        month_count = len(monthly_totals_desc)
        total_general = sum(total for _, total in monthly_totals_desc)
        average_monthly = (total_general / month_count) if month_count > 0 else 0

        latest_month = (
            _format_month(monthly_totals_desc[0][0]) if month_count > 0 else "N/D"
        )
        latest_total = monthly_totals_desc[0][1] if month_count > 0 else 0

        previous_total = monthly_totals_desc[1][1] if month_count > 1 else None
        if previous_total in (None, 0):
            trend_delta = 0
            trend_percent = None
            trend_direction = "neutral"
        else:
            trend_delta = latest_total - previous_total
            trend_percent = (trend_delta / previous_total) * 100
            trend_direction = (
                "up" if trend_delta > 0 else "down" if trend_delta < 0 else "neutral"
            )

        latest_vs_avg_delta = latest_total - average_monthly if month_count > 0 else 0
        if average_monthly > 0:
            latest_vs_avg_percent = (latest_vs_avg_delta / average_monthly) * 100
            latest_vs_avg_direction = (
                "up"
                if latest_vs_avg_delta > 0
                else "down" if latest_vs_avg_delta < 0 else "neutral"
            )
        else:
            latest_vs_avg_percent = None
            latest_vs_avg_direction = "neutral"

        return {
            "business": business,
            "primary_business": primary_business,
            "monthly_totals": dict(monthly_totals_display),
            "monthly_totals_last_12": dict(monthly_totals_last_12),
            "chart_months": chart_months,
            "chart_totals": chart_totals,
            "best_month_label": best_month_label,
            "best_month_total": best_month_total,
            "lowest_month_label": lowest_month_label,
            "lowest_month_total": lowest_month_total,
            "total_general": total_general,
            "month_count": month_count,
            "average_monthly": average_monthly,
            "latest_month": latest_month,
            "latest_total": latest_total,
            "trend_delta": trend_delta,
            "trend_percent": trend_percent,
            "trend_direction": trend_direction,
            "latest_vs_avg_delta": latest_vs_avg_delta,
            "latest_vs_avg_percent": latest_vs_avg_percent,
            "latest_vs_avg_direction": latest_vs_avg_direction,
        }
