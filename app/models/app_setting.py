from app.extensions import db


class AppSetting(db.Model):
    __tablename__ = "app_setting"

    KEY_ACCOUNTING_FISCAL_THRESHOLD = "accounting_fiscal_threshold"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
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

    def __repr__(self):
        return f"<AppSetting key={self.key} value={self.value}>"
