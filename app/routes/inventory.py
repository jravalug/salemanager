from flask import Blueprint, flash, redirect, render_template, request, url_for
from app.extensions import db
from app.forms import InventoryItemForm
from app.models import Business, InventoryItem

bp = Blueprint(
    "inventory", __name__, url_prefix="/business/<int:business_id>/inventory"
)


@bp.route("/item/list", methods=["GET", "POST"])
def item_list(business_id):
    business = Business.query.get_or_404(business_id)

    form = InventoryItemForm()

    if form.validate_on_submit():
        name = form.name.data
        unit = form.unit.data

        new_inventory_item = InventoryItem(name=name, unit=unit)
        db.session.add(new_inventory_item)
        db.session.commit()

        flash("Articulo de inventario agregado correctamente", "success")
        return redirect(url_for("inventory.item_list", business_id=business.id))

    inventory_items_list = InventoryItem.query.order_by(InventoryItem.name).all()

    return render_template(
        "inventory/item_list.html",
        business=business,
        inventory_items=inventory_items_list,
        form=form,
    )


@bp.route("/<int:inventory_item_id>", methods=["POST"])
def item_update(business_id, inventory_item_id):
    business = Business.query.get_or_404(business_id)

    inventory_item = InventoryItem.query.get_or_404(inventory_item_id)
    inventory_item.name = request.form["name"]
    inventory_item.unit = request.form["unit"]
    db.session.commit()
    flash("Articulo de inventario actualizado correctamente", "success")
    return redirect(url_for("inventory.item_list", business_id=business.id))
