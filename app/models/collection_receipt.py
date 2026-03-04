from app.extensions import db


class CollectionReceipt(db.Model):
    __tablename__ = "collection_receipt"

    id = db.Column(db.Integer, primary_key=True)
    income_event_id = db.Column(
        db.Integer,
        db.ForeignKey("income_event.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    bank_operation_number = db.Column(db.String(80), nullable=False, index=True)
    collected_date = db.Column(db.Date, nullable=False, index=True)
    bank_name = db.Column(db.String(120), nullable=True)
    reconciled_by = db.Column(db.String(120), nullable=True)
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

    income_event = db.relationship(
        "IncomeEvent",
        backref=db.backref(
            "collection_receipt",
            uselist=False,
            cascade="all, delete-orphan",
        ),
    )

    def __repr__(self):
        return (
            f"<CollectionReceipt income_event_id={self.income_event_id} "
            f"operation={self.bank_operation_number}>"
        )
