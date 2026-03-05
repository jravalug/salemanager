from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services import IncomeService
from app.services.cash_flow_service import CashFlowService

bp = Blueprint(
    "cash_flow",
    __name__,
    url_prefix="/clients/<string:client_slug>/business/<string:business_slug>/income",
)

cash_flow_service = CashFlowService()


@bp.route("/funds/reports-panel", methods=["GET"])
def funds_reports_panel(client_slug, business_slug):
    """Panel parcial HTMX para reportes operativos de cash-flow."""
    income_service = IncomeService()

    try:
        business, _ = income_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except Exception:
        return render_template(
            "income/partials/_fund_reports_panel.html",
            business=None,
            cash_balance_report={
                "entries": [],
                "totals": {"bank": 0, "cash": 0, "overall": 0},
            },
            cash_movement_report={
                "entries": [],
                "totals": {"count": 0, "inflows": 0, "outflows": 0, "net": 0},
                "filters": {
                    "start_date": None,
                    "end_date": None,
                    "subaccount_code": None,
                    "chronological": False,
                    "limit": 100,
                },
            },
            report_subaccount_options=[],
            report_error="No se pudo resolver el negocio para generar reportes.",
        )

    start_date = (request.args.get("start_date") or "").strip() or None
    end_date = (request.args.get("end_date") or "").strip() or None
    subaccount_code = (request.args.get("subaccount_code") or "").strip() or None
    chronological = (request.args.get("chronological") or "") in {
        "1",
        "true",
        "True",
        "on",
    }

    report_error = None
    try:
        cash_balance_report = cash_flow_service.get_cash_balance_report(
            business_id=business.id
        )
        cash_movement_report = cash_flow_service.get_cash_movement_report(
            business_id=business.id,
            start_date=start_date,
            end_date=end_date,
            subaccount_code=subaccount_code,
            chronological=chronological,
            limit=100,
        )
    except Exception as exc:
        report_error = str(exc)
        cash_balance_report = {
            "entries": [],
            "totals": {"bank": 0, "cash": 0, "overall": 0},
        }
        cash_movement_report = {
            "entries": [],
            "totals": {"count": 0, "inflows": 0, "outflows": 0, "net": 0},
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "subaccount_code": subaccount_code,
                "chronological": chronological,
                "limit": 100,
            },
        }

    try:
        report_subaccount_options = cash_flow_service.list_fund_configurations(
            business_id=business.id
        )
    except Exception:
        report_subaccount_options = []

    return render_template(
        "income/partials/_fund_reports_panel.html",
        business=business,
        cash_balance_report=cash_balance_report,
        cash_movement_report=cash_movement_report,
        report_subaccount_options=report_subaccount_options,
        report_error=report_error,
    )


