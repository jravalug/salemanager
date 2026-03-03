from datetime import date, datetime
from typing import Dict

from flask import current_app
from sqlalchemy import func

from app.extensions import db
from app.models import Business, Client, Sale


class ClientAccountingService:
    """Gestiona reglas de transición entre contabilidad fiscal y financiera."""

    def evaluate_annual_regime_transition(
        self,
        process_date: date | None = None,
        force: bool = False,
    ) -> Dict[str, int]:
        """
        Evalúa para cada cliente el régimen aplicable según los ingresos brutos
        del año anterior y aplica cambios para el año actual.

        Args:
            process_date: Fecha de proceso. Si no se define, usa la fecha actual.
            force: Si es True, evalúa aunque ya se haya evaluado el año actual.

        Returns:
            Resumen con clientes evaluados y actualizados.
        """
        process_date = process_date or date.today()
        reviewed_year = process_date.year - 1
        target_year = process_date.year

        threshold = float(current_app.config.get("ACCOUNTING_FISCAL_THRESHOLD", 500000))
        allow_reversion = bool(
            current_app.config.get("ACCOUNTING_REGIME_ALLOW_REVERSION", True)
        )

        clients = Client.query.filter_by(is_active=True).all()
        evaluated_count = 0
        updated_count = 0

        try:
            for client in clients:
                if not force and client.last_regime_evaluation_year == target_year:
                    continue

                evaluated_count += 1
                gross_income = self.get_client_gross_income_for_year(client.id, reviewed_year)
                previous_regime = client.accounting_regime

                if gross_income > threshold:
                    new_regime = Client.REGIME_FINANCIAL
                    reason = (
                        f"Ingresos brutos {reviewed_year}: {gross_income:.2f} "
                        f"> umbral {threshold:.2f}"
                    )
                elif allow_reversion:
                    new_regime = Client.REGIME_FISCAL
                    reason = (
                        f"Ingresos brutos {reviewed_year}: {gross_income:.2f} "
                        f"<= umbral {threshold:.2f}"
                    )
                else:
                    new_regime = previous_regime
                    reason = "Reversión deshabilitada por configuración"

                if new_regime != previous_regime:
                    client.accounting_regime = new_regime
                    client.regime_changed_at = datetime.utcnow()
                    client.regime_change_reason = reason
                    updated_count += 1

                client.last_regime_evaluation_year = target_year
                client.last_regime_evaluated_at = datetime.utcnow()

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {
            "reviewed_year": reviewed_year,
            "target_year": target_year,
            "evaluated_clients": evaluated_count,
            "updated_clients": updated_count,
        }

    @staticmethod
    def get_client_gross_income_for_year(client_id: int, year: int) -> float:
        """Calcula ingresos brutos del cliente en un año natural (enero-diciembre)."""
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        total = (
            db.session.query(func.coalesce(func.sum(Sale.total_amount), 0.0))
            .join(Business, Business.id == Sale.business_id)
            .filter(Business.client_id == client_id)
            .filter(Sale.date >= start_date, Sale.date <= end_date)
            .scalar()
        )

        return float(total or 0.0)
