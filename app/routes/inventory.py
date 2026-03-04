from flask import Blueprint, flash, redirect, render_template, request, url_for
from app.forms import InventoryItemForm
from app.services import InventoryService

bp = Blueprint(
    "inventory",
    __name__,
    url_prefix="/clients/<string:client_slug>/business/<string:business_slug>/inventory",
)

inventory_service = InventoryService()


@bp.route("/item/list", methods=["GET", "POST"])
def item_list(client_slug, business_slug):
    try:
        business = inventory_service.resolve_business(client_slug, business_slug)
    except ValueError:
        return redirect(url_for("client.list_clients"))

    form = InventoryItemForm()

    if form.validate_on_submit():
        inventory_service.create_item(name=form.name.data, unit=form.unit.data)

        flash("Articulo de inventario agregado correctamente", "success")
        return redirect(
            url_for(
                "inventory.item_list",
                client_slug=business.client.slug,
                business_slug=business.slug,
            )
        )

    inventory_items_list = inventory_service.get_all_items()

    return render_template(
        "inventory/item_list.html",
        business=business,
        inventory_items=inventory_items_list,
        form=form,
    )


@bp.route("/<int:inventory_item_id>", methods=["POST"])
def item_update(client_slug, business_slug, inventory_item_id):
    try:
        business = inventory_service.resolve_business(client_slug, business_slug)
    except ValueError:
        return redirect(url_for("client.list_clients"))

    inventory_service.update_item(
        inventory_item_id=inventory_item_id,
        name=request.form["name"],
        unit=request.form["unit"],
    )
    flash("Articulo de inventario actualizado correctamente", "success")
    return redirect(
        url_for(
            "inventory.item_list",
            client_slug=business.client.slug,
            business_slug=business.slug,
        )
    )
