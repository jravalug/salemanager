from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import AppSetting


class AppSettingService:
    @staticmethod
    def get_value(key: str, default: str | None = None) -> str | None:
        try:
            setting = AppSetting.query.filter_by(key=key).first()
            if setting:
                return setting.value
            return default
        except SQLAlchemyError:
            return default

    @staticmethod
    def get_float(key: str, default: float) -> float:
        value = AppSettingService.get_value(key)
        if value is None:
            return float(default)

        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def set_value(key: str, value: str, description: str | None = None) -> AppSetting:
        try:
            setting = AppSetting.query.filter_by(key=key).first()

            if not setting:
                setting = AppSetting(key=key, value=value, description=description)
                db.session.add(setting)
            else:
                setting.value = value
                if description is not None:
                    setting.description = description

            db.session.commit()
            return setting
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise RuntimeError(
                "No se pudo guardar la configuración global. "
                "Verifica que las migraciones estén aplicadas."
            ) from exc
