from tortoise import fields, models


class BaseModel(models.Model):
    id = fields.BigIntField(pk=True, index=True)

    async def to_dict(self, m2m=True):
        d = {}
        for field in self._meta.db_fields:
            d[field] = getattr(self, field)
        if m2m:
            for field in self._meta.m2m_fields:
                d[field] = await getattr(self, field).all().values()
        return d

    class Meta:
        abstract = True


class UUIDModel:
    uuid = fields.UUIDField(unique=True, pk=False)


class TimestampMixin:
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
