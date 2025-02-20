from flask import Blueprint, flash, redirect, render_template, request, url_for
from app.extensions import db
from app.forms import RawMaterialForm
from app.models import Business, RawMaterial

bp = Blueprint(
    "raw_material", __name__, url_prefix="/business/<int:business_id>/raw_material"
)


@bp.route("/list", methods=["GET", "POST"])
def list(business_id):
    business = Business.query.get_or_404(business_id)

    form = RawMaterialForm()

    if form.validate_on_submit():
        name = form.name.data
        unit = form.unit.data

        new_raw_material = RawMaterial(name=name, unit=unit)
        db.session.add(new_raw_material)
        db.session.commit()

        flash("Materia prima agregada correctamente", "success")
        return redirect(url_for("raw_material.list", business_id=business.id))

    raw_materials_list = RawMaterial.query.order_by(RawMaterial.name).all()

    return render_template(
        "raw_material/list.html",
        business=business,
        raw_materials=raw_materials_list,
        form=form,
    )


@bp.route("/<int:raw_material_id>", methods=["POST"])
def update(business_id, raw_material_id):
    business = Business.query.get_or_404(business_id)

    raw_material = RawMaterial.query.get_or_404(raw_material_id)
    raw_material.name = request.form["name"]
    raw_material.unit = request.form["unit"]
    db.session.commit()
    flash("Materia prima actualizada correctamente", "success")
    return redirect(url_for("raw_material.list", business_id=business.id))
