from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Business, Product, Sale, SaleProduct
from app.forms import BusinessForm
from app.services.business_service import create_business, update_business
from app.utils.file_utils import handle_logo_upload

bp = Blueprint("business", __name__, url_prefix="/business")


@bp.route("/list", methods=["GET", "POST"])
def list():
    """
    Muestra la lista de negocios y maneja la creación de nuevos negocios.
    """
    form = BusinessForm()

    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        logo_path = handle_logo_upload(form.logo.data)

        if logo_path is not None:
            try:
                create_business(name, description, logo_path)
                flash("Negocio agregado correctamente", "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Error al agregar el negocio: {str(e)}", "error")
            except Exception as e:
                flash(f"Error inesperado: {str(e)}", "error")
        return redirect(url_for("business.list"))

    business_list = Business.query.all()
    return render_template("business/list.html", business_list=business_list, form=form)


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
                update_business(
                    business, form.name.data, form.description.data, logo_path
                )
                flash("Negocio actualizado correctamente", "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Error al actualizar el negocio: {str(e)}", "error")
            except Exception as e:
                flash(f"Error inesperado: {str(e)}", "error")
        return redirect(url_for("business.detail_or_edit", business_id=business.id))

    return render_template(
        "business/detail_or_edit.html", business=business, form=form, edit=edit
    )


@bp.route("/<int:business_id>/dashboard")
def dashboard(business_id):
    """
    Muestra el dashboard de un negocio con ventas mensuales.
    """
    business = Business.query.get_or_404(business_id)
    monthly_totals = (
        db.session.query(
            func.strftime("%Y-%m", Sale.date).label("month"),
            func.sum(SaleProduct.quantity * Product.price).label("total"),
        )
        .join(Sale.products)
        .join(SaleProduct.product)
        .filter(Sale.business_id == business.id)
        .group_by(func.strftime("%Y-%m", Sale.date))
        .all()
    )
    total_general = sum(total for month, total in monthly_totals)
    return render_template(
        "business/dashboard.html",
        business=business,
        monthly_totals=dict(monthly_totals),
        total_general=total_general,
    )
