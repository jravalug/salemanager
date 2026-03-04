from app.extensions import db


class IncomeEvent(db.Model):
    __tablename__ = "income_event"

    ORIGIN_SALE = "sale"
    ORIGIN_SERVICE = "service"
    ORIGIN_MANUAL = "manual"

    CHANNEL_CASH = "cash"
    CHANNEL_BANK_TRANSFER = "bank_transfer"
    CHANNEL_CARD = "card"

    STATUS_IMMEDIATE = "immediate"
    STATUS_PENDING = "pending"
    STATUS_COLLECTED = "collected"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(
        db.Integer,
        db.ForeignKey("business.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    origin_type = db.Column(db.String(20), nullable=False, index=True)
    payment_channel = db.Column(db.String(20), nullable=False, index=True)
    collection_status = db.Column(db.String(20), nullable=False, index=True)
    collected_date = db.Column(db.Date, nullable=True, index=True)
    bank_operation_number = db.Column(db.String(80), nullable=True, index=True)
    reconciled_by = db.Column(db.String(120), nullable=True)
    reconciled_at = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.String(255), nullable=True)
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

    business = db.relationship(
        "Business",
        backref=db.backref(
            "income_events",
            lazy="dynamic",
            cascade="all, delete-orphan",
        ),
    )

    __table_args__ = (
        db.CheckConstraint("amount >= 0", name="income_event_amount_non_negative"),
        db.CheckConstraint(
            "origin_type IN ('sale', 'service', 'manual')",
            name="income_event_origin_type_allowed_values",
        ),
        db.CheckConstraint(
            "payment_channel IN ('cash', 'bank_transfer', 'card')",
            name="income_event_payment_channel_allowed_values",
        ),
        db.CheckConstraint(
            "collection_status IN ('immediate', 'pending', 'collected')",
            name="income_event_collection_status_allowed_values",
        ),
    )

    def __repr__(self):
        return (
            f"<IncomeEvent business_id={self.business_id} "
            f"event_date={self.event_date} amount={self.amount} "
            f"status={self.collection_status}>"
        )
