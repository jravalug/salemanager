from app.extensions import db


class CashSubaccountBalance(db.Model):
    __tablename__ = "cash_subaccount_balance"

    REGIME_FISCAL = "fiscal"
    REGIME_FINANCIAL = "financiera"

    LOCATION_CASH = "cash_box"
    LOCATION_BANK = "bank_account"

    CURRENCY_CUP = "CUP"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(
        db.Integer,
        db.ForeignKey("business.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    regime = db.Column(db.String(20), nullable=False, index=True)
    location = db.Column(db.String(20), nullable=False, index=True)
    subaccount_code = db.Column(db.String(50), nullable=False, index=True)
    subaccount_name = db.Column(db.String(120), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default=CURRENCY_CUP)
    current_balance = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        nullable=False,
    )

    business = db.relationship(
        "Business",
        backref=db.backref(
            "cash_subaccount_balances",
            lazy="dynamic",
            cascade="all, delete-orphan",
        ),
    )

    __table_args__ = (
        db.CheckConstraint(
            "regime IN ('fiscal', 'financiera')",
            name="cash_subaccount_balance_regime_allowed_values",
        ),
        db.CheckConstraint(
            "location IN ('cash_box', 'bank_account')",
            name="cash_subaccount_balance_location_allowed_values",
        ),
        db.CheckConstraint(
            "currency = 'CUP'",
            name="cash_subaccount_balance_currency_cup_only",
        ),
        db.CheckConstraint(
            "current_balance >= 0",
            name="cash_subaccount_balance_non_negative",
        ),
        db.UniqueConstraint(
            "business_id",
            "subaccount_code",
            name="uq_cash_subaccount_balance_business_code",
        ),
    )

    def __repr__(self):
        return (
            f"<CashSubaccountBalance business_id={self.business_id} "
            f"code={self.subaccount_code} balance={self.current_balance}>"
        )
