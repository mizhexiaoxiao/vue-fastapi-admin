from datetime import datetime

from tortoise import fields, models

from app.settings import settings


class BaseModel(models.Model):
    id = fields.BigIntField(pk=True, index=True)

    async def to_dict(self, m2m: bool = False, exclude_fields: list[str] | None = None):
        if exclude_fields is None:
            exclude_fields = []

        d = {}
        for field in self._meta.db_fields:
            if field not in exclude_fields:
                value = getattr(self, field)
                if isinstance(value, datetime):
                    value = value.strftime(settings.DATETIME_FORMAT)
                d[field] = value
        if m2m:
            for field in self._meta.m2m_fields:
                if field not in exclude_fields:
                    values = [value for value in await getattr(self, field).all().values()]
                    for value in values:
                        value.update(
                            (k, v.strftime(settings.DATETIME_FORMAT))
                            for k, v in value.items()
                            if isinstance(v, datetime)
                        )
                    d[field] = values
        return d

    class Meta:
        abstract = True


class UUIDModel:
    uuid = fields.UUIDField(unique=True, pk=False)


class TimestampMixin:
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
