import datetime
import functools
from typing import Any, Optional

from tortoise import fields, models, timezone

try:
    from ciso8601 import parse_datetime
except ImportError:  # pragma: nocoverage
    from iso8601 import parse_date

    parse_datetime = functools.partial(parse_date, default_timezone=None)
from tortoise.timezone import get_timezone, localtime


class BaseModel(models.Model):
    id = fields.BigIntField(pk=True, index=True)

    async def to_dict(self, m2m=False):
        d = {}
        for field in self._meta.db_fields:
            d[field] = getattr(self, field)
        if m2m:
            for field in self._meta.m2m_fields:
                values = await getattr(self, field).all().values()
                d[field] = values
        return d

    class Meta:
        abstract = True


class UUIDModel:
    uuid = fields.UUIDField(unique=True, pk=False)


class CustomDatetimeField(fields.DatetimeField):
    def to_python_value(self, value: Any) -> Optional[datetime.datetime]:
        if value is None:
            value = None
        else:
            if isinstance(value, datetime.datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, int):
                value = datetime.datetime.fromtimestamp(value)
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                value = parse_datetime(value)
            if timezone.is_naive(value):
                value = timezone.make_aware(value, get_timezone())
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                value = localtime(value)
                value = value.strftime("%Y-%m-%d %H:%M:%S")
        self.validate(value)
        return value


class TimestampMixin:
    created_at = CustomDatetimeField(auto_now_add=True)
    updated_at = CustomDatetimeField(auto_now=True)
