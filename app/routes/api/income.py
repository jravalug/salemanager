from flask import Blueprint, jsonify, request, send_file

from app.services import IncomeService, IncomeReportService

bp = Blueprint("api_income", __name__)

income_service = IncomeService()
income_report_service = IncomeReportService()


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


def _resolve_scoped_business(client_slug, business_slug):
    business, _ = income_service.resolve_business_and_filters(
        client_slug=client_slug,
        business_slug=business_slug,
    )
    return business


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
