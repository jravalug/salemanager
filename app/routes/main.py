from datetime import datetime

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from sqlalchemy import func

from app.models import Business, Client, DailyIncome

bp = Blueprint("main", __name__)


@bp.route("/node_modules/<path:filename>")
def node_modules(filename):
    return send_from_directory("../node_modules", filename)


@bp.route("/")
def index():
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
