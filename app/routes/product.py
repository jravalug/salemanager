from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from app.extensions import db
from app.forms import ProductForm, ProductDetailForm, DeleteProductDetailForm
from app.models import Business, InventoryItem
from app.services import BusinessService, ProductService


bp = Blueprint("product", __name__, url_prefix="/business/<int:business_id>/product")
product_service = ProductService()
business_service = BusinessService()


@bp.route("/list", methods=["GET", "POST"])
def list(business_id):
    """
    Lista los productos de un negocio y permite agregar nuevos productos.
    """
    # Obtener el negocio y sus filtros
    business = Business.query.get_or_404(business_id)
    business_filter = business_service.get_parent_filters(business=business)

    # Inicializar el formulario para agregar productos
    add_product_form = ProductForm()

    # Procesar el formulario si se envía
    if add_product_form.validate_on_submit():
        try:
            # Crear el producto usando el servicio
            new_product = product_service.create_product(
                business_filter["business_id"],
                add_product_form,
            )
            flash("Producto agregado correctamente.", "success")
            return redirect(
                url_for(
                    "product.technical_card",
                    business_id=business.id,
                    product_id=new_product.id,
                )
            )
        except RuntimeError as e:
            flash(str(e), "error")
            return redirect(
                url_for(
                    "product.list",
                    business_id=business.id,
                )
            )

    products_list = product_service.get_all_products(
        business_id=business_filter["business_id"]
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
    """
    Gestiona la ficha técnica de un producto, incluyendo la edición del producto
    y la asociación de materias primas.
    """
    business_service = BusinessService()

    # Obtener el negocio y el producto
    try:
        business = Business.query.get_or_404(business_id)
        # Determinar los filtros según el tipo de negocio
        business_filter = business_service.get_parent_filters(business=business)

        product = product_service.get_full_product(
            business_id=business_filter["business_id"], product_id=product_id
        )
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("product.list", business_id=business_id))

    # Formularios
    add_raw_material_form = ProductDetailForm(prefix="add_raw_material")
    update_raw_material_form = ProductDetailForm(prefix="update_raw_material")
    remove_raw_material_form = DeleteProductDetailForm(prefix="remove_raw_material")
    update_product_form = ProductForm(
        request.form, obj=product, prefix="update_product"
    )

    # Función auxiliar para redirigir a los detalles del producto
    def redirect_to_technical_card():
        return redirect(
            url_for(
                "product.technical_card", business_id=business.id, product_id=product.id
            )
        )

    try:
        if remove_raw_material_form.validate_on_submit():
            raw_material_id = remove_raw_material_form.raw_material_id.data
            removed_raw_material = InventoryItem.query.get(raw_material_id)
            if not removed_raw_material:
                flash("La materia prima seleccionada no existe.", "error")
                return redirect_to_technical_card()
            product_service.remove_raw_material(
                product_id=product.id,
                raw_material_id=removed_raw_material.id,
            )
            flash(
                f"Materia prima {removed_raw_material.name} eliminada.",
                "success",
            )
            return redirect_to_technical_card()
        if add_raw_material_form.validate_on_submit():
            new_raw_material = product_service.add_raw_material(
                product_id=product.id,
                raw_material_id=add_raw_material_form.raw_material_id.data,
                quantity=add_raw_material_form.quantity.data,
            )
            flash(
                f"Materia prima {new_raw_material.raw_material.name} agregada.",
                "success",
            )
            return redirect_to_technical_card()
        if update_raw_material_form.validate_on_submit():
            print(update_product_form)
            updated_raw_material = product_service.update_raw_material(
                product_id=product.id,
                raw_material_id=update_raw_material_form.raw_material_id.data,
                quantity=update_raw_material_form.quantity.data,
            )
            flash(
                f"Materia prima {updated_raw_material.raw_material.name} actualizada.",
                "success",
            )
            return redirect_to_technical_card()
        if update_product_form.validate_on_submit():
            updated_product = product_service.update_product(
                product, update_product_form
            )
            flash(
                f"El producto: {updated_product.name} fue actualizado correctamente",
                "success",
            )
            return redirect_to_technical_card()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error en el producto {product_id}: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect_to_technical_card()

    return render_template(
        "product/technical_card.html",
        business=business,
        product=product,
        raw_materials=product.raw_materials,
        update_product_form=update_product_form,
        add_raw_material_form=add_raw_material_form,
        update_raw_material_form=update_raw_material_form,
        remove_raw_material_form=remove_raw_material_form,
    )
