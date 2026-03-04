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
from app.models import Business, Client, DailyIncome, Product, Sale
from app.forms import BusinessForm, DailyIncomeForm
from app.repositories.business_repository import BusinessRepository
from app.services import BusinessService, SalesService
from app.utils.file_utils import handle_logo_upload

bp = Blueprint("business", __name__, url_prefix="/business")

business_repo = BusinessRepository()
business_service = BusinessService()
sale_service = SalesService()


def _normalize_optional_text(value):
    if value is None:
        return None
    cleaned_value = value.strip()
    return cleaned_value or None


def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _sync_children_inherited_fields(parent_business, previous_parent_state):
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

            should_inherit = _is_blank(child_value) or child_value == old_parent_value
            if should_inherit and child_value != new_parent_value:
                setattr(child, field_name, new_parent_value)
                updated_any_child = True

        old_parent_logo = previous_parent_state.get("logo")
        new_parent_logo = parent_business.logo
        should_inherit_logo = _is_blank(child.logo) or child.logo == old_parent_logo
        if should_inherit_logo and child.logo != new_parent_logo:
            child.logo = new_parent_logo
            updated_any_child = True

    if updated_any_child:
        db.session.commit()


def _resolve_business_income_defaults(client, business):
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

    default_activity = business.default_income_activity or Business.INCOME_ACTIVITY_SALE
    return default_mode, default_activity


def _sync_sales_summary_daily_income(business):
    if not business:
        return

    if business.income_entry_mode != Business.INCOME_MODE_DETAILED:
        return

    sales_scope = sale_service.generate_monthly_totals_sales(
        business_id=business.id if business.is_general else business.parent_business_id,
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
                activity=business.default_income_activity or DailyIncome.ACTIVITY_SALE,
                amount=round(amount, 2),
                description="Resumen automático de ventas del día",
                cash_location=location,
                source=DailyIncome.SOURCE_SALES_SUMMARY,
            )
        )

    db.session.commit()


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

    if request.method == "GET":
        default_mode, default_activity = _resolve_business_income_defaults(
            business.client, business
        )
        if not business.income_entry_mode:
            form.income_entry_mode.data = default_mode
        if not business.default_income_activity:
            form.default_income_activity.data = default_activity

    if edit and form.validate_on_submit():
        previous_parent_state = None
        if business.is_general:
            previous_parent_state = {
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

        parent_business = business.parent_business if not business.is_general else None

        fiscal_street = _normalize_optional_text(form.fiscal_street.data)
        fiscal_number = _normalize_optional_text(form.fiscal_number.data)
        fiscal_between_streets = _normalize_optional_text(
            form.fiscal_between_streets.data
        )
        fiscal_apartment = _normalize_optional_text(form.fiscal_apartment.data)
        fiscal_district = _normalize_optional_text(form.fiscal_district.data)
        fiscal_municipality = _normalize_optional_text(form.fiscal_municipality.data)
        fiscal_province = _normalize_optional_text(form.fiscal_province.data)
        fiscal_postal_code = _normalize_optional_text(form.fiscal_postal_code.data)

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

        logo_path = handle_logo_upload(form.logo.data)
        if logo_path is not None:
            try:
                business_service.update_business(
                    business=business,
                    name=form.name.data,
                    description=form.description.data,
                    business_activity=_normalize_optional_text(
                        form.business_activity.data
                    ),
                    income_entry_mode=form.income_entry_mode.data,
                    default_income_activity=form.default_income_activity.data,
                    fiscal_street=fiscal_street,
                    fiscal_number=fiscal_number,
                    fiscal_between_streets=fiscal_between_streets,
                    fiscal_apartment=fiscal_apartment,
                    fiscal_district=fiscal_district,
                    fiscal_municipality=fiscal_municipality,
                    fiscal_province=fiscal_province,
                    fiscal_postal_code=fiscal_postal_code,
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
                business_activity=_normalize_optional_text(form.business_activity.data),
                income_entry_mode=form.income_entry_mode.data,
                default_income_activity=form.default_income_activity.data,
                fiscal_street=fiscal_street,
                fiscal_number=fiscal_number,
                fiscal_between_streets=fiscal_between_streets,
                fiscal_apartment=fiscal_apartment,
                fiscal_district=fiscal_district,
                fiscal_municipality=fiscal_municipality,
                fiscal_province=fiscal_province,
                fiscal_postal_code=fiscal_postal_code,
                is_general=form.is_general.data,
            )
            flash("Negocio actualizado correctamente", "success")

        if previous_parent_state is not None:
            _sync_children_inherited_fields(business, previous_parent_state)

        _sync_sales_summary_daily_income(business)

        return redirect(url_for("business.detail_or_edit", business_id=business.id))

    return render_template(
        "business/detail_or_edit.html", business=business, form=form, edit=edit
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

    default_mode, default_activity = _resolve_business_income_defaults(
        business.client, business
    )
    if request.method == "GET":
        form.business_activity.data = business.business_activity
        form.income_entry_mode.data = default_mode
        form.default_income_activity.data = default_activity

    if form.validate_on_submit():
        fiscal_street = (
            _normalize_optional_text(form.fiscal_street.data) or business.fiscal_street
        )
        fiscal_number = (
            _normalize_optional_text(form.fiscal_number.data) or business.fiscal_number
        )
        fiscal_between_streets = (
            _normalize_optional_text(form.fiscal_between_streets.data)
            or business.fiscal_between_streets
        )
        fiscal_apartment = (
            _normalize_optional_text(form.fiscal_apartment.data)
            or business.fiscal_apartment
        )
        fiscal_district = (
            _normalize_optional_text(form.fiscal_district.data)
            or business.fiscal_district
        )
        fiscal_municipality = (
            _normalize_optional_text(form.fiscal_municipality.data)
            or business.fiscal_municipality
        )
        fiscal_province = (
            _normalize_optional_text(form.fiscal_province.data)
            or business.fiscal_province
        )
        fiscal_postal_code = (
            _normalize_optional_text(form.fiscal_postal_code.data)
            or business.fiscal_postal_code
        )

        # Crear un nuevo negocio específico
        new_sub_business = Business(
            name=form.name.data,
            description=business.description,
            business_activity=_normalize_optional_text(form.business_activity.data)
            or business.business_activity,
            income_entry_mode=form.income_entry_mode.data or default_mode,
            default_income_activity=form.default_income_activity.data
            or default_activity,
            is_general=False,  # Es un negocio específico
            parent_business_id=business.id,  # Asociarlo al negocio general
            client_id=business.client_id,
            fiscal_street=fiscal_street,
            fiscal_number=fiscal_number,
            fiscal_between_streets=fiscal_between_streets,
            fiscal_apartment=fiscal_apartment,
            fiscal_district=fiscal_district,
            fiscal_municipality=fiscal_municipality,
            fiscal_province=fiscal_province,
            fiscal_postal_code=fiscal_postal_code,
        )

        db.session.add(new_sub_business)
        db.session.commit()

        _sync_sales_summary_daily_income(new_sub_business)

        flash("Negocio específico agregado correctamente.", "success")
        if business.client:
            return redirect(
                url_for(
                    "main.client_dashboard",
                    client_slug=business.client.slug,
                    business_id=business.id,
                )
            )
        return redirect(url_for("client.list_clients"))

    return render_template(
        "business/add_sub_business.html", business=business, form=form
    )


@bp.route("/<int:business_id>/daily-income", methods=["GET", "POST"])
def daily_income(business_id):
    return redirect(url_for("sale.sales", business_id=business_id))
