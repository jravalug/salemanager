from app.extensions import db


class DailyIncome(db.Model):
    __tablename__ = "daily_income"

    TYPE_INCOME_OBTAINED = "income_obtained"
    TYPE_NON_TAXABLE = "non_taxable"

    ACTIVITY_SALE = "sale"
    ACTIVITY_SERVICE = "service"

    LOCATION_CASH = "cash_register"
    LOCATION_BANK = "bank_cash"

    SOURCE_MANUAL = "manual"
    SOURCE_SALES_SUMMARY = "sales_summary"
    PAYMENT_METHOD_CASH = "cash"
    PAYMENT_METHOD_TRANSFER = "transfer"
    PAYMENT_METHOD_CHECK = "check"

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(
        db.Integer,
        db.ForeignKey("business.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = db.Column(db.Date, nullable=False, index=True)
    income_type = db.Column(
        db.String(20), nullable=False, default=TYPE_INCOME_OBTAINED, index=True
    )
    activity = db.Column(db.String(20), nullable=False, default=ACTIVITY_SALE)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.String(255), nullable=True)
    payment_method = db.Column(
        db.String(20), nullable=False, default=PAYMENT_METHOD_CASH
    )
    cash_location = db.Column(
        db.String(20), nullable=False, default=LOCATION_CASH, index=True
    )
    debtor_type = db.Column(db.String(20), nullable=True)
    debtor_natural_full_name = db.Column(db.String(150), nullable=True)
    debtor_natural_identity_number = db.Column(db.String(50), nullable=True)
    debtor_natural_bank_account = db.Column(db.String(80), nullable=True)
    debtor_legal_entity_name = db.Column(db.String(200), nullable=True)
    debtor_legal_reeup_code = db.Column(db.String(50), nullable=True)
    debtor_legal_address = db.Column(db.String(255), nullable=True)
    debtor_legal_credit_branch = db.Column(db.String(120), nullable=True)
    debtor_legal_bank_account = db.Column(db.String(80), nullable=True)
    debtor_legal_contract_number = db.Column(db.String(80), nullable=True)
    source = db.Column(db.String(20), nullable=False, default=SOURCE_MANUAL, index=True)
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
            "daily_incomes", lazy="dynamic", cascade="all, delete-orphan"
        ),
    )

    __table_args__ = (
        db.CheckConstraint("amount >= 0", name="daily_income_amount_non_negative"),
        db.CheckConstraint(
            "income_type IN ('income_obtained', 'non_taxable')",
            name="daily_income_type_allowed_values",
        ),
        db.CheckConstraint(
            "activity IN ('sale', 'service')",
            name="daily_income_activity_allowed_values",
        ),
        db.CheckConstraint(
            "cash_location IN ('cash_register', 'bank_cash')",
            name="daily_income_cash_location_allowed_values",
        ),
        db.CheckConstraint(
            "source IN ('manual', 'sales_summary')",
            name="daily_income_source_allowed_values",
        ),
        db.UniqueConstraint(
            "business_id",
            "date",
            "income_type",
            "activity",
            "cash_location",
            "source",
            name="uq_daily_income_summary_bucket",
        ),
    )

    def __repr__(self):
        return (
            f"<DailyIncome business_id={self.business_id} date={self.date} "
            f"amount={self.amount}>"
        )
