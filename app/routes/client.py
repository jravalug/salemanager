from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError

from app.forms import AccountingSettingsForm, ClientForm
from app.models import AppSetting
from app.services import AppSettingService, ClientAccountingService, ClientService

bp = Blueprint("client", __name__, url_prefix="/clients")

client_service = ClientService()


@bp.route("/list", methods=["GET", "POST"])
def list_clients():
    form = ClientForm()

    if form.validate_on_submit():
        try:
            client_service.create_client_with_default_business(form)
            flash("Cliente creado correctamente.", "success")
        except SQLAlchemyError as exc:
            flash(f"Error al crear cliente: {exc}", "error")

        return redirect(url_for("client.list_clients"))

    client_cards, summary = client_service.get_clients_overview()

    return render_template(
        "client/list.html",
        client_cards=client_cards,
        summary=summary,
        form=form,
    )


@bp.route("/<string:client_slug>", methods=["GET", "POST"])
def detail_or_edit(client_slug):
    client = client_service.get_client_by_slug(client_slug)
    if not client:
        abort(404)
    form = ClientForm(obj=client)

    if request.method == "GET":
        form.phone_numbers_input.data = ", ".join(client.phone_numbers or [])
        form.email_addresses_input.data = ", ".join(client.email_addresses or [])

    if form.validate_on_submit():
        try:
            client_service.update_client_from_form(client, form)
            flash("Cliente actualizado correctamente.", "success")
            return redirect(url_for("client.detail_or_edit", client_slug=client.slug))
        except SQLAlchemyError as exc:
            flash(f"Error al actualizar cliente: {exc}", "error")

    client_businesses, business_groups, total_sub_businesses = (
        client_service.get_business_groups_for_client(client)
    )

    return render_template(
        "client/detail_or_edit.html",
        client=client,
        client_businesses=client_businesses,
        business_groups=business_groups,
        total_sub_businesses=total_sub_businesses,
        form=form,
    )


@bp.route("/evaluate-regime", methods=["POST"])
def evaluate_regime():
    try:
        summary = ClientAccountingService().evaluate_annual_regime_transition(
            force=True
        )
        flash(
            "Evaluación completada. "
            f"Evaluados: {summary['evaluated_clients']} | "
            f"Actualizados: {summary['updated_clients']}",
            "success",
        )
    except Exception as exc:
        flash(f"Error al evaluar régimen: {exc}", "error")

    return redirect(url_for("client.list_clients"))


@bp.route("/settings", methods=["GET", "POST"])
def accounting_settings():
    fallback_threshold = float(
        current_app.config.get("ACCOUNTING_FISCAL_THRESHOLD", 500000)
    )
    default_threshold = float(
        AppSettingService.get_float(
            AppSetting.KEY_ACCOUNTING_FISCAL_THRESHOLD,
            default=fallback_threshold,
        )
    )
    form = AccountingSettingsForm()

    if request.method == "GET":
        form.accounting_fiscal_threshold.data = default_threshold

    if form.validate_on_submit():
        AppSettingService.set_value(
            AppSetting.KEY_ACCOUNTING_FISCAL_THRESHOLD,
            str(form.accounting_fiscal_threshold.data),
            description="Umbral anual para transición de régimen fiscal a financiera",
        )
        flash("Configuración global actualizada correctamente.", "success")
        return redirect(url_for("client.accounting_settings"))

    return render_template(
        "client/settings.html",
        form=form,
    )


@bp.route("/<string:client_slug>/dashboard", methods=["GET"])
def client_dashboard(client_slug):
    client = client_service.get_client_by_slug(client_slug)
    if not client:
        abort(404)

    selected_business_slug = request.args.get("business_slug", type=str)
    dashboard_context = client_service.build_client_dashboard_context(
        client=client,
        selected_business_slug=selected_business_slug,
    )
    if not dashboard_context:
        return redirect(url_for("client.list_clients"))

    return render_template(
        "client/dashboard.html",
        client=client,
        **dashboard_context,
    )
