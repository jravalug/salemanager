from flask import Blueprint, jsonify, request, send_file

from app.services import IncomeService, IncomeReportService, CashFlowService

bp = Blueprint("api_income", __name__)

income_service = IncomeService()
income_report_service = IncomeReportService()
cash_flow_service = CashFlowService()


@bp.route("/records", methods=["GET"])
def get_income_sales(client_slug, business_slug):
    try:
        business, _ = income_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except ValueError:
        return jsonify([])
    return jsonify(income_service.get_incomes_api_data(business.id))


@bp.route("/pending", methods=["GET"])
def get_pending_incomes(client_slug, business_slug):
    try:
        business, _ = income_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except ValueError:
        return jsonify([])

    pending_events = income_service.get_pending_income_events(business.id)
    return jsonify(
        [
            {
                "id": event.id,
                "event_date": event.event_date.strftime("%Y-%m-%d"),
                "amount": float(event.amount or 0),
                "origin_type": event.origin_type,
                "payment_channel": event.payment_channel,
                "collection_status": event.collection_status,
                "description": event.description,
                "source_ref": event.source_ref,
            }
            for event in pending_events
        ]
    )


@bp.route("/events/<int:income_event_id>/reconcile", methods=["POST"])
def reconcile_income_event(client_slug, business_slug, income_event_id):
    try:
        business, _ = income_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    payload = request.get_json(silent=True) or {}
    bank_operation_number = payload.get(
        "bank_operation_number", request.form.get("bank_operation_number", "")
    )
    collected_date = payload.get("collected_date", request.form.get("collected_date"))
    reconciled_by = payload.get("reconciled_by", request.form.get("reconciled_by"))
    bank_name = payload.get("bank_name", request.form.get("bank_name"))

    try:
        event = income_service.reconcile_income_event(
            business_id=business.id,
            income_event_id=income_event_id,
            bank_operation_number=bank_operation_number,
            collected_date_value=collected_date,
            reconciled_by=reconciled_by,
            bank_name=bank_name,
        )
        receipt = event.collection_receipt
        return jsonify(
            {
                "id": event.id,
                "collection_status": event.collection_status,
                "collected_date": (
                    event.collected_date.strftime("%Y-%m-%d")
                    if event.collected_date
                    else None
                ),
                "bank_operation_number": event.bank_operation_number,
                "reconciled_by": event.reconciled_by,
                "collection_receipt": (
                    {
                        "id": receipt.id,
                        "bank_operation_number": receipt.bank_operation_number,
                        "collected_date": receipt.collected_date.strftime("%Y-%m-%d"),
                        "bank_name": receipt.bank_name,
                        "reconciled_by": receipt.reconciled_by,
                    }
                    if receipt
                    else None
                ),
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/cash-flow/balances", methods=["GET"])
def get_cash_flow_balances(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    balances = business.cash_subaccount_balances.order_by(
        "location", "subaccount_code"
    ).all()
    return jsonify(
        [
            {
                "id": balance.id,
                "regime": balance.regime,
                "location": balance.location,
                "subaccount_code": balance.subaccount_code,
                "subaccount_name": balance.subaccount_name,
                "current_balance": float(balance.current_balance or 0),
                "currency": balance.currency,
            }
            for balance in balances
        ]
    )


@bp.route("/cash-flow/funds/config", methods=["GET"])
def get_cash_fund_configurations(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        rows = cash_flow_service.list_fund_configurations(business_id=business.id)
        return jsonify(rows)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/cash-flow/funds/config", methods=["POST"])
def upsert_cash_fund_configuration(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    payload = request.get_json(silent=True) or {}
    subaccount_code = payload.get(
        "subaccount_code", request.form.get("subaccount_code")
    )
    is_active = payload.get("is_active")
    threshold_max_per_operation = payload.get(
        "threshold_max_per_operation",
        request.form.get("threshold_max_per_operation"),
    )
    requires_documentation = payload.get("requires_documentation")
    target_balance = payload.get("target_balance", request.form.get("target_balance"))
    display_name = payload.get("display_name", request.form.get("display_name"))

    try:
        data = cash_flow_service.upsert_fund_configuration(
            business_id=business.id,
            subaccount_code=(subaccount_code or "").strip(),
            is_active=(_parse_bool(is_active) if is_active is not None else None),
            threshold_max_per_operation=(
                float(threshold_max_per_operation)
                if threshold_max_per_operation not in (None, "")
                else None
            ),
            requires_documentation=(
                _parse_bool(requires_documentation)
                if requires_documentation is not None
                else None
            ),
            target_balance=(
                float(target_balance) if target_balance not in (None, "") else None
            ),
            display_name=display_name,
            commit=True,
        )
        return jsonify({"status": "ok", "fund": data})
    except ValueError as exc:
        return jsonify({"error": str(exc), "alert": str(exc)}), 400


@bp.route("/cash-flow/funds/custom", methods=["POST"])
def create_custom_cash_fund(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    payload = request.get_json(silent=True) or {}
    subaccount_code = payload.get(
        "subaccount_code", request.form.get("subaccount_code")
    )
    display_name = payload.get("display_name", request.form.get("display_name"))
    location = payload.get("location", request.form.get("location"))
    is_active = payload.get("is_active", True)
    threshold_max_per_operation = payload.get(
        "threshold_max_per_operation",
        request.form.get("threshold_max_per_operation"),
    )
    requires_documentation = payload.get("requires_documentation", False)
    target_balance = payload.get("target_balance", request.form.get("target_balance"))

    try:
        data = cash_flow_service.create_custom_fund(
            business_id=business.id,
            subaccount_code=(subaccount_code or "").strip(),
            display_name=(display_name or "").strip(),
            location=(location or "cash_box").strip(),
            threshold_max_per_operation=(
                float(threshold_max_per_operation)
                if threshold_max_per_operation not in (None, "")
                else None
            ),
            requires_documentation=_parse_bool(requires_documentation),
            target_balance=(
                float(target_balance) if target_balance not in (None, "") else None
            ),
            is_active=_parse_bool(is_active),
            commit=True,
        )
        return jsonify({"status": "ok", "fund": data})
    except ValueError as exc:
        return jsonify({"error": str(exc), "alert": str(exc)}), 400


@bp.route("/cash-flow/transfer", methods=["POST"])
def transfer_cash_flow(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    payload = request.get_json(silent=True) or {}

    source_subaccount_code = payload.get(
        "source_subaccount_code", request.form.get("source_subaccount_code")
    )
    target_subaccount_code = payload.get(
        "target_subaccount_code", request.form.get("target_subaccount_code")
    )
    amount = payload.get("amount", request.form.get("amount"))
    description = payload.get("description", request.form.get("description"))
    occurred_at = payload.get("occurred_at", request.form.get("occurred_at"))
    supporting_document_ref = payload.get(
        "supporting_document_ref", request.form.get("supporting_document_ref")
    )

    try:
        cash_flow_service.transfer_between_subaccounts(
            business_id=business.id,
            source_subaccount_code=(source_subaccount_code or "").strip(),
            target_subaccount_code=(target_subaccount_code or "").strip(),
            amount=float(amount or 0),
            description=description,
            occurred_at_value=occurred_at,
            source_type="manual_transfer",
            source_ref=payload.get("source_ref"),
            supporting_document_ref=supporting_document_ref,
            commit=True,
        )
        return jsonify(
            {
                "status": "ok",
                "message": "Transferencia registrada correctamente.",
            }
        )
    except ValueError as exc:
        return (
            jsonify(
                {
                    "error": str(exc),
                    "alert": str(exc),
                }
            ),
            400,
        )


@bp.route("/cash-flow/card-payment", methods=["POST"])
def register_card_payment(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    payload = request.get_json(silent=True) or {}
    amount = payload.get("amount", request.form.get("amount"))
    description = payload.get("description", request.form.get("description"))
    occurred_at = payload.get("occurred_at", request.form.get("occurred_at"))
    subaccount_code = payload.get(
        "subaccount_code", request.form.get("subaccount_code")
    )

    try:
        cash_flow_service.register_card_payment_outflow(
            business_id=business.id,
            amount=float(amount or 0),
            description=description,
            occurred_at_value=occurred_at,
            source_ref=payload.get("source_ref"),
            subaccount_code=(subaccount_code or "").strip() or None,
            commit=True,
        )
        return jsonify(
            {
                "status": "ok",
                "message": "Pago con tarjeta registrado correctamente.",
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "alert": str(exc)}), 400


@bp.route("/cash-flow/payroll/extract", methods=["POST"])
def extract_payroll_cash_flow(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    payload = request.get_json(silent=True) or {}
    amount = payload.get("amount", request.form.get("amount"))
    description = payload.get("description", request.form.get("description"))
    occurred_at = payload.get("occurred_at", request.form.get("occurred_at"))

    try:
        cash_flow_service.extract_payroll_funds(
            business_id=business.id,
            amount=float(amount or 0),
            description=description,
            occurred_at_value=occurred_at,
            source_ref=payload.get("source_ref"),
            commit=True,
        )
        return jsonify(
            {
                "status": "ok",
                "message": "Extracción para nómina registrada correctamente.",
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "alert": str(exc)}), 400


@bp.route("/cash-flow/payroll/revert", methods=["POST"])
def revert_payroll_cash_flow(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    payload = request.get_json(silent=True) or {}
    amount = payload.get("amount", request.form.get("amount"))
    description = payload.get("description", request.form.get("description"))
    occurred_at = payload.get("occurred_at", request.form.get("occurred_at"))

    try:
        cash_flow_service.revert_unpaid_payroll(
            business_id=business.id,
            amount=float(amount or 0),
            description=description,
            occurred_at_value=occurred_at,
            source_ref=payload.get("source_ref"),
            commit=True,
        )
        return jsonify(
            {
                "status": "ok",
                "message": "Reversión de nómina no cobrada registrada correctamente.",
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "alert": str(exc)}), 400


@bp.route("/cash-flow/change-fund/transfer", methods=["POST"])
def transfer_change_fund_cash_flow(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    payload = request.get_json(silent=True) or {}
    source_subaccount_code = payload.get(
        "source_subaccount_code", request.form.get("source_subaccount_code")
    )
    target_subaccount_code = payload.get(
        "target_subaccount_code", request.form.get("target_subaccount_code")
    )
    amount = payload.get("amount", request.form.get("amount"))
    description = payload.get("description", request.form.get("description"))
    occurred_at = payload.get("occurred_at", request.form.get("occurred_at"))
    denominations = payload.get("denominations") or []
    supporting_document_ref = payload.get(
        "supporting_document_ref", request.form.get("supporting_document_ref")
    )

    try:
        cash_flow_service.transfer_change_fund_with_denominations(
            business_id=business.id,
            source_subaccount_code=(source_subaccount_code or "").strip(),
            target_subaccount_code=(target_subaccount_code or "").strip(),
            amount=float(amount or 0),
            denominations=denominations,
            description=description,
            occurred_at_value=occurred_at,
            source_ref=payload.get("source_ref"),
            supporting_document_ref=supporting_document_ref,
            commit=True,
        )
        return jsonify(
            {
                "status": "ok",
                "message": "Movimiento de fondo para cambios registrado correctamente.",
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc), "alert": str(exc)}), 400


@bp.route("/cash-flow/change-fund/movements", methods=["GET"])
def get_change_fund_movements(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20

    rows = cash_flow_service.get_change_fund_movement_details(
        business_id=business.id,
        limit=limit,
    )
    return jsonify(rows)


@bp.route("/cash-flow/rebuild", methods=["POST"])
def rebuild_cash_flow(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        result = cash_flow_service.rebuild_balances_from_history(
            business_id=business.id,
            commit=True,
        )
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/cash-flow/consistency", methods=["GET"])
def validate_cash_flow_consistency(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        result = cash_flow_service.validate_cash_flow_consistency(
            business_id=business.id,
        )
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/cash-flow/reports/current-balance", methods=["GET"])
def report_cash_current_balance(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    report = cash_flow_service.get_cash_balance_report(business_id=business.id)
    return jsonify(report)


@bp.route("/cash-flow/reports/movements", methods=["GET"])
def report_cash_movements(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        report = cash_flow_service.get_cash_movement_report(
            business_id=business.id,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            subaccount_code=request.args.get("subaccount_code"),
            chronological=False,
            limit=request.args.get("limit", 500),
        )
        return jsonify(report)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/cash-flow/reports/chronological", methods=["GET"])
def report_cash_chronological(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        report = cash_flow_service.get_cash_movement_report(
            business_id=business.id,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            subaccount_code=request.args.get("subaccount_code"),
            chronological=True,
            limit=request.args.get("limit", 500),
        )
        return jsonify(report)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/cash-flow/reports/current-balance/export", methods=["GET"])
def export_cash_current_balance(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
        report = cash_flow_service.get_cash_balance_report(business_id=business.id)

        rows = [
            [
                item.get("subaccount_code"),
                item.get("subaccount_name"),
                item.get("location"),
                item.get("regime"),
                item.get("current_balance"),
                item.get("currency"),
            ]
            for item in report.get("entries", [])
        ]
        totals = report.get("totals", {})
        rows.append([])
        rows.append(["TOTAL_BANK", "", "", "", totals.get("bank"), "CUP"])
        rows.append(["TOTAL_CASH", "", "", "", totals.get("cash"), "CUP"])
        rows.append(["TOTAL_OVERALL", "", "", "", totals.get("overall"), "CUP"])

        excel_file = income_report_service.generate_excel_tabular_report(
            title="Saldos Efectivo",
            headers=[
                "SUBACCOUNT_CODE",
                "SUBACCOUNT_NAME",
                "LOCATION",
                "REGIME",
                "CURRENT_BALANCE",
                "CURRENCY",
            ],
            rows=rows,
        )
        return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"saldos_efectivo_{business.slug}.xlsx",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/cash-flow/reports/movements/export", methods=["GET"])
def export_cash_movements(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
        report = cash_flow_service.get_cash_movement_report(
            business_id=business.id,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            subaccount_code=request.args.get("subaccount_code"),
            chronological=(request.args.get("chronological", "0") == "1"),
            limit=request.args.get("limit", 1000),
        )

        rows = [
            [
                item.get("id"),
                item.get("occurred_at"),
                item.get("movement_kind"),
                item.get("subaccount_code"),
                item.get("origin_subaccount_code"),
                item.get("target_subaccount_code"),
                item.get("amount"),
                item.get("signed_amount"),
                item.get("source_type"),
                item.get("source_ref"),
                item.get("description"),
            ]
            for item in report.get("entries", [])
        ]

        excel_file = income_report_service.generate_excel_tabular_report(
            title="Movimientos Efectivo",
            headers=[
                "ID",
                "OCCURRED_AT",
                "MOVEMENT_KIND",
                "SUBACCOUNT_CODE",
                "ORIGIN_SUBACCOUNT",
                "TARGET_SUBACCOUNT",
                "AMOUNT",
                "SIGNED_AMOUNT",
                "SOURCE_TYPE",
                "SOURCE_REF",
                "DESCRIPTION",
            ],
            rows=rows,
        )
        return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"movimientos_efectivo_{business.slug}.xlsx",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


def _resolve_scoped_business(client_slug, business_slug):
    business, _ = income_service.resolve_business_and_filters(
        client_slug=client_slug,
        business_slug=business_slug,
    )
    return business


def _parse_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "si", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


@bp.route("/reports/financial-ledger", methods=["GET"])
def financial_ledger_report(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        report = income_report_service.get_financial_ledger_report(
            business_id=business.id,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            regime=request.args.get("regime"),
        )
        return jsonify(report)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/reports/fiscal-ledger", methods=["GET"])
def fiscal_ledger_report(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        report = income_report_service.get_fiscal_ledger_report(
            business_id=business.id,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            regime=request.args.get("regime"),
        )
        return jsonify(report)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/reports/pending-aging", methods=["GET"])
def pending_aging_report(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        report = income_report_service.get_pending_aging_report(
            business_id=business.id,
            as_of_date=request.args.get("as_of_date"),
            regime=request.args.get("regime"),
        )
        return jsonify(report)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/reports/regime-compliance", methods=["GET"])
def regime_compliance_report(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
    except ValueError:
        return jsonify({"error": "Negocio no encontrado"}), 404

    try:
        report = income_report_service.get_regime_compliance_report(
            business_id=business.id,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            regime=request.args.get("regime"),
        )
        return jsonify(report)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/reports/financial-ledger/export", methods=["GET"])
def export_financial_ledger_report(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
        report = income_report_service.get_financial_ledger_report(
            business_id=business.id,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            regime=request.args.get("regime"),
        )
        rows = [
            [
                item.get("id"),
                item.get("income_event_id"),
                item.get("recognition_date"),
                item.get("regime"),
                item.get("amount"),
                item.get("source_ref"),
            ]
            for item in report.get("entries", [])
        ]
        excel_file = income_report_service.generate_excel_tabular_report(
            title="Libro Financiero",
            headers=[
                "ID",
                "INCOME_EVENT_ID",
                "FECHA_RECONOCIMIENTO",
                "REGIMEN",
                "IMPORTE",
                "SOURCE_REF",
            ],
            rows=rows,
        )
        return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"libro_financiero_{business.slug}.xlsx",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/reports/fiscal-ledger/export", methods=["GET"])
def export_fiscal_ledger_report(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
        report = income_report_service.get_fiscal_ledger_report(
            business_id=business.id,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            regime=request.args.get("regime"),
        )
        rows = [
            [
                item.get("id"),
                item.get("income_event_id"),
                item.get("recognition_date"),
                item.get("regime"),
                item.get("amount"),
                item.get("source_ref"),
            ]
            for item in report.get("entries", [])
        ]
        excel_file = income_report_service.generate_excel_tabular_report(
            title="Libro Fiscal",
            headers=[
                "ID",
                "INCOME_EVENT_ID",
                "FECHA_RECONOCIMIENTO",
                "REGIMEN",
                "IMPORTE",
                "SOURCE_REF",
            ],
            rows=rows,
        )
        return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"libro_fiscal_{business.slug}.xlsx",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/reports/pending-aging/export", methods=["GET"])
def export_pending_aging_report(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
        report = income_report_service.get_pending_aging_report(
            business_id=business.id,
            as_of_date=request.args.get("as_of_date"),
            regime=request.args.get("regime"),
        )
        rows = [
            [
                item.get("income_event_id"),
                item.get("event_date"),
                item.get("days_pending"),
                item.get("aging_bucket"),
                item.get("amount"),
                item.get("payment_channel"),
            ]
            for item in report.get("entries", [])
        ]
        excel_file = income_report_service.generate_excel_tabular_report(
            title="Pendientes Aging",
            headers=[
                "INCOME_EVENT_ID",
                "FECHA_EVENTO",
                "DIAS_PENDIENTE",
                "BUCKET",
                "IMPORTE",
                "CANAL_PAGO",
            ],
            rows=rows,
        )
        return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"pendientes_aging_{business.slug}.xlsx",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/reports/regime-compliance/export", methods=["GET"])
def export_regime_compliance_report(client_slug, business_slug):
    try:
        business = _resolve_scoped_business(client_slug, business_slug)
        report = income_report_service.get_regime_compliance_report(
            business_id=business.id,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            regime=request.args.get("regime"),
        )
        totals = report.get("totals", {})
        period = report.get("period", {})
        rows = [
            [
                report.get("business_id"),
                report.get("client_id"),
                report.get("applicable_regime"),
                period.get("start_date"),
                period.get("end_date"),
                totals.get("financial_amount"),
                totals.get("fiscal_amount"),
                totals.get("pending_amount"),
                totals.get("applicable_book_amount"),
            ]
        ]
        excel_file = income_report_service.generate_excel_tabular_report(
            title="Cumplimiento Regimen",
            headers=[
                "BUSINESS_ID",
                "CLIENT_ID",
                "REGIMEN_APLICABLE",
                "START_DATE",
                "END_DATE",
                "TOTAL_FINANCIERO",
                "TOTAL_FISCAL",
                "TOTAL_PENDIENTE",
                "TOTAL_LIBRO_APLICABLE",
            ],
            rows=rows,
        )
        return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"cumplimiento_regimen_{business.slug}.xlsx",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
