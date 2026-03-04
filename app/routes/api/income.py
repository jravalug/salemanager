from flask import Blueprint, jsonify, request

from app.services import IncomeService

bp = Blueprint("api_income", __name__)

income_service = IncomeService()


@bp.route("/sales", methods=["GET"])
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
