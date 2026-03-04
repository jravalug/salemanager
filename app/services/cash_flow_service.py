from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import func

from app import db
from app.models import (
    Business,
    Client,
    IncomeEvent,
    CashSubaccountBalance,
    CashSubaccountMovement,
    CashChangeDenomination,
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
    def _parse_occurred_at(occurred_at_value=None) -> datetime:
        if not occurred_at_value:
            return datetime.utcnow()

        if isinstance(occurred_at_value, datetime):
            return occurred_at_value

        if isinstance(occurred_at_value, date):
            return datetime.combine(occurred_at_value, datetime.min.time())

        try:
            return datetime.fromisoformat(str(occurred_at_value))
        except ValueError:
            raise ValueError(
                "La fecha/hora del movimiento no es válida. Usa formato ISO."
            )

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

    def _register_outflow(
        self,
        balance: CashSubaccountBalance,
        amount: float,
        occurred_at: datetime,
        source_type: str,
        source_ref: str,
        description: str,
        movement_kind: str = CashSubaccountMovement.KIND_TRANSFER_OUT,
        counterparty_subaccount_code: str | None = None,
        denominations: list[dict] | None = None,
    ) -> bool:
        if amount <= 0:
            return False

        if self._movement_exists(
            source_ref=source_ref,
            subaccount_code=balance.subaccount_code,
            movement_kind=movement_kind,
        ):
            return False

        current_balance = float(balance.current_balance or 0)
        if current_balance < float(amount):
            raise ValueError("No hay fondo suficiente para la operación.")

        balance.current_balance = current_balance - float(amount)

        movement = CashSubaccountMovement(
            business_id=balance.business_id,
            balance_id=balance.id,
            regime=balance.regime,
            location=balance.location,
            subaccount_code=balance.subaccount_code,
            movement_kind=movement_kind,
            amount=float(amount),
            currency=CashSubaccountMovement.CURRENCY_CUP,
            occurred_at=occurred_at,
            source_type=source_type,
            source_ref=source_ref,
            counterparty_subaccount_code=counterparty_subaccount_code,
            description=description,
        )
        db.session.add(movement)
        self._attach_change_denominations(movement, denominations)
        return True

    def _register_transfer_in(
        self,
        balance: CashSubaccountBalance,
        amount: float,
        occurred_at: datetime,
        source_type: str,
        source_ref: str,
        description: str,
        counterparty_subaccount_code: str | None = None,
        denominations: list[dict] | None = None,
    ) -> bool:
        if amount <= 0:
            return False

        if self._movement_exists(
            source_ref=source_ref,
            subaccount_code=balance.subaccount_code,
            movement_kind=CashSubaccountMovement.KIND_TRANSFER_IN,
        ):
            return False

        balance.current_balance = float(balance.current_balance or 0) + float(amount)

        movement = CashSubaccountMovement(
            business_id=balance.business_id,
            balance_id=balance.id,
            regime=balance.regime,
            location=balance.location,
            subaccount_code=balance.subaccount_code,
            movement_kind=CashSubaccountMovement.KIND_TRANSFER_IN,
            amount=float(amount),
            currency=CashSubaccountMovement.CURRENCY_CUP,
            occurred_at=occurred_at,
            source_type=source_type,
            source_ref=source_ref,
            counterparty_subaccount_code=counterparty_subaccount_code,
            description=description,
        )
        db.session.add(movement)
        self._attach_change_denominations(movement, denominations)
        return True

    @staticmethod
    def _normalize_change_denominations(
        denominations: list[dict] | None,
    ) -> tuple[list[dict], float]:
        if not denominations:
            return [], 0.0

        normalized = []
        total = 0.0

        for item in denominations:
            if not isinstance(item, dict):
                raise ValueError("Formato de denominaciones no válido.")

            raw_value = item.get("denomination", item.get("denomination_value"))
            raw_count = item.get("quantity", item.get("unit_count"))

            denomination_value = float(raw_value or 0)
            unit_count = int(raw_count or 0)

            if denomination_value <= 0 or unit_count <= 0:
                raise ValueError(
                    "Cada denominación debe tener valor y cantidad mayores que cero."
                )

            line_total = round(denomination_value * unit_count, 2)
            total = round(total + line_total, 2)
            normalized.append(
                {
                    "denomination_value": denomination_value,
                    "unit_count": unit_count,
                    "total_amount": line_total,
                }
            )

        return normalized, total

    @staticmethod
    def _attach_change_denominations(
        movement: CashSubaccountMovement,
        denominations: list[dict] | None,
    ) -> None:
        if not denominations:
            return

        for item in denominations:
            db.session.add(
                CashChangeDenomination(
                    movement=movement,
                    denomination_value=float(item["denomination_value"]),
                    unit_count=int(item["unit_count"]),
                    total_amount=float(item["total_amount"]),
                )
            )

    @staticmethod
    def _validate_financial_transfer_rules(source_code: str, target_code: str) -> None:
        allowed_from_bank = {
            CashFlowService.SUBACCOUNT_FIN_CARD,
            CashFlowService.SUBACCOUNT_FIN_PAYROLL,
            CashFlowService.SUBACCOUNT_FIN_CHANGES,
            CashFlowService.SUBACCOUNT_FIN_MINOR,
            CashFlowService.SUBACCOUNT_FIN_PURCHASES,
            CashFlowService.SUBACCOUNT_FIN_TO_DEPOSIT,
        }
        allowed_from_to_deposit = allowed_from_bank | {CashFlowService.SUBACCOUNT_BANK}

        if (
            source_code == CashFlowService.SUBACCOUNT_BANK
            and target_code in allowed_from_bank
        ):
            return

        if (
            source_code == CashFlowService.SUBACCOUNT_FIN_TO_DEPOSIT
            and target_code in allowed_from_to_deposit
        ):
            return

        if (
            source_code == CashFlowService.SUBACCOUNT_FIN_PAYROLL
            and target_code == CashFlowService.SUBACCOUNT_BANK
        ):
            return

        raise ValueError(
            "Transferencia no permitida por reglas financieras del negocio."
        )

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

    def transfer_between_subaccounts(
        self,
        business_id: int,
        source_subaccount_code: str,
        target_subaccount_code: str,
        amount: float,
        description: str | None = None,
        source_type: str = "manual_transfer",
        source_ref: str | None = None,
        occurred_at_value=None,
        denominations: list[dict] | None = None,
        commit: bool = True,
    ) -> bool:
        if source_subaccount_code == target_subaccount_code:
            raise ValueError("Origen y destino no pueden ser iguales.")

        amount_value = float(amount or 0)
        if amount_value <= 0:
            raise ValueError("El monto de la transferencia debe ser mayor que cero.")

        source_balance = CashSubaccountBalance.query.filter_by(
            business_id=business_id,
            subaccount_code=source_subaccount_code,
        ).first()
        target_balance = CashSubaccountBalance.query.filter_by(
            business_id=business_id,
            subaccount_code=target_subaccount_code,
        ).first()

        if not source_balance or not target_balance:
            raise ValueError("Sub-saldo origen o destino no encontrado.")

        if source_balance.regime != target_balance.regime:
            raise ValueError("No se puede transferir entre regímenes distintos.")

        if source_balance.regime == Client.REGIME_FINANCIAL:
            self._validate_financial_transfer_rules(
                source_code=source_subaccount_code,
                target_code=target_subaccount_code,
            )

        occurred_at = self._parse_occurred_at(occurred_at_value)
        normalized_denominations, denom_total = self._normalize_change_denominations(
            denominations
        )
        if normalized_denominations and round(denom_total, 2) != round(amount_value, 2):
            raise ValueError(
                "La suma de denominaciones debe coincidir con el monto del movimiento."
            )

        transfer_ref = (
            source_ref
            or f"transfer:{business_id}:{source_subaccount_code}:{target_subaccount_code}:{occurred_at.isoformat()}:{amount_value}"
        )

        denominations_out = (
            normalized_denominations
            if source_subaccount_code == self.SUBACCOUNT_FIN_CHANGES
            else None
        )
        denominations_in = (
            normalized_denominations
            if target_subaccount_code == self.SUBACCOUNT_FIN_CHANGES
            else None
        )

        self._register_outflow(
            balance=source_balance,
            amount=amount_value,
            occurred_at=occurred_at,
            source_type=source_type,
            source_ref=transfer_ref,
            description=(description or "Transferencia interna").strip(),
            counterparty_subaccount_code=target_subaccount_code,
            denominations=denominations_out,
        )
        self._register_transfer_in(
            balance=target_balance,
            amount=amount_value,
            occurred_at=occurred_at,
            source_type=source_type,
            source_ref=transfer_ref,
            description=(description or "Transferencia interna").strip(),
            counterparty_subaccount_code=source_subaccount_code,
            denominations=denominations_in,
        )

        if commit:
            db.session.commit()

        return True

    def transfer_change_fund_with_denominations(
        self,
        business_id: int,
        source_subaccount_code: str,
        target_subaccount_code: str,
        amount: float,
        denominations: list[dict],
        description: str | None = None,
        source_ref: str | None = None,
        occurred_at_value=None,
        commit: bool = True,
    ) -> bool:
        if self.SUBACCOUNT_FIN_CHANGES not in {
            source_subaccount_code,
            target_subaccount_code,
        }:
            raise ValueError(
                "La operación de denominaciones aplica solo a movimientos del fondo para cambios."
            )

        return self.transfer_between_subaccounts(
            business_id=business_id,
            source_subaccount_code=source_subaccount_code,
            target_subaccount_code=target_subaccount_code,
            amount=amount,
            description=(description or "Movimiento de fondo para cambios"),
            source_type="change_fund_transfer",
            source_ref=source_ref,
            occurred_at_value=occurred_at_value,
            denominations=denominations,
            commit=commit,
        )

    def get_change_fund_movement_details(
        self,
        business_id: int,
        limit: int = 20,
    ) -> list[dict]:
        rows = (
            CashSubaccountMovement.query.filter_by(
                business_id=business_id,
                subaccount_code=self.SUBACCOUNT_FIN_CHANGES,
            )
            .order_by(
                CashSubaccountMovement.occurred_at.desc(),
                CashSubaccountMovement.id.desc(),
            )
            .limit(max(int(limit or 20), 1))
            .all()
        )

        result = []
        for movement in rows:
            result.append(
                {
                    "id": movement.id,
                    "movement_kind": movement.movement_kind,
                    "amount": float(movement.amount or 0),
                    "occurred_at": (
                        movement.occurred_at.isoformat()
                        if movement.occurred_at
                        else None
                    ),
                    "source_type": movement.source_type,
                    "source_ref": movement.source_ref,
                    "counterparty_subaccount_code": movement.counterparty_subaccount_code,
                    "description": movement.description,
                    "denominations": [
                        {
                            "denomination_value": float(item.denomination_value or 0),
                            "unit_count": int(item.unit_count or 0),
                            "total_amount": float(item.total_amount or 0),
                        }
                        for item in movement.change_denominations
                    ],
                }
            )

        return result

    def register_card_payment_outflow(
        self,
        business_id: int,
        amount: float,
        description: str | None = None,
        source_type: str = "card_payment",
        source_ref: str | None = None,
        occurred_at_value=None,
        subaccount_code: str | None = None,
        commit: bool = True,
    ) -> bool:
        amount_value = float(amount or 0)
        if amount_value <= 0:
            raise ValueError("El monto del pago debe ser mayor que cero.")

        business_balances = CashSubaccountBalance.query.filter_by(
            business_id=business_id
        ).all()
        if not business_balances:
            raise ValueError("No hay sub-saldos configurados para el negocio.")

        source_balance = None
        if subaccount_code:
            source_balance = CashSubaccountBalance.query.filter_by(
                business_id=business_id,
                subaccount_code=subaccount_code,
            ).first()
        else:
            source_balance = (
                CashSubaccountBalance.query.filter_by(
                    business_id=business_id,
                    subaccount_code=self.SUBACCOUNT_FIN_CARD,
                ).first()
                or CashSubaccountBalance.query.filter_by(
                    business_id=business_id,
                    subaccount_code=self.SUBACCOUNT_FISCAL_CARD,
                ).first()
            )

        if not source_balance:
            raise ValueError("Sub-saldo de tarjeta no encontrado.")

        if source_balance.subaccount_code not in {
            self.SUBACCOUNT_FIN_CARD,
            self.SUBACCOUNT_FISCAL_CARD,
        }:
            raise ValueError("El pago solo se permite desde una sub-cuenta de tarjeta.")

        occurred_at = self._parse_occurred_at(occurred_at_value)
        payment_ref = (
            source_ref
            or f"card_payment:{business_id}:{source_balance.subaccount_code}:{occurred_at.isoformat()}:{amount_value}"
        )

        self._register_outflow(
            balance=source_balance,
            amount=amount_value,
            occurred_at=occurred_at,
            source_type=source_type,
            source_ref=payment_ref,
            description=(description or "Pago desde tarjeta").strip(),
            movement_kind=CashSubaccountMovement.KIND_OUTFLOW,
            counterparty_subaccount_code=None,
        )

        if commit:
            db.session.commit()

        return True

    def extract_payroll_funds(
        self,
        business_id: int,
        amount: float,
        description: str | None = None,
        source_ref: str | None = None,
        occurred_at_value=None,
        commit: bool = True,
    ) -> bool:
        return self.transfer_between_subaccounts(
            business_id=business_id,
            source_subaccount_code=self.SUBACCOUNT_BANK,
            target_subaccount_code=self.SUBACCOUNT_FIN_PAYROLL,
            amount=amount,
            description=(description or "Extracción para nómina"),
            source_type="payroll_extract",
            source_ref=source_ref,
            occurred_at_value=occurred_at_value,
            commit=commit,
        )

    def revert_unpaid_payroll(
        self,
        business_id: int,
        amount: float,
        description: str | None = None,
        source_ref: str | None = None,
        occurred_at_value=None,
        commit: bool = True,
    ) -> bool:
        return self.transfer_between_subaccounts(
            business_id=business_id,
            source_subaccount_code=self.SUBACCOUNT_FIN_PAYROLL,
            target_subaccount_code=self.SUBACCOUNT_BANK,
            amount=amount,
            description=(description or "Reversión nómina no cobrada"),
            source_type="payroll_revert",
            source_ref=source_ref,
            occurred_at_value=occurred_at_value,
            commit=commit,
        )

    @staticmethod
    def _movement_sign(kind: str) -> int:
        if kind in {
            CashSubaccountMovement.KIND_INFLOW,
            CashSubaccountMovement.KIND_TRANSFER_IN,
        }:
            return 1
        if kind in {
            CashSubaccountMovement.KIND_OUTFLOW,
            CashSubaccountMovement.KIND_TRANSFER_OUT,
        }:
            return -1
        return 0

    def _calculate_expected_balances(self, business_id: int) -> dict[str, float]:
        expected = {}
        rows = (
            db.session.query(
                CashSubaccountMovement.subaccount_code,
                CashSubaccountMovement.movement_kind,
                func.coalesce(func.sum(CashSubaccountMovement.amount), 0.0),
            )
            .filter(CashSubaccountMovement.business_id == business_id)
            .group_by(
                CashSubaccountMovement.subaccount_code,
                CashSubaccountMovement.movement_kind,
            )
            .all()
        )
        for subaccount_code, movement_kind, total_amount in rows:
            sign = self._movement_sign(movement_kind)
            expected[subaccount_code] = round(
                float(expected.get(subaccount_code, 0.0))
                + (float(total_amount or 0.0) * sign),
                2,
            )
        return expected

    @staticmethod
    def _resolve_report_datetime(
        value, field_name: str, end_of_day: bool
    ) -> datetime | None:
        if not value:
            return None

        raw = str(value).strip()
        try:
            if "T" in raw:
                return datetime.fromisoformat(raw)
            parsed_date = datetime.strptime(raw, "%Y-%m-%d").date()
            if end_of_day:
                return datetime.combine(parsed_date, datetime.max.time())
            return datetime.combine(parsed_date, datetime.min.time())
        except ValueError:
            raise ValueError(
                f"{field_name} no tiene un formato válido. Usa YYYY-MM-DD o ISO datetime."
            )

    def rebuild_balances_from_history(
        self, business_id: int, commit: bool = True
    ) -> dict:
        business = Business.query.get(business_id)
        if not business:
            raise ValueError("Negocio no encontrado")

        regime = (business.client.accounting_regime or "").strip().lower()
        if regime in {Client.REGIME_FISCAL, Client.REGIME_FINANCIAL}:
            self.ensure_default_subaccounts(business_id=business_id, regime=regime)

        balances = (
            CashSubaccountBalance.query.filter_by(business_id=business_id)
            .order_by(CashSubaccountBalance.subaccount_code.asc())
            .all()
        )
        expected = self._calculate_expected_balances(business_id)

        updates = []
        for balance in balances:
            expected_value = round(float(expected.get(balance.subaccount_code, 0.0)), 2)
            if expected_value < 0:
                raise ValueError(
                    f"El recálculo arroja saldo negativo para '{balance.subaccount_code}'."
                )

            current_value = round(float(balance.current_balance or 0.0), 2)
            if current_value != expected_value:
                updates.append(
                    {
                        "subaccount_code": balance.subaccount_code,
                        "previous_balance": current_value,
                        "new_balance": expected_value,
                    }
                )
                balance.current_balance = expected_value

        if commit:
            db.session.commit()

        return {
            "business_id": business_id,
            "updated_count": len(updates),
            "updates": updates,
        }

    def validate_cash_flow_consistency(self, business_id: int) -> dict:
        business = Business.query.get(business_id)
        if not business:
            raise ValueError("Negocio no encontrado")

        expected = self._calculate_expected_balances(business_id)
        balances = (
            CashSubaccountBalance.query.filter_by(business_id=business_id)
            .order_by(CashSubaccountBalance.subaccount_code.asc())
            .all()
        )

        balance_mismatches = []
        for balance in balances:
            expected_value = round(float(expected.get(balance.subaccount_code, 0.0)), 2)
            current_value = round(float(balance.current_balance or 0.0), 2)
            if current_value != expected_value:
                balance_mismatches.append(
                    {
                        "subaccount_code": balance.subaccount_code,
                        "current_balance": current_value,
                        "expected_balance": expected_value,
                    }
                )

        regime = (business.client.accounting_regime or "").strip().lower()
        expected_income_refs = []
        income_events = (
            IncomeEvent.query.filter_by(business_id=business_id)
            .order_by(IncomeEvent.event_date.asc(), IncomeEvent.id.asc())
            .all()
        )
        for event in income_events:
            if event.payment_channel == IncomeEvent.CHANNEL_CASH:
                target_code = (
                    self.SUBACCOUNT_FIN_TO_DEPOSIT
                    if regime == Client.REGIME_FINANCIAL
                    else self.SUBACCOUNT_FISCAL_CASH
                )
                expected_income_refs.append(
                    {
                        "income_event_id": event.id,
                        "subaccount_code": target_code,
                        "movement_kind": CashSubaccountMovement.KIND_INFLOW,
                        "source_ref": f"income_event:{event.id}:cash_inflow",
                    }
                )

            if (
                event.payment_channel == IncomeEvent.CHANNEL_BANK_TRANSFER
                and event.collection_status
                in {IncomeEvent.STATUS_COLLECTED, IncomeEvent.STATUS_IMMEDIATE}
            ):
                expected_income_refs.append(
                    {
                        "income_event_id": event.id,
                        "subaccount_code": self.SUBACCOUNT_BANK,
                        "movement_kind": CashSubaccountMovement.KIND_INFLOW,
                        "source_ref": f"income_event:{event.id}:bank_inflow",
                    }
                )

        missing_income_movements = []
        for expected_ref in expected_income_refs:
            exists = (
                CashSubaccountMovement.query.filter_by(
                    business_id=business_id,
                    subaccount_code=expected_ref["subaccount_code"],
                    movement_kind=expected_ref["movement_kind"],
                    source_ref=expected_ref["source_ref"],
                ).first()
                is not None
            )
            if not exists:
                missing_income_movements.append(expected_ref)

        return {
            "business_id": business_id,
            "is_consistent": (not balance_mismatches)
            and (not missing_income_movements),
            "balance_mismatches": balance_mismatches,
            "missing_income_movements": missing_income_movements,
            "totals": {
                "balance_mismatches": len(balance_mismatches),
                "missing_income_movements": len(missing_income_movements),
            },
        }

    def get_cash_balance_report(self, business_id: int) -> dict:
        balances = (
            CashSubaccountBalance.query.filter_by(business_id=business_id)
            .order_by(
                CashSubaccountBalance.location.asc(),
                CashSubaccountBalance.subaccount_code.asc(),
            )
            .all()
        )

        entries = []
        total_bank = 0.0
        total_cash = 0.0
        for balance in balances:
            amount = round(float(balance.current_balance or 0.0), 2)
            entries.append(
                {
                    "subaccount_code": balance.subaccount_code,
                    "subaccount_name": balance.subaccount_name,
                    "location": balance.location,
                    "regime": balance.regime,
                    "current_balance": amount,
                    "currency": balance.currency,
                }
            )
            if balance.location == CashSubaccountBalance.LOCATION_BANK:
                total_bank += amount
            else:
                total_cash += amount

        return {
            "business_id": business_id,
            "entries": entries,
            "totals": {
                "bank": round(total_bank, 2),
                "cash": round(total_cash, 2),
                "overall": round(total_bank + total_cash, 2),
            },
        }

    def get_cash_movement_report(
        self,
        business_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
        subaccount_code: str | None = None,
        chronological: bool = False,
        limit: int = 500,
    ) -> dict:
        start_dt = self._resolve_report_datetime(start_date, "start_date", False)
        end_dt = self._resolve_report_datetime(end_date, "end_date", True)

        if start_dt and end_dt and start_dt > end_dt:
            raise ValueError("start_date no puede ser mayor que end_date.")

        query = CashSubaccountMovement.query.filter_by(business_id=business_id)
        if subaccount_code:
            query = query.filter(
                CashSubaccountMovement.subaccount_code == subaccount_code.strip()
            )
        if start_dt:
            query = query.filter(CashSubaccountMovement.occurred_at >= start_dt)
        if end_dt:
            query = query.filter(CashSubaccountMovement.occurred_at <= end_dt)

        if chronological:
            query = query.order_by(
                CashSubaccountMovement.occurred_at.asc(),
                CashSubaccountMovement.id.asc(),
            )
        else:
            query = query.order_by(
                CashSubaccountMovement.occurred_at.desc(),
                CashSubaccountMovement.id.desc(),
            )

        movements = query.limit(max(int(limit or 500), 1)).all()

        inflows = 0.0
        outflows = 0.0
        entries = []
        for movement in movements:
            amount = round(float(movement.amount or 0.0), 2)
            sign = self._movement_sign(movement.movement_kind)
            signed_amount = round(amount * sign, 2)

            if sign >= 0:
                inflows += amount
            else:
                outflows += amount

            if movement.movement_kind in {
                CashSubaccountMovement.KIND_INFLOW,
                CashSubaccountMovement.KIND_TRANSFER_IN,
            }:
                origin_subaccount = movement.counterparty_subaccount_code
                target_subaccount = movement.subaccount_code
            else:
                origin_subaccount = movement.subaccount_code
                target_subaccount = movement.counterparty_subaccount_code

            entries.append(
                {
                    "id": movement.id,
                    "occurred_at": (
                        movement.occurred_at.isoformat()
                        if movement.occurred_at
                        else None
                    ),
                    "subaccount_code": movement.subaccount_code,
                    "movement_kind": movement.movement_kind,
                    "amount": amount,
                    "signed_amount": signed_amount,
                    "origin_subaccount_code": origin_subaccount,
                    "target_subaccount_code": target_subaccount,
                    "source_type": movement.source_type,
                    "source_ref": movement.source_ref,
                    "description": movement.description,
                }
            )

        return {
            "business_id": business_id,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "subaccount_code": subaccount_code,
                "chronological": chronological,
                "limit": max(int(limit or 500), 1),
            },
            "entries": entries,
            "totals": {
                "count": len(entries),
                "inflows": round(inflows, 2),
                "outflows": round(outflows, 2),
                "net": round(inflows - outflows, 2),
            },
        }
