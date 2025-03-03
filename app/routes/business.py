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
from app.models import Business, Product, Sale, SaleDetail
from app.forms import BusinessForm
from app.services.business_service import BusinessService
from app.utils.file_utils import handle_logo_upload

bp = Blueprint("business", __name__, url_prefix="/business")


@bp.route("/list", methods=["GET", "POST"])
def list():
    """
    Muestra la lista de negocios y maneja la creación de nuevos negocios.
    """
    business_service = BusinessService()
    form = BusinessForm()

    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        logo_path = None

        # Solo manejar la subida del logo si se proporciona un archivo
        if form.logo.data and form.logo.data.filename != "":
            logo_path = handle_logo_upload(form.logo.data)
            if logo_path is None:
                return redirect(
                    url_for("business.list")
                )  # Detener si hay un error en la subida

        try:
            business_service.create_business(
                name=name, description=description, logo=logo_path
            )
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
    business_service = BusinessService()
    business = Business.query.get_or_404(business_id)
    edit = request.args.get("edit", False)
    form = BusinessForm(obj=business)

    if edit and form.validate_on_submit():
        logo_path = handle_logo_upload(form.logo.data)
        if logo_path is not None:
            try:
                business_service.update_business(
                    business=business,
                    name=form.name.data,
                    description=form.description.data,
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
                is_general=form.is_general.data,
            )
            flash("Negocio actualizado correctamente", "success")

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
            func.sum(SaleDetail.quantity * Product.price).label("total"),
        )
        .join(Sale.products)
        .join(SaleDetail.product)
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


@bp.route("/<int:business_id>/add-sub-business", methods=["GET", "POST"])
def add_sub_business(business_id):
    # Obtener el negocio general
    business = Business.query.get_or_404(business_id)

    if not business.is_general:
        flash("Este negocio no es un negocio general.", "danger")
        return redirect(url_for("main.index"))

    # Inicializar el formulario
    form = BusinessForm()

    if form.validate_on_submit():
        # Crear un nuevo negocio específico
        new_sub_business = Business(
            name=form.name.data,
            description=business.description,
            is_general=False,  # Es un negocio específico
            parent_business_id=business.id,  # Asociarlo al negocio general
        )

        db.session.add(new_sub_business)
        db.session.commit()

        flash("Negocio específico agregado correctamente.", "success")
        return redirect(url_for("business.dashboard", business_id=business.id))

    return render_template(
        "business/add_sub_business.html", business=business, form=form
    )
