from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.forms import (
    DailyManualIncomeForm,
    IncomeDetailForm,
    IncomeForm,
    RemoveIncomeDetailForm,
    UpdateIncomeDetailForm,
)
from app.models import DailyIncome
from app.services import IncomeService

bp = Blueprint(
    "income",
    __name__,
    url_prefix="/clients/<string:client_slug>/business/<string:business_slug>/income",
)


@bp.route("/list", methods=["GET", "POST"])
def sales(client_slug, business_slug):
    """Muestra ingresos y maneja creación de ingresos manuales o detallados."""
    income_service = IncomeService()

    try:
        business, filters = income_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("client.list_clients"))

    month_param = request.args.get("month")
    try:
        list_context = income_service.build_income_list_context(
            business=business,
            filters=filters,
            month_param=month_param,
        )
    except ValueError:
        flash("Formato de mes inválido. Usa YYYY-MM.", "error")
        list_context = income_service.build_income_list_context(
            business=business,
            filters=filters,
            month_param=None,
        )

    is_daily_mode = list_context["is_daily_mode"]

    add_income_detail_form = IncomeForm(
        parent_business_id=filters["business_id"], prefix="add_sale"
    )
    add_daily_manual_income_form = DailyManualIncomeForm(prefix="add_income")
    if not add_daily_manual_income_form.date.data:
        add_daily_manual_income_form.date.data = datetime.today().date()
    if not add_daily_manual_income_form.activity.data:
        add_daily_manual_income_form.activity.data = (
            business.default_income_activity or DailyIncome.ACTIVITY_SALE
        )
    if not add_daily_manual_income_form.payment_method.data:
        add_daily_manual_income_form.payment_method.data = "cash"

    if is_daily_mode:
        if add_daily_manual_income_form.validate_on_submit():
            try:
                income_service.create_daily_income(
                    business=business,
                    form=add_daily_manual_income_form,
                )
                flash("Ingreso diario creado correctamente", "success")
                return redirect(
                    url_for(
                        "income.sales",
                        client_slug=business.client.slug,
                        business_slug=business.slug,
                    )
                )
            except Exception as e:
                flash(f"Error inesperado: {str(e)}", "error")
    else:
        if add_income_detail_form.validate_on_submit():
            try:
                new_income = income_service.add_income(
                    business=business,
                    form=add_income_detail_form,
                )
                flash("Ingreso detallado creado correctamente", "success")
                return redirect(
                    url_for(
                        "income.details",
                        client_slug=business.client.slug,
                        business_slug=business.slug,
                        sale_id=new_income.id,
                    )
                )
            except Exception as e:
                flash(f"Error inesperado: {str(e)}", "error")
                return redirect(
                    url_for(
                        "income.sales",
                        client_slug=business.client.slug,
                        business_slug=business.slug,
                    )
                )

    template_context = {
        "business": business,
        "add_sale_form": add_income_detail_form,
        "add_income_form": add_daily_manual_income_form,
        "pending_income_events": income_service.get_pending_income_events(business.id),
        "inline_message": None,
        "inline_message_type": None,
        **list_context,
    }

    if request.method == "GET" and request.headers.get("HX-Request") == "true":
        return render_template(
            "income/partials/_income_list_content.html",
            **template_context,
        )

    return render_template("income/list.html", **template_context)


