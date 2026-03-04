from app import create_app
from app.extensions import db
from app.services.cash_flow_service import CashFlowService
from app.models import Business


def rebuild_cash_subaccount_balances():
    app = create_app()
    with app.app_context():
        service = CashFlowService()
        businesses = Business.query.order_by(Business.id.asc()).all()

        print(f"Negocios a procesar: {len(businesses)}")
        total_updates = 0

        for business in businesses:
            try:
                result = service.rebuild_balances_from_history(
                    business_id=business.id,
                    commit=False,
                )
                updates = int(result.get("updated_count", 0))
                total_updates += updates
                print(
                    f"- business_id={business.id} slug={business.slug} updates={updates}"
                )
            except Exception as exc:
                print(f"- business_id={business.id} error={exc}")

        db.session.commit()
        print(f"Total de sub-saldos actualizados: {total_updates}")


if __name__ == "__main__":
    rebuild_cash_subaccount_balances()
