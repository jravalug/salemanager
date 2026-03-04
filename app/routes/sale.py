from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from datetime import datetime
from app.forms import (
    SaleForm,
    DailyIncomeForm,
)

from app.services import SalesService
from app.models import DailyIncome

bp = Blueprint(
    "sale",
    __name__,
    url_prefix="/clients/<string:client_slug>/business/<string:business_slug>/sale",
)

@bp.route("/list", methods=["GET", "POST"])
def sales(client_slug, business_slug):
    """
    Muestra la lista de ventas y maneja la creación de nuevas ventas.
    """
    sale_service = SalesService()

    try:
        business, filters = sale_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("client.list_clients"))

    month_param = request.args.get("month")
    try:
        list_context = sale_service.build_sales_list_context(
            business=business,
            filters=filters,
            month_param=month_param,
        )
    except ValueError:
        flash("Formato de mes inválido. Usa YYYY-MM.", "error")
        list_context = sale_service.build_sales_list_context(
            business=business,
            filters=filters,
            month_param=None,
        )

    is_daily_mode = list_context["is_daily_mode"]

    add_sale_form = SaleForm(
        parent_business_id=filters["business_id"], prefix="add_sale"
    )
    add_income_form = DailyIncomeForm(prefix="add_income")
    if not add_income_form.date.data:
        add_income_form.date.data = datetime.today().date()
    if not add_income_form.activity.data:
        add_income_form.activity.data = (
            business.default_income_activity or DailyIncome.ACTIVITY_SALE
        )

    # Manejar la validación y creación de nuevas ventas
    if is_daily_mode:
        if add_income_form.validate_on_submit():
            try:
                sale_service.create_daily_income(business=business, form=add_income_form)
                flash("Ingreso diario creado correctamente", "success")
                return redirect(
                    url_for(
                        "sale.sales",
                        client_slug=business.client.slug,
                        business_slug=business.slug,
                    )
                )
            except Exception as e:
                flash(f"Error inesperado: {str(e)}", "error")
    else:
        if add_sale_form.validate_on_submit():
            try:
                new_sale = sale_service.add_sale(
                    business=business,
                    form=add_sale_form,
                )
                flash("Ingreso detallado creado correctamente", "success")
                return redirect(
                    url_for(
                        "sale.details",
                        client_slug=business.client.slug,
                        business_slug=business.slug,
                        sale_id=new_sale.id,
                    )
                )
            except Exception as e:
                flash(f"Error inesperado: {str(e)}", "error")
                return redirect(
                    url_for(
                        "sale.sales",
                        client_slug=business.client.slug,
                        business_slug=business.slug,
                    )
                )

    return render_template(
        "sale/list.html",
        business=business,
        add_sale_form=add_sale_form,
        add_income_form=add_income_form,
        **list_context,
    )


@bp.route("/<int:sale_id>", methods=["GET", "POST"])
def details(client_slug, business_slug, sale_id):
    """
    Muestra los detalles de una venta específica y maneja las operaciones relacionadas.
    """
    sale_service = SalesService()

    try:
        business, filters, sale = sale_service.resolve_sale_scope(
            client_slug=client_slug,
            business_slug=business_slug,
            sale_id=sale_id,
        )
    except Exception as e:
        flash(str(e), "error")
        return redirect(
            url_for(
                "sale.sales",
                client_slug=client_slug,
                business_slug=business_slug,
            )
        )

    details_context = sale_service.build_sale_details_context(
        sale=sale,
        filters=filters,
    )
    add_product_form = details_context["add_product_form"]
    update_product_form = details_context["update_product_form"]
    remove_product_form = details_context["remove_product_form"]
    update_sale_form = details_context["update_sale_form"]
    add_sale_form = details_context["add_sale_form"]

    # Función auxiliar para redirigir a los detalles de la venta
    def redirect_to_sale():
        return redirect(
            url_for(
                "sale.details",
                client_slug=business.client.slug,
                business_slug=business.slug,
                sale_id=sale.id,
            )
        )

    # Procesar formularios
    try:
        if remove_product_form.validate_on_submit():
            removed_product = sale_service.handle_remove_product_form(
                sale=sale,
                sale_detail_id=remove_product_form.sale_detail_id.data,
            )
            flash(f"Producto '{removed_product.name}' eliminado", "success")
            return redirect_to_sale()

        if add_product_form.validate_on_submit():
            new_sale_detail = sale_service.handle_add_product_form(
                sale=sale,
                product_id=add_product_form.product_id.data,
                quantity=add_product_form.quantity.data,
                discount=add_product_form.discount.data,
            )
            flash(f"Producto '{new_sale_detail.product.name}' agregado", "success")
            return redirect_to_sale()

        if update_product_form.validate_on_submit():
            sale_service.handle_update_product_form(
                sale=sale,
                sale_detail_id=update_product_form.sale_detail_id.data,
                quantity=update_product_form.quantity.data,
                discount=update_product_form.discount.data,
            )
            flash("Producto actualizado correctamente", "success")
            return redirect_to_sale()

        if update_sale_form.validate_on_submit():
            sale_service.update_sale(sale=sale, form=update_sale_form)
            flash("Venta actualizada correctamente", "success")
            return redirect_to_sale()

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect_to_sale()

    # Manejar la validación y creación de nuevas ventas
    if add_sale_form.validate_on_submit():
        try:
            new_sale = sale_service.add_sale(
                business=business,
                form=add_sale_form,
            )
            flash("Ingreso detallado creado correctamente", "success")
            return redirect(
                url_for(
                    "sale.details",
                    client_slug=business.client.slug,
                    business_slug=business.slug,
                    sale_id=new_sale.id,
                )
            )
        except Exception as e:
            flash(f"Error inesperado: {str(e)}", "error")
            return redirect(
                url_for(
                    "sale.sales",
                    client_slug=business.client.slug,
                    business_slug=business.slug,
                )
            )

    return render_template(
        "sale/details.html",
        business=business,
        sale=sale,
        products=details_context["sale_details"],
        add_product_form=add_product_form,
        remove_product_form=remove_product_form,
        update_product_form=update_product_form,
        update_sale_form=update_sale_form,
        add_sale_form=add_sale_form,
    )


