from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from app.forms import ProductForm, ProductDetailForm, DeleteProductDetailForm
from app.services import BusinessService, ProductService
from app.utils.slug_utils import get_business_by_slugs


bp = Blueprint(
    "product",
    __name__,
    url_prefix="/clients/<string:client_slug>/business/<string:business_slug>/product",
)
product_service = ProductService()
business_service = BusinessService()


@bp.route("/list", methods=["GET", "POST"])
def list(client_slug, business_slug):
    """
    Lista los productos de un negocio y permite agregar nuevos productos.
    """
    # Obtener el negocio y sus filtros
    business = get_business_by_slugs(client_slug, business_slug)
    if not business:
        return redirect(url_for("client.list_clients"))
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
                    client_slug=business.client.slug,
                    business_slug=business.slug,
                    product_id=new_product.id,
                )
            )
        except RuntimeError as e:
            flash(str(e), "error")
            return redirect(
                url_for(
                    "product.list",
                    client_slug=business.client.slug,
                    business_slug=business.slug,
                )
            )

    products_list = product_service.get_all_products(
        business_id=business_filter["business_id"]
    )
    categories, sale_stats = product_service.get_product_list_stats(
        business_id=business_filter["business_id"],
        products_list=products_list,
    )
    return render_template(
        "product/list.html",
        business=business,
        products=products_list,
        add_product_form=add_product_form,
        categories=categories,
        sale_stats=sale_stats,
    )


@bp.route(
    "/<int:product_id>/technical-card",
    methods=["GET", "POST"],
)
def technical_card(client_slug, business_slug, product_id):
    """
    Gestiona la ficha técnica de un producto, incluyendo la edición del producto
    y la asociación de materias primas.
    """
    business_service = BusinessService()

    # Obtener el negocio y el producto
    try:
        business = get_business_by_slugs(client_slug, business_slug)
        if not business:
            raise ValueError("Negocio no encontrado")
        # Determinar los filtros según el tipo de negocio
        business_filter = business_service.get_parent_filters(business=business)

        product = product_service.get_full_product(
            business_id=business_filter["business_id"], product_id=product_id
        )
    except Exception as e:
        flash(str(e), "error")
        return redirect(
            url_for(
                "product.list",
                client_slug=client_slug,
                business_slug=business_slug,
            )
        )

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
                "product.technical_card",
                client_slug=business.client.slug,
                business_slug=business.slug,
                product_id=product.id,
            )
        )

    try:
        if remove_raw_material_form.validate_on_submit():
            removed_name = product_service.remove_raw_material_with_name(
                product_id=product.id,
                raw_material_id=remove_raw_material_form.raw_material_id.data,
            )
            flash(
                f"Materia prima {removed_name} eliminada.",
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
