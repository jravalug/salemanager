from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from app.forms import ProductForm, ProductDetailForm
from app.models import Business, Product
from app.extensions import db
from app.models import ProductDetail, InventoryItem


bp = Blueprint("product", __name__, url_prefix="/business/<int:business_id>/product")


@bp.route("/list", methods=["GET", "POST"])
def list(business_id):
    business = Business.query.get_or_404(business_id)

    add_product_form = ProductForm()

    if add_product_form.validate_on_submit():
        # Crear un nuevo producto con los datos del formulario
        new_product = Product(
            name=add_product_form.name.data,
            price=add_product_form.price.data,
            instructions=add_product_form.instructions.data,
            description=add_product_form.description.data,
            category=add_product_form.category.data,
            sku=add_product_form.sku.data,
            is_active=add_product_form.is_active.data,
            business_id=business.id,  # Suponiendo que tienes acceso al negocio actual
        )

        db.session.add(new_product)
        db.session.commit()
        flash("Producto agregado correctamente", "success")
        return redirect(
            url_for(
                "product.technical_card",
                business_id=business.id,
                product_id=new_product.id,
            )
        )

    products_list = (
        Product.query.filter_by(business_id=business.id).order_by(Product.name).all()
    )
    return render_template(
        "product/list.html",
        business=business,
        products=products_list,
        add_product_form=add_product_form,
    )


@bp.route(
    "/<int:product_id>/technical-card",
    methods=["GET", "POST"],
)
def technical_card(business_id, product_id):
    business = Business.query.get_or_404(business_id)
    product = Product.query.get_or_404(product_id)

    add_inventory_item_form = ProductDetailForm()
    update_product_form = ProductForm(request.form, obj=product)

    if add_inventory_item_form.validate_on_submit():
        inventory_item_id = add_inventory_item_form.inventory_item.data
        quantity = add_inventory_item_form.quantity.data

        # Verificar si ya existe esta relación
        existing_relation = ProductDetail.query.filter_by(
            product_id=product.id, inventory_item_id=inventory_item_id
        ).first()

        if existing_relation:
            flash("Esta materia prima ya está asociada al producto.", "warning")
        else:
            # Crear una nueva relación
            new_relation = ProductDetail(
                product_id=product.id,
                inventory_item_id=inventory_item_id,
                quantity=quantity,
            )
            db.session.add(new_relation)
            db.session.commit()
            flash("Materia prima agregada al producto correctamente.", "success")

        return redirect(
            url_for(
                "product.technical_card", business_id=business.id, product_id=product.id
            )
        )
    if update_product_form.validate_on_submit():
        product.name = (update_product_form.name.data,)
        product.price = (update_product_form.price.data,)
        product.instructions = (update_product_form.instructions.data,)
        product.description = (update_product_form.description.data,)
        product.category = (update_product_form.category.data,)
        product.sku = (update_product_form.sku.data,)
        product.is_active = (update_product_form.is_active.data,)

        flash("Producto actualizado correctamente.", "success")
        return redirect(
            url_for(
                "product.technical_card", business_id=business.id, product_id=product.id
            )
        )

    # Obtener las materias primas asociadas al producto
    inventory_items = (
        db.session.query(ProductDetail, InventoryItem)
        .join(InventoryItem, ProductDetail.inventory_item_id == InventoryItem.id)
        .filter(ProductDetail.product_id == product.id)
        .all()
    )

    return render_template(
        "product/technical_card.html",
        business=business,
        product=product,
        inventory_items=inventory_items,
        update_product_form=update_product_form,
        add_inventory_item_form=add_inventory_item_form,
    )


@bp.route(
    "/<int:product_id>/update-raw-material",
    methods=["POST"],
)
def update_inventory_item(business_id, product_id):
    # Obtener el negocio y el producto
    business = Business.query.get_or_404(business_id)
    product = Product.query.get_or_404(product_id)

    # Buscar la relación específica usando el ID de ProductDetail
    prm_id = request.form.get("prm_id")
    relation = ProductDetail.query.get_or_404(prm_id)
    if not relation:
        flash(
            f"Error al intentar eliminar la materia prima.",
            "error",
        )
        return redirect(
            url_for(
                "product.technical_card", business_id=business.id, product_id=product.id
            )
        )

    # Obtener los datos del formulario
    prm_quantity = request.form.get("prm_quantity")
    print(f"La cantidad es: {prm_quantity}")
    inventory_item_name = relation.inventory_item.name

    # Actualizar la cantidad
    relation.quantity = prm_quantity
    db.session.commit()

    flash(
        f"La materia prima '{inventory_item_name}' ha sido actualizada.",
        "success",
    )
    return redirect(
        url_for(
            "product.technical_card", business_id=business.id, product_id=product.id
        )
    )


@bp.route(
    "/<int:product_id>/remove-raw-material/<int:prm_id>",
    methods=["POST"],
)
def remove_inventory_item(business_id, product_id, prm_id):
    # Obtener el negocio
    business = Business.query.get_or_404(business_id)
    product = Product.query.get_or_404(product_id)

    # Buscar la relación específica usando el ID de ProductDetail
    relation = ProductDetail.query.get_or_404(prm_id)
    if not relation:
        flash(
            f"Error al intentar eliminar la materia prima.",
            "error",
        )
        return redirect(
            url_for(
                "product.technical_card", business_id=business.id, product_id=product.id
            )
        )

    # Acceder al nombre del producto antes de eliminarlo
    inventory_item_name = relation.inventory_item.name

    # Eliminar el producto de la venta
    db.session.delete(relation)
    db.session.commit()

    flash(
        f"La materia prima '{inventory_item_name}' ha sido eliminada de la carta tecnológica.",
        "success",
    )
    return redirect(
        url_for(
            "product.technical_card", business_id=business.id, product_id=product.id
        )
    )
