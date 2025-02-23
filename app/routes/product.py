from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from app.forms import ProductForm, ProductRawMaterialForm, ProductInstructionsForm
from app.models import Business, Product
from app.extensions import db
from app.models import ProductRawMaterial, RawMaterial


bp = Blueprint("product", __name__, url_prefix="/business/<int:business_id>/product")


@bp.route("/list", methods=["GET", "POST"])
def list(business_id):
    business = Business.query.get_or_404(business_id)

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        new_product = Product(name=name, price=price, business_id=business.id)
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
        "product/list.html", business=business, products=products_list
    )


@bp.route(
    "/<int:product_id>/technical-card",
    methods=["GET", "POST"],
)
def technical_card(business_id, product_id):
    business = Business.query.get_or_404(business_id)
    product = Product.query.get_or_404(product_id)

    add_raw_maerial_form = ProductRawMaterialForm()
    update_product_form = ProductForm(request.form, obj=product)

    if add_raw_maerial_form.validate_on_submit():
        raw_material_id = add_raw_maerial_form.raw_material.data
        quantity = add_raw_maerial_form.quantity.data

        # Verificar si ya existe esta relación
        existing_relation = ProductRawMaterial.query.filter_by(
            product_id=product.id, raw_material_id=raw_material_id
        ).first()

        if existing_relation:
            flash("Esta materia prima ya está asociada al producto.", "warning")
        else:
            # Crear una nueva relación
            new_relation = ProductRawMaterial(
                product_id=product.id,
                raw_material_id=raw_material_id,
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
        name = update_product_form.name.data
        price = update_product_form.price.data
        instructions = update_product_form.instructions.data

        product.name = name
        product.price = price
        product.instructions = instructions
        db.session.commit()

        flash("Producto actualizado correctamente.", "success")
        return redirect(
            url_for(
                "product.technical_card", business_id=business.id, product_id=product.id
            )
        )

    # Obtener las materias primas asociadas al producto
    raw_materials = (
        db.session.query(ProductRawMaterial, RawMaterial)
        .join(RawMaterial, ProductRawMaterial.raw_material_id == RawMaterial.id)
        .filter(ProductRawMaterial.product_id == product.id)
        .all()
    )

    return render_template(
        "product/technical_card.html",
        business=business,
        product=product,
        raw_materials=raw_materials,
        update_product_form=update_product_form,
        add_raw_maerial_form=add_raw_maerial_form,
    )


@bp.route(
    "/<int:product_id>/update-raw-material",
    methods=["POST"],
)
def update_raw_material(business_id, product_id):
    # Obtener el negocio y el producto
    business = Business.query.get_or_404(business_id)
    product = Product.query.get_or_404(product_id)

    # Buscar la relación específica usando el ID de ProductRawMaterial
    prm_id = request.form.get("prm_id")
    relation = ProductRawMaterial.query.get_or_404(prm_id)
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
    raw_material_name = relation.raw_material.name

    # Actualizar la cantidad
    relation.quantity = prm_quantity
    db.session.commit()

    flash(
        f"La materia prima '{raw_material_name}' ha sido actualizada.",
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
def remove_raw_material(business_id, product_id, prm_id):
    # Obtener el negocio
    business = Business.query.get_or_404(business_id)
    product = Product.query.get_or_404(product_id)

    # Buscar la relación específica usando el ID de ProductRawMaterial
    relation = ProductRawMaterial.query.get_or_404(prm_id)
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
    raw_material_name = relation.raw_material.name

    # Eliminar el producto de la venta
    db.session.delete(relation)
    db.session.commit()

    flash(
        f"La materia prima '{raw_material_name}' ha sido eliminada de la carta tecnológica.",
        "success",
    )
    return redirect(
        url_for(
            "product.technical_card", business_id=business.id, product_id=product.id
        )
    )
