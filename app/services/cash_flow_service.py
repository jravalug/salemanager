from __future__ import annotations

from datetime import datetime, date

from app import db
from app.models import (
    Client,
    IncomeEvent,
    CashSubaccountBalance,
    CashSubaccountMovement,
)


class CashFlowService:
    """Gestiona saldos y movimientos de efectivo por sub-cuenta."""

    SUBACCOUNT_BANK = "bank"
    SUBACCOUNT_FISCAL_CASH = "cash_physical"
    SUBACCOUNT_FISCAL_CARD = "cash_magnetic_card"

    SUBACCOUNT_FIN_CARD = "magnetic_card"
    SUBACCOUNT_FIN_PAYROLL = "payroll_extracted"
    SUBACCOUNT_FIN_CHANGES = "change_fund"
    SUBACCOUNT_FIN_MINOR = "minor_payments_fund"
    SUBACCOUNT_FIN_PURCHASES = "purchases_fund"
    SUBACCOUNT_FIN_TO_DEPOSIT = "cash_to_deposit"

    DEFAULT_SUBACCOUNTS = {
        Client.REGIME_FISCAL: [
            (
                SUBACCOUNT_FISCAL_CASH,
                "Caja física",
                CashSubaccountBalance.LOCATION_CASH,
            ),
            (
                SUBACCOUNT_FISCAL_CARD,
                "Caja tarjeta magnética",
                CashSubaccountBalance.LOCATION_CASH,
            ),
            (
                SUBACCOUNT_BANK,
                "Banco",
                CashSubaccountBalance.LOCATION_BANK,
            ),
        ],
        Client.REGIME_FINANCIAL: [
            (
                SUBACCOUNT_FIN_CARD,
                "Tarjeta magnética",
                CashSubaccountBalance.LOCATION_CASH,
            ),
            (
                SUBACCOUNT_FIN_PAYROLL,
                "Extraído para nómina",
                CashSubaccountBalance.LOCATION_CASH,
            ),
            (
                SUBACCOUNT_FIN_CHANGES,
                "Fondo para cambios",
                CashSubaccountBalance.LOCATION_CASH,
            ),
            (
                SUBACCOUNT_FIN_MINOR,
                "Fondo para pagos menores",
                CashSubaccountBalance.LOCATION_CASH,
            ),
            (
                SUBACCOUNT_FIN_PURCHASES,
                "Fondo para compras",
                CashSubaccountBalance.LOCATION_CASH,
            ),
            (
                SUBACCOUNT_FIN_TO_DEPOSIT,
                "Efectivo por depositar",
                CashSubaccountBalance.LOCATION_CASH,
            ),
            (
                SUBACCOUNT_BANK,
                "Banco",
                CashSubaccountBalance.LOCATION_BANK,
            ),
        ],
    }

    @staticmethod
    def _resolve_event_datetime(income_event: IncomeEvent) -> datetime:
        event_date = income_event.collected_date or income_event.event_date
        if isinstance(event_date, date):
            return datetime.combine(event_date, datetime.min.time())
        return datetime.utcnow()

    @staticmethod
    def _resolve_client_regime(income_event: IncomeEvent) -> str | None:
        if not income_event.business or not income_event.business.client:
            return None
        return income_event.business.client.accounting_regime

    def ensure_default_subaccounts(self, business_id: int, regime: str) -> None:
        for code, name, location in self.DEFAULT_SUBACCOUNTS.get(regime, []):
            self._get_or_create_balance(
                business_id=business_id,
                regime=regime,
                subaccount_code=code,
                subaccount_name=name,
                location=location,
            )

    @staticmethod
    def _get_or_create_balance(
        business_id: int,
        regime: str,
        subaccount_code: str,
        subaccount_name: str,
        location: str,
    ) -> CashSubaccountBalance:
        balance = CashSubaccountBalance.query.filter_by(
            business_id=business_id,
            subaccount_code=subaccount_code,
        ).first()
        if balance:
            return balance

        balance = CashSubaccountBalance(
            business_id=business_id,
            regime=regime,
            location=location,
            subaccount_code=subaccount_code,
            subaccount_name=subaccount_name,
            currency=CashSubaccountBalance.CURRENCY_CUP,
            current_balance=0.0,
        )
        db.session.add(balance)
        db.session.flush()
        return balance

    @staticmethod
    def _movement_exists(
        source_ref: str, subaccount_code: str, movement_kind: str
    ) -> bool:
        return (
            CashSubaccountMovement.query.filter_by(
                source_ref=source_ref,
                subaccount_code=subaccount_code,
                movement_kind=movement_kind,
            ).first()
            is not None
        )

    def _register_inflow(
        self,
        balance: CashSubaccountBalance,
        amount: float,
        occurred_at: datetime,
        source_type: str,
        source_ref: str,
        description: str,
    ) -> bool:
        if amount <= 0:
            return False

        if self._movement_exists(
            source_ref=source_ref,
            subaccount_code=balance.subaccount_code,
            movement_kind=CashSubaccountMovement.KIND_INFLOW,
        ):
            return False

        balance.current_balance = float(balance.current_balance or 0) + float(amount)

        movement = CashSubaccountMovement(
            business_id=balance.business_id,
            balance_id=balance.id,
            regime=balance.regime,
            location=balance.location,
            subaccount_code=balance.subaccount_code,
            movement_kind=CashSubaccountMovement.KIND_INFLOW,
            amount=float(amount),
            currency=CashSubaccountMovement.CURRENCY_CUP,
            occurred_at=occurred_at,
            source_type=source_type,
            source_ref=source_ref,
            description=description,
        )
        db.session.add(movement)
        return True

    def record_income_event_inflow(
        self,
        income_event: IncomeEvent,
        commit: bool = False,
    ) -> bool:
        if not income_event:
            return False

        regime = self._resolve_client_regime(income_event)
        if regime not in {Client.REGIME_FISCAL, Client.REGIME_FINANCIAL}:
            return False

        self.ensure_default_subaccounts(income_event.business_id, regime)

        amount = float(income_event.amount or 0)
        occurred_at = self._resolve_event_datetime(income_event)
        movement_created = False

        if income_event.payment_channel == IncomeEvent.CHANNEL_CASH:
            target_code = (
                self.SUBACCOUNT_FIN_TO_DEPOSIT
                if regime == Client.REGIME_FINANCIAL
                else self.SUBACCOUNT_FISCAL_CASH
            )
            balance = CashSubaccountBalance.query.filter_by(
                business_id=income_event.business_id,
                subaccount_code=target_code,
            ).first()
            if balance:
                movement_created = self._register_inflow(
                    balance=balance,
                    amount=amount,
                    occurred_at=occurred_at,
                    source_type="income_event",
                    source_ref=f"income_event:{income_event.id}:cash_inflow",
                    description="Ingreso por efectivo",
                )

        elif income_event.payment_channel == IncomeEvent.CHANNEL_BANK_TRANSFER:
            if income_event.collection_status not in {
                IncomeEvent.STATUS_COLLECTED,
                IncomeEvent.STATUS_IMMEDIATE,
            }:
                return False

            balance = CashSubaccountBalance.query.filter_by(
                business_id=income_event.business_id,
                subaccount_code=self.SUBACCOUNT_BANK,
            ).first()
            if balance:
                movement_created = self._register_inflow(
                    balance=balance,
                    amount=amount,
                    occurred_at=occurred_at,
                    source_type="income_event",
                    source_ref=f"income_event:{income_event.id}:bank_inflow",
                    description="Ingreso conciliado en banco",
                )

        if commit:
            db.session.commit()

        return movement_created
