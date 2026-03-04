from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.forms import ClientForm
from app.models import Business, Client, Product, Sale
from app.models.daily_income import DailyIncome
from app.services import ClientAccountingService

bp = Blueprint("client", __name__, url_prefix="/clients")


def _split_list_values(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _build_default_business_name(client_name: str) -> str:
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


def _get_client_by_slug(client_slug: str) -> Client | None:
    clients = Client.query.order_by(Client.id.asc()).all()
    return next((item for item in clients if item.slug == client_slug), None)


@bp.route("/list", methods=["GET", "POST"])
def list_clients():
    form = ClientForm()

    if form.validate_on_submit():
        client = Client(
            name=form.name.data.strip(),
            identity_number=(form.identity_number.data or "").strip() or None,
            nit=(form.nit.data or "").strip() or None,
            legal_street=(form.legal_street.data or "").strip() or None,
            legal_number=(form.legal_number.data or "").strip() or None,
            legal_between_streets=(form.legal_between_streets.data or "").strip()
            or None,
            legal_apartment=(form.legal_apartment.data or "").strip() or None,
            legal_district=(form.legal_district.data or "").strip() or None,
            legal_municipality=(form.legal_municipality.data or "").strip() or None,
            legal_province=(form.legal_province.data or "").strip() or None,
            legal_postal_code=(form.legal_postal_code.data or "").strip() or None,
            phone_numbers=_split_list_values(form.phone_numbers_input.data),
            primary_phone_number=(form.primary_phone_number.data or "").strip() or None,
            email_addresses=_split_list_values(form.email_addresses_input.data),
            primary_email_address=(form.primary_email_address.data or "").strip()
            or None,
            fiscal_account_number=(form.fiscal_account_number.data or "").strip()
            or None,
            fiscal_account_card_number=(
                form.fiscal_account_card_number.data or ""
            ).strip()
            or None,
            client_type=form.client_type.data,
            accounting_regime=form.accounting_regime.data,
            is_active=bool(form.is_active.data),
        )

        try:
            db.session.add(client)
            db.session.flush()

            business = Business(
                name=_build_default_business_name(client.name),
                description=f"Negocio principal de {client.name}",
                is_general=True,
                client_id=client.id,
            )
            db.session.add(business)

            db.session.commit()
            flash("Cliente creado correctamente.", "success")
        except SQLAlchemyError as exc:
            db.session.rollback()
            flash(f"Error al crear cliente: {exc}", "error")

        return redirect(url_for("client.list_clients"))

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
        all_business_ids = parent_business_ids + [item.id for item in sub_businesses]

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
                "primary_business": parent_businesses[0] if parent_businesses else None,
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

    return render_template(
        "client/list.html",
        client_cards=client_cards,
        summary=summary,
        form=form,
    )


@bp.route("/<string:client_slug>", methods=["GET", "POST"])
def detail_or_edit(client_slug):
    client = _get_client_by_slug(client_slug)
    if not client:
        abort(404)
    form = ClientForm(obj=client)

    if request.method == "GET":
        form.phone_numbers_input.data = ", ".join(client.phone_numbers or [])
        form.email_addresses_input.data = ", ".join(client.email_addresses or [])

    if form.validate_on_submit():
        try:
            client.name = form.name.data.strip()
            client.identity_number = (form.identity_number.data or "").strip() or None
            client.nit = (form.nit.data or "").strip() or None
            client.legal_street = (form.legal_street.data or "").strip() or None
            client.legal_number = (form.legal_number.data or "").strip() or None
            client.legal_between_streets = (
                form.legal_between_streets.data or ""
            ).strip() or None
            client.legal_apartment = (form.legal_apartment.data or "").strip() or None
            client.legal_district = (form.legal_district.data or "").strip() or None
            client.legal_municipality = (
                form.legal_municipality.data or ""
            ).strip() or None
            client.legal_province = (form.legal_province.data or "").strip() or None
            client.legal_postal_code = (
                form.legal_postal_code.data or ""
            ).strip() or None
            client.phone_numbers = _split_list_values(form.phone_numbers_input.data)
            client.primary_phone_number = (
                form.primary_phone_number.data or ""
            ).strip() or None
            client.email_addresses = _split_list_values(form.email_addresses_input.data)
            client.primary_email_address = (
                form.primary_email_address.data or ""
            ).strip() or None
            client.fiscal_account_number = (
                form.fiscal_account_number.data or ""
            ).strip() or None
            client.fiscal_account_card_number = (
                form.fiscal_account_card_number.data or ""
            ).strip() or None
            client.client_type = form.client_type.data
            client.accounting_regime = form.accounting_regime.data
            client.is_active = bool(form.is_active.data)

            db.session.commit()
            flash("Cliente actualizado correctamente.", "success")
            return redirect(url_for("client.detail_or_edit", client_slug=client.slug))
        except SQLAlchemyError as exc:
            db.session.rollback()
            flash(f"Error al actualizar cliente: {exc}", "error")

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

    return render_template(
        "client/detail_or_edit.html",
        client=client,
        client_businesses=client_businesses,
        business_groups=business_groups,
        total_sub_businesses=total_sub_businesses,
        form=form,
    )


@bp.route("/evaluate-regime", methods=["POST"])
def evaluate_regime():
    try:
        summary = ClientAccountingService().evaluate_annual_regime_transition(
            force=True
        )
        flash(
            "Evaluación completada. "
            f"Evaluados: {summary['evaluated_clients']} | "
            f"Actualizados: {summary['updated_clients']}",
            "success",
        )
    except Exception as exc:
        flash(f"Error al evaluar régimen: {exc}", "error")

    return redirect(url_for("client.list_clients"))


@bp.route("/<client_slug>/dashboard")
def client_dashboard(client_slug):
    clients = Client.query.order_by(Client.id.asc()).all()
    client = next((item for item in clients if item.slug == client_slug), None)
    if not client:
        abort(404)

    all_businesses = Business.query.filter_by(client_id=client.id).all()
    if not all_businesses:
        return redirect(url_for("client.list_clients"))

    from app.routes.business import _sync_sales_summary_daily_income

    primary_businesses = [item for item in all_businesses if item.is_general]
    if not primary_businesses:
        primary_businesses = all_businesses

    for item in primary_businesses:
        _sync_sales_summary_daily_income(item)

    selected_business_id = request.args.get("business_id", type=int)
    selected_business = None
    if selected_business_id:
        selected_business = next(
            (item for item in all_businesses if item.id == selected_business_id), None
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

    return render_template(
        "business/dashboard.html",
        business=business,
        client=client,
        primary_business=primary_business,
        monthly_totals=dict(monthly_totals_display),
        monthly_totals_last_12=dict(monthly_totals_last_12),
        chart_months=chart_months,
        chart_totals=chart_totals,
        best_month_label=best_month_label,
        best_month_total=best_month_total,
        lowest_month_label=lowest_month_label,
        lowest_month_total=lowest_month_total,
        total_general=total_general,
        month_count=month_count,
        average_monthly=average_monthly,
        latest_month=latest_month,
        latest_total=latest_total,
        trend_delta=trend_delta,
        trend_percent=trend_percent,
        trend_direction=trend_direction,
        latest_vs_avg_delta=latest_vs_avg_delta,
        latest_vs_avg_percent=latest_vs_avg_percent,
        latest_vs_avg_direction=latest_vs_avg_direction,
    )
