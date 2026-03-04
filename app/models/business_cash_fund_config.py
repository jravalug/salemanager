from app.extensions import db


class BusinessCashFundConfig(db.Model):
    __tablename__ = "business_cash_fund_config"

    REGIME_FISCAL = "fiscal"
    REGIME_FINANCIAL = "financiera"

    LOCATION_CASH = "cash_box"
    LOCATION_BANK = "bank_account"

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
    display_name = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_custom = db.Column(db.Boolean, nullable=False, default=False)
    threshold_max_per_operation = db.Column(db.Float, nullable=True)
    requires_documentation = db.Column(db.Boolean, nullable=False, default=False)
    target_balance = db.Column(db.Float, nullable=True)
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
            "cash_fund_configs",
            lazy="dynamic",
            cascade="all, delete-orphan",
        ),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "business_id",
            "subaccount_code",
            name="uq_business_cash_fund_config_business_subaccount",
        ),
        db.CheckConstraint(
            "regime IN ('fiscal', 'financiera')",
            name="business_cash_fund_config_regime_allowed_values",
        ),
        db.CheckConstraint(
            "location IN ('cash_box', 'bank_account')",
            name="business_cash_fund_config_location_allowed_values",
        ),
        db.CheckConstraint(
            "threshold_max_per_operation IS NULL OR threshold_max_per_operation > 0",
            name="business_cash_fund_config_threshold_positive_or_null",
        ),
        db.CheckConstraint(
            "target_balance IS NULL OR target_balance >= 0",
            name="business_cash_fund_config_target_non_negative_or_null",
        ),
    )

    def __repr__(self):
        return (
            f"<BusinessCashFundConfig business_id={self.business_id} "
            f"subaccount_code={self.subaccount_code} active={self.is_active}>"
        )
