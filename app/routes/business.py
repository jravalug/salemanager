from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Business, Product, Sale
from app.forms import BusinessForm
from app.repositories.business_repository import BusinessRepository
from app.services import BusinessService, SalesService
from app.utils.file_utils import handle_logo_upload

bp = Blueprint("business", __name__, url_prefix="/business")

business_repo = BusinessRepository()
business_service = BusinessService()
sale_service = SalesService()


@bp.route("/list", methods=["GET", "POST"])
def business_list():
    flash("El acceso principal ahora es por clientes.", "info")
    return redirect(url_for("client.list_clients"))


@bp.route("/<int:business_id>", methods=["GET", "POST"])
def detail_or_edit(business_id):
    """
    Muestra los detalles de un negocio y maneja su edición.
    """
    business = Business.query.get_or_404(business_id)
    edit = request.args.get("edit", False)
    form = BusinessForm(obj=business)

    if edit and form.validate_on_submit():
        logo_path = handle_logo_upload(form.logo.data)
        if logo_path is not None:
            try:
                business_service.update_business(
                    business=business,
                    name=form.name.data,
                    description=form.description.data,
                    is_general=form.is_general.data,
                    logo=logo_path,
                )
                flash("Negocio actualizado correctamente", "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Error al actualizar el negocio: {str(e)}", "error")
            except Exception as e:
                flash(f"Error inesperado: {str(e)}", "error")
        else:
            business_service.update_business(
                business=business,
                name=form.name.data,
                description=form.description.data,
                is_general=form.is_general.data,
            )
            flash("Negocio actualizado correctamente", "success")

        return redirect(url_for("business.detail_or_edit", business_id=business.id))

    return render_template(
        "business/detail_or_edit.html", business=business, form=form, edit=edit
    )


@bp.route("/<int:business_id>/dashboard")
def dashboard(business_id):
    """
    Muestra el dashboard de ingresos del contexto seleccionado (negocio principal o subnegocio).
    """
    business = Business.query.get_or_404(business_id)
    client = business.client

    primary_business = None
    if client:
        primary_business = client.businesses.filter_by(is_general=True).first()

    if primary_business is None:
        primary_business = business if business.is_general else business.parent_business

    business_filters = business_service.get_parent_filters(business)

    monthly_totals_raw = sale_service.generate_monthly_totals_sales(
        business_id=business_filters["business_id"],
        specific_business_id=business_filters.get("specific_business_id"),
    )

    # monthly_totals_raw comes sorted DESC by month (latest first)
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

    # Comparación último mes vs promedio
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


@bp.route("/<int:business_id>/add-sub-business", methods=["GET", "POST"])
def add_sub_business(business_id):
    # Obtener el negocio general
    business = Business.query.get_or_404(business_id)

    if not business.is_general:
        flash("Este negocio no es un negocio general.", "danger")
        return redirect(url_for("main.index"))

    # Inicializar el formulario
    form = BusinessForm()

    if form.validate_on_submit():
        # Crear un nuevo negocio específico
        new_sub_business = Business(
            name=form.name.data,
            description=business.description,
            is_general=False,  # Es un negocio específico
            parent_business_id=business.id,  # Asociarlo al negocio general
        )

        db.session.add(new_sub_business)
        db.session.commit()

        flash("Negocio específico agregado correctamente.", "success")
        return redirect(url_for("business.dashboard", business_id=business.id))

    return render_template(
        "business/add_sub_business.html", business=business, form=form
    )
