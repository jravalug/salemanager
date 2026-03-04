from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import (
    Client,
    FinancialLedgerEntry,
    FiscalIncomeEntry,
    IncomeEvent,
)


class IncomePostingService:
    """Publica eventos de ingreso en el libro contable aplicable al cliente."""

    @staticmethod
    def _resolve_client_regime(income_event: IncomeEvent) -> str | None:
        if not income_event.business or not income_event.business.client:
            return None
        return income_event.business.client.accounting_regime

    @staticmethod
    def _resolve_fiscal_date(income_event: IncomeEvent):
        if income_event.collection_status == IncomeEvent.STATUS_PENDING:
            return income_event.collected_date
        return income_event.collected_date or income_event.event_date

    @staticmethod
    def _upsert_financial_entry(income_event: IncomeEvent, regime: str):
        entry = FinancialLedgerEntry.query.filter_by(
            income_event_id=income_event.id
        ).first()

        if not entry:
            entry = FinancialLedgerEntry(
                income_event_id=income_event.id,
                business_id=income_event.business_id,
            )
            db.session.add(entry)

        entry.recognition_date = income_event.event_date
        entry.amount = float(income_event.amount or 0)
        entry.regime = regime
        entry.source_ref = income_event.source_ref

    @staticmethod
    def _upsert_fiscal_entry(income_event: IncomeEvent, regime: str):
        recognition_date = IncomePostingService._resolve_fiscal_date(income_event)
        if not recognition_date:
            return

        entry = FiscalIncomeEntry.query.filter_by(
            income_event_id=income_event.id
        ).first()

        if not entry:
            entry = FiscalIncomeEntry(
                income_event_id=income_event.id,
                business_id=income_event.business_id,
            )
            db.session.add(entry)

        entry.recognition_date = recognition_date
        entry.amount = float(income_event.amount or 0)
        entry.regime = regime
        entry.source_ref = income_event.source_ref

    @staticmethod
    def _delete_opposite_entry(income_event: IncomeEvent, regime: str):
        if regime == Client.REGIME_FINANCIAL:
            FiscalIncomeEntry.query.filter_by(income_event_id=income_event.id).delete()
            return

        if regime == Client.REGIME_FISCAL:
            FinancialLedgerEntry.query.filter_by(
                income_event_id=income_event.id
            ).delete()

    def post_event(self, income_event: IncomeEvent, commit: bool = False) -> bool:
        if not income_event:
            return False

        regime = self._resolve_client_regime(income_event)
        if regime not in {Client.REGIME_FISCAL, Client.REGIME_FINANCIAL}:
            return False

        try:
            self._delete_opposite_entry(income_event, regime)

            if regime == Client.REGIME_FINANCIAL:
                self._upsert_financial_entry(income_event, regime)
            else:
                self._upsert_fiscal_entry(income_event, regime)

            if commit:
                db.session.commit()

            return True
        except SQLAlchemyError:
            if commit:
                db.session.rollback()
            raise