@bp.route("/funds/settings", methods=["GET", "POST"])
def funds_settings(client_slug, business_slug):
    """Administración mínima de fondos por negocio (F10 UI)."""
    income_service = IncomeService()
    is_htmx_request = request.headers.get("HX-Request") == "true"

    try:
        business, _ = income_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("client.list_clients"))

    if request.method == "POST":
        action = (request.form.get("action") or "").strip()
        message = ""
        message_type = "success"
        try:
            if action == "update":
                subaccount_code = (request.form.get("subaccount_code") or "").strip()
                threshold_raw = (
                    request.form.get("threshold_max_per_operation") or ""
                ).strip()
                target_raw = (request.form.get("target_balance") or "").strip()

                cash_flow_service.upsert_fund_configuration(
                    business_id=business.id,
                    subaccount_code=subaccount_code,
                    is_active=(request.form.get("is_active") == "on"),
                    threshold_max_per_operation=(
                        float(threshold_raw) if threshold_raw else None
                    ),
                    requires_documentation=(
                        request.form.get("requires_documentation") == "on"
                    ),
                    target_balance=(float(target_raw) if target_raw else None),
                    display_name=(request.form.get("display_name") or "").strip(),
                    commit=True,
                )
                message = "Configuración de fondo actualizada."

            elif action == "create_custom":
                threshold_raw = (
                    request.form.get("new_threshold_max_per_operation") or ""
                ).strip()
                target_raw = (request.form.get("new_target_balance") or "").strip()

                cash_flow_service.create_custom_fund(
                    business_id=business.id,
                    subaccount_code=(
                        request.form.get("new_subaccount_code") or ""
                    ).strip(),
                    display_name=(request.form.get("new_display_name") or "").strip(),
                    location=(request.form.get("new_location") or "cash_box").strip(),
                    threshold_max_per_operation=(
                        float(threshold_raw) if threshold_raw else None
                    ),
                    requires_documentation=(
                        request.form.get("new_requires_documentation") == "on"
                    ),
                    target_balance=(float(target_raw) if target_raw else None),
                    is_active=(request.form.get("new_is_active") == "on"),
                    commit=True,
                )
                message = "Fondo personalizado creado correctamente."
            elif action == "transfer":
                amount_raw = (request.form.get("transfer_amount") or "").strip()
                cash_flow_service.transfer_between_subaccounts(
                    business_id=business.id,
                    source_subaccount_code=(
                        request.form.get("source_subaccount_code") or ""
                    ).strip(),
                    target_subaccount_code=(
                        request.form.get("target_subaccount_code") or ""
                    ).strip(),
                    amount=float(amount_raw or 0),
                    description=(
                        request.form.get("transfer_description") or ""
                    ).strip(),
                    occurred_at_value=(request.form.get("occurred_at") or "").strip()
                    or None,
                    supporting_document_ref=(
                        request.form.get("supporting_document_ref") or ""
                    ).strip()
                    or None,
                    source_type="manual_transfer",
                    source_ref=None,
                    commit=True,
                )
                message = "Transferencia registrada correctamente."
            else:
                message = "Acción no reconocida."
                message_type = "error"
        except ValueError as exc:
            message = str(exc)
            message_type = "error"
        except Exception as exc:
            message = f"Error al guardar configuración de fondos: {exc}"
            message_type = "error"

        if is_htmx_request:
            report_error = None
            try:
                fund_configs = cash_flow_service.list_fund_configurations(
                    business_id=business.id
                )
            except ValueError as exc:
                message = str(exc)
                message_type = "error"
                fund_configs = []

            try:
                cash_balance_report = cash_flow_service.get_cash_balance_report(
                    business_id=business.id
                )
                cash_movement_report = cash_flow_service.get_cash_movement_report(
                    business_id=business.id,
                    limit=100,
                )
            except Exception as exc:
                report_error = str(exc)
                cash_balance_report = {
                    "entries": [],
                    "totals": {"bank": 0, "cash": 0, "overall": 0},
                }
                cash_movement_report = {
                    "entries": [],
                    "totals": {"count": 0, "inflows": 0, "outflows": 0, "net": 0},
                    "filters": {
                        "start_date": None,
                        "end_date": None,
                        "subaccount_code": None,
                        "chronological": False,
                        "limit": 100,
                    },
                }

            return render_template(
                "income/partials/_funds_settings_content.html",
                business=business,
                fund_configs=fund_configs,
                inline_message=message,
                inline_message_type=message_type,
                cash_balance_report=cash_balance_report,
                cash_movement_report=cash_movement_report,
                report_subaccount_options=fund_configs,
                report_error=report_error,
            )

        flash(message, message_type)

        return redirect(
            url_for(
                "cash_flow.funds_settings",
                client_slug=client_slug,
                business_slug=business_slug,
            )
        )

    try:
        fund_configs = cash_flow_service.list_fund_configurations(
            business_id=business.id
        )
    except ValueError as exc:
        flash(str(exc), "error")
        fund_configs = []

    report_error = None
    try:
        cash_balance_report = cash_flow_service.get_cash_balance_report(
            business_id=business.id
        )
        cash_movement_report = cash_flow_service.get_cash_movement_report(
            business_id=business.id,
            limit=100,
        )
    except Exception as exc:
        report_error = str(exc)
        cash_balance_report = {
            "entries": [],
            "totals": {"bank": 0, "cash": 0, "overall": 0},
        }
        cash_movement_report = {
            "entries": [],
            "totals": {"count": 0, "inflows": 0, "outflows": 0, "net": 0},
            "filters": {
                "start_date": None,
                "end_date": None,
                "subaccount_code": None,
                "chronological": False,
                "limit": 100,
            },
        }

    return render_template(
        "income/funds_settings.html",
        business=business,
        fund_configs=fund_configs,
        inline_message=None,
        inline_message_type=None,
        cash_balance_report=cash_balance_report,
        cash_movement_report=cash_movement_report,
        report_subaccount_options=fund_configs,
        report_error=report_error,
    )
