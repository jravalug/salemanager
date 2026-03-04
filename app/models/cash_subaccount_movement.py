from app.extensions import db


class CashSubaccountMovement(db.Model):
    __tablename__ = "cash_subaccount_movement"

    REGIME_FISCAL = "fiscal"
    REGIME_FINANCIAL = "financiera"

    LOCATION_CASH = "cash_box"
    LOCATION_BANK = "bank_account"

    KIND_INFLOW = "inflow"
    KIND_OUTFLOW = "outflow"
    KIND_TRANSFER_IN = "transfer_in"
    KIND_TRANSFER_OUT = "transfer_out"

    CURRENCY_CUP = "CUP"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(
        db.Integer,
        db.ForeignKey("business.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    balance_id = db.Column(
        db.Integer,
        db.ForeignKey("cash_subaccount_balance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    regime = db.Column(db.String(20), nullable=False, index=True)
    location = db.Column(db.String(20), nullable=False, index=True)
    subaccount_code = db.Column(db.String(50), nullable=False, index=True)
    movement_kind = db.Column(db.String(20), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(3), nullable=False, default=CURRENCY_CUP)
    occurred_at = db.Column(db.DateTime, nullable=False, index=True)
    source_type = db.Column(db.String(30), nullable=True, index=True)
    source_ref = db.Column(db.String(120), nullable=True, index=True)
    counterparty_subaccount_code = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        nullable=False,
    )

    business = db.relationship("Business")
    balance = db.relationship("CashSubaccountBalance")

    __table_args__ = (
        db.CheckConstraint(
            "regime IN ('fiscal', 'financiera')",
            name="cash_subaccount_movement_regime_allowed_values",
        ),
        db.CheckConstraint(
            "location IN ('cash_box', 'bank_account')",
            name="cash_subaccount_movement_location_allowed_values",
        ),
        db.CheckConstraint(
            "movement_kind IN ('inflow', 'outflow', 'transfer_in', 'transfer_out')",
            name="cash_subaccount_movement_kind_allowed_values",
        ),
        db.CheckConstraint(
            "amount > 0",
            name="cash_subaccount_movement_amount_positive",
        ),
        db.CheckConstraint(
            "currency = 'CUP'",
            name="cash_subaccount_movement_currency_cup_only",
        ),
    )

    def __repr__(self):
        return (
            f"<CashSubaccountMovement business_id={self.business_id} "
            f"subaccount={self.subaccount_code} kind={self.movement_kind} "
            f"amount={self.amount}>"
        )
