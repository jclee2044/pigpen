"""Typed wire models shared by HTTP and operation replay."""
from datetime import date, datetime, timezone
from typing import Annotated, Literal, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, create_model, field_validator
from .domain import MAX_MINOR, month_bounds

Money = Annotated[StrictInt, Field(ge=0, le=MAX_MINOR)]
PositiveMoney = Annotated[StrictInt, Field(gt=0, le=MAX_MINOR)]
Revision = Annotated[StrictInt, Field(ge=1)]
Text = Annotated[str, Field(min_length=1, max_length=200)]
Description = Annotated[str, Field(max_length=4000)]


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Avatar(Model):
    background: str = 'cream'
    bandana: str = 'grass'
    glasses: str = 'none'
    hat: str = 'none'
    eyelashes: str = 'none'


class HouseholdInit(Model):
    name: Text
    currency: Literal['USD'] = 'USD'
    timezone: Literal['America/New_York'] = 'America/New_York'


class UserCreate(Model):
    name: Text
    avatar: Avatar = Field(default_factory=Avatar)


class UserUpdate(UserCreate):
    expected_revision: Revision
    active: StrictBool = True


class CategoryCreate(Model):
    name: Text
    kind: Literal['expense', 'personal', 'savings'] = 'expense'
    owner_id: UUID | None = None
    parent_id: UUID | None = None


class CategoryUpdate(Model):
    expected_revision: Revision
    name: Text
    active: StrictBool


PAYLOADS = {'household.initialize': HouseholdInit, 'user.create': UserCreate, 'user.update': UserUpdate,
            'category.create': CategoryCreate, 'category.update': CategoryUpdate}


class Envelope(Model):
    operation_id: UUID
    entity_id: UUID
    actor_id: UUID | None = None
    client_time: datetime

    @field_validator('client_time')
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('client_time must include a timezone')
        return value.astimezone(timezone.utc)


def operation_type():
    # A fixed registry produces a discriminated OpenAPI union, not untyped payloads.
    models = [create_model(kind.replace('.', '_'), __base__=Envelope,
                           kind=(Literal[kind], ...), data=(data, ...)) for kind, data in PAYLOADS.items()]
    return Annotated[Union[tuple(models)], Field(discriminator='kind')]


Operation = operation_type()
