from app.extensions import db


class CashChangeDenomination(db.Model):
    __tablename__ = "cash_change_denomination"

    id = db.Column(db.Integer, primary_key=True)
    movement_id = db.Column(
        db.Integer,
        db.ForeignKey("cash_subaccount_movement.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    denomination_value = db.Column(db.Float, nullable=False)
    unit_count = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        nullable=False,
    )

    movement = db.relationship(
        "CashSubaccountMovement",
        backref=db.backref(
            "change_denominations",
            lazy="select",
            cascade="all, delete-orphan",
        ),
    )

    __table_args__ = (
        db.CheckConstraint(
            "denomination_value > 0",
            name="cash_change_denomination_value_positive",
        ),
        db.CheckConstraint(
            "unit_count > 0",
            name="cash_change_denomination_unit_count_positive",
        ),
        db.CheckConstraint(
            "total_amount > 0",
            name="cash_change_denomination_total_positive",
        ),
    )

    def __repr__(self):
        return (
            f"<CashChangeDenomination movement_id={self.movement_id} "
            f"value={self.denomination_value} unit_count={self.unit_count}>"
        )
