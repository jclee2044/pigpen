"""Typed wire models shared by HTTP and operation replay."""
from datetime import date, datetime, timezone
from typing import Annotated, Literal, Union
from uuid import UUID
from pydantic import HttpUrl, BaseModel, ConfigDict, Field, StrictBool, StrictInt, create_model, field_validator
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
    allows_subcategories: StrictBool = False


class CategoryUpdate(Model):
    expected_revision: Revision
    name: Text
    active: StrictBool
    allows_subcategories: StrictBool | None = None


class CategoryReorder(Model):
    expected_revision: Revision
    category_ids: list[UUID] = Field(max_length=500)


PAYLOADS = {'household.initialize': HouseholdInit, 'user.create': UserCreate, 'user.update': UserUpdate,
            'category.create': CategoryCreate, 'category.update': CategoryUpdate, 'category.reorder': CategoryReorder}


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


class Allocation(Model):
    category_id: UUID
    amount_minor: Money


class BudgetSet(Model):
    month: str
    expected_revision: Annotated[StrictInt, Field(ge=0)] = 0
    expected_income_minor: Money = 0
    allocations: list[Allocation] | None = Field(default=None, max_length=500)

    @field_validator('month')
    @classmethod
    def valid_month(cls, value):
        month_bounds(value)
        return value


class PurchaseCreate(Model):
    item: Text
    amount_minor: PositiveMoney
    category_id: UUID
    transaction_date: date
    merchant: Annotated[str, Field(max_length=200)] | None = None
    description: Description = ''
    request_id: UUID | None = None
    request_revision: Revision | None = None


class PurchaseUpdate(PurchaseCreate):
    expected_revision: Revision


class Delete(Model):
    expected_revision: Revision


PAYLOADS.update({'budget.set': BudgetSet, 'purchase.create': PurchaseCreate,
                 'purchase.update': PurchaseUpdate, 'purchase.delete': Delete})
class IncomeCreate(Model):
    description: Text
    amount_minor: PositiveMoney
    transaction_date: date


class IncomeUpdate(IncomeCreate):
    expected_revision: Revision


class SavingsCreate(Model):
    kind: Literal['opening', 'contribution', 'withdrawal']
    amount_minor: Money
    transaction_date: date
    description: Description = ''


class BillCreate(Model):
    name: Text
    amount_minor: PositiveMoney
    category_id: UUID
    due_day: Annotated[StrictInt, Field(ge=1, le=31)]
    start_date: date
    description: Description = ''


class BillUpdate(BillCreate):
    expected_revision: Revision
    active: StrictBool = True


class BillPay(Model):
    bill_id: UUID
    due_date: date
    transaction_date: date
    amount_minor: PositiveMoney | None = None
    purchase_id: UUID | None = None


PAYLOADS.update({'income.create':IncomeCreate,'income.update':IncomeUpdate,'income.delete':Delete,
                 'savings.create':SavingsCreate,'savings.delete':Delete,
                 'bill.create':BillCreate,'bill.update':BillUpdate,'bill.pay':BillPay})
class WishlistCreate(Model):
    name: Text
    price_minor: Money
    description: Description = ''
    url: HttpUrl | None = None


class WishlistUpdate(WishlistCreate):
    expected_revision: Revision
    status: Literal['active','purchased','archived'] = 'active'


class RequestCreate(Model):
    item: Text
    amount_minor: PositiveMoney
    description: Description = ''
    url: HttpUrl | None = None
    category_id: UUID | None = None


class RequestUpdate(RequestCreate):
    expected_revision: Revision


class RequestDeny(Model):
    expected_revision: Revision
    reason: Annotated[str, Field(min_length=1, max_length=4000)]


class VoteSet(Model):
    request_id: UUID
    request_revision: Revision
    expected_revision: Annotated[StrictInt, Field(ge=0)] = 0
    approved: StrictBool


class CommentCreate(Model):
    target_resource: Literal['wishlist-items','approval-requests']
    target_id: UUID
    text: Annotated[str, Field(min_length=1,max_length=4000)]


PAYLOADS.update({'wishlist.create':WishlistCreate,'wishlist.update':WishlistUpdate,'wishlist.delete':Delete,
                 'request.create':RequestCreate,'request.update':RequestUpdate,'request.cancel':Delete,'request.delete':Delete,'request.deny':RequestDeny,
                 'vote.set':VoteSet,'comment.create':CommentCreate,'notification.read':Delete})
class InstallationSelect(Model):
    expected_revision: Annotated[StrictInt, Field(ge=0)] = 0


class SubscriptionSet(Model):
    installation_id: UUID
    expected_revision: Annotated[StrictInt, Field(ge=0)] = 0
    endpoint: HttpUrl
    p256dh: Annotated[str, Field(max_length=200)]
    auth: Annotated[str, Field(max_length=100)]


class AttachmentCreate(Model):
    purchase_id: UUID
    storage_key: str
    filename: str
    media_type: str
    byte_size: PositiveMoney
    checksum: str


class AttachmentOperation(Envelope):
    kind: Literal['attachment.create'] = 'attachment.create'
    data: AttachmentCreate


class AttachmentDeleteOperation(Envelope):
    kind: Literal['attachment.delete'] = 'attachment.delete'
    data: Delete


PAYLOADS.update({'installation.select':InstallationSelect,'subscription.set':SubscriptionSet,'subscription.disable':Delete})
Operation = operation_type()
