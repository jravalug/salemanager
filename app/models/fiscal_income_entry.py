from app.extensions import db


class FiscalIncomeEntry(db.Model):
    __tablename__ = "fiscal_income_entry"

    REGIME_FISCAL = "fiscal"
    REGIME_FINANCIAL = "financiera"

    id = db.Column(db.Integer, primary_key=True)
    income_event_id = db.Column(
        db.Integer,
        db.ForeignKey("income_event.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    business_id = db.Column(
        db.Integer,
        db.ForeignKey("business.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recognition_date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    regime = db.Column(db.String(20), nullable=False, index=True)
    source_ref = db.Column(db.String(50), nullable=True, index=True)
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

    income_event = db.relationship("IncomeEvent", backref="fiscal_income_entry")

    __table_args__ = (
        db.CheckConstraint(
            "amount >= 0",
            name="fiscal_income_entry_amount_non_negative",
        ),
        db.CheckConstraint(
            "regime IN ('fiscal', 'financiera')",
            name="fiscal_income_entry_regime_allowed_values",
        ),
    )

    def __repr__(self):
        return (
            f"<FiscalIncomeEntry income_event_id={self.income_event_id} "
            f"date={self.recognition_date} amount={self.amount}>"
        )