@bp.route("/<int:sale_id>", methods=["GET", "POST"])
def details(client_slug, business_slug, sale_id):
    """Muestra detalles de ingreso detallado."""
    income_service = IncomeService()

    try:
        business, filters, income = income_service.resolve_income_scope(
            client_slug=client_slug,
            business_slug=business_slug,
            income_id=sale_id,
        )
    except Exception as e:
        flash(str(e), "error")
        return redirect(
            url_for(
                "income.sales",
                client_slug=client_slug,
                business_slug=business_slug,
            )
        )

    def build_details_context():
        return income_service.build_income_details_context(
            income=income,
            filters=filters,
        )

    def build_template_context(details_context):
        return {
            "business": business,
            "sale": income,
            "products": details_context["sale_details"],
            "add_product_form": details_context["add_product_form"],
            "remove_product_form": details_context["remove_product_form"],
            "update_product_form": details_context["update_product_form"],
            "update_sale_form": details_context["update_sale_form"],
            "add_sale_form": details_context["add_sale_form"],
            "sale_summaries": details_context.get("sale_summaries", {}),
            "inline_message": details_context.get("inline_message"),
            "inline_message_type": details_context.get("inline_message_type"),
        }

    def render_sale_detail_panel(details_context):
        return render_template(
            "income/partials/_sale_detail_panel.html",
            **build_template_context(details_context),
        )

    def build_htmx_details_context(message, message_type="success"):
        details_context = build_details_context()
        details_context["inline_message"] = message
        details_context["inline_message_type"] = message_type
        return details_context

    details_context = build_details_context()
    add_product_form = details_context["add_product_form"]
    update_product_form = details_context["update_product_form"]
    remove_product_form = details_context["remove_product_form"]
    update_sale_form = details_context["update_sale_form"]
    add_sale_form = details_context["add_sale_form"]

    def redirect_to_income_detail():
        return redirect(
            url_for(
                "income.details",
                client_slug=business.client.slug,
                business_slug=business.slug,
                sale_id=income.id,
            )
        )

    try:
        if remove_product_form.validate_on_submit():
            removed_product = income_service.handle_remove_product_form(
                income=income,
                sale_detail_id=remove_product_form.sale_detail_id.data,
            )
            flash(f"Producto '{removed_product.name}' eliminado", "success")
            if request.headers.get("HX-Request") == "true":
                return render_sale_detail_panel(
                    build_htmx_details_context(
                        f"Producto '{removed_product.name}' eliminado"
                    )
                )
            return redirect_to_income_detail()

        if add_product_form.validate_on_submit():
            new_income_detail = income_service.handle_add_product_form(
                income=income,
                product_id=add_product_form.product_id.data,
                quantity=add_product_form.quantity.data,
                discount=add_product_form.discount.data,
            )
            flash(f"Producto '{new_income_detail.product.name}' agregado", "success")
            if request.headers.get("HX-Request") == "true":
                return render_sale_detail_panel(
                    build_htmx_details_context(
                        f"Producto '{new_income_detail.product.name}' agregado"
                    )
                )
            return redirect_to_income_detail()

        if update_product_form.validate_on_submit():
            income_service.handle_update_product_form(
                income=income,
                sale_detail_id=update_product_form.sale_detail_id.data,
                quantity=update_product_form.quantity.data,
                discount=update_product_form.discount.data,
            )
            flash("Producto actualizado correctamente", "success")
            if request.headers.get("HX-Request") == "true":
                return render_sale_detail_panel(
                    build_htmx_details_context("Producto actualizado correctamente")
                )
            return redirect_to_income_detail()

        if update_sale_form.validate_on_submit():
            income_service.update_income(income=income, form=update_sale_form)
            flash("Ingreso actualizado correctamente", "success")
            if request.headers.get("HX-Request") == "true":
                return render_sale_detail_panel(
                    build_htmx_details_context("Ingreso actualizado correctamente")
                )
            return redirect_to_income_detail()

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect_to_income_detail()

    if add_sale_form.validate_on_submit():
        try:
            new_income = income_service.add_income(
                business=business,
                form=add_sale_form,
            )
            flash("Ingreso detallado creado correctamente", "success")
            return redirect(
                url_for(
                    "income.details",
                    client_slug=business.client.slug,
                    business_slug=business.slug,
                    sale_id=new_income.id,
                )
            )
        except Exception as e:
            flash(f"Error inesperado: {str(e)}", "error")
            return redirect(
                url_for(
                    "income.sales",
                    client_slug=business.client.slug,
                    business_slug=business.slug,
                )
            )

    return render_template(
        "income/details.html", **build_template_context(details_context)
    )


@bp.route("/events/<int:income_event_id>/reconcile", methods=["POST"])
def reconcile_income_event(client_slug, business_slug, income_event_id):
    """Concilia manualmente un ingreso pendiente por acreditar."""
    income_service = IncomeService()
    is_htmx_request = request.headers.get("HX-Request") == "true"
    month_param = (request.form.get("month") or request.args.get("month") or "").strip()

    try:
        business, filters = income_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("client.list_clients"))

    message = ""
    message_type = "success"
    try:
        income_service.reconcile_income_event(
            business_id=business.id,
            income_event_id=income_event_id,
            bank_operation_number=request.form.get("bank_operation_number", ""),
            collected_date_value=request.form.get("collected_date"),
            reconciled_by=request.form.get("reconciled_by"),
            bank_name=request.form.get("bank_name"),
        )
        message = "Ingreso pendiente conciliado correctamente."
    except ValueError as exc:
        message = str(exc)
        message_type = "error"
    except Exception as exc:
        message = f"Error al conciliar ingreso: {exc}"
        message_type = "error"

    if is_htmx_request:
        try:
            list_context = income_service.build_income_list_context(
                business=business,
                filters=filters,
                month_param=month_param or None,
            )
        except ValueError:
            list_context = income_service.build_income_list_context(
                business=business,
                filters=filters,
                month_param=None,
            )
            message = "Formato de mes inválido. Usa YYYY-MM."
            message_type = "error"

        return render_template(
            "income/partials/_income_list_content.html",
            business=business,
            pending_income_events=income_service.get_pending_income_events(business.id),
            inline_message=message,
            inline_message_type=message_type,
            **list_context,
        )

    flash(message, message_type)

    return redirect(
        url_for(
            "income.sales",
            client_slug=client_slug,
            business_slug=business_slug,
            month=month_param or None,
        )
    )
