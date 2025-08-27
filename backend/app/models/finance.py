from datetime import date, datetime
from pydantic import BaseModel, Field, field_serializer
from typing import Optional

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tenant_id: str

class GroupInDB(GroupCreate):
    id: str
    created_at: str

class SubgroupCreate(BaseModel):
    group_id: str
    name: str
    description: Optional[str] = None
    tenant_id: str

class SubgroupInDB(SubgroupCreate):
    id: str
    created_at: str

class AccountCreate(BaseModel):
    subgroup_id: str
    name: str
    balance: float
    tenant_id: str

class AccountInDB(AccountCreate):
    id: str
    created_at: str


class TransactionCreate(BaseModel):
    account_id: str
    amount: float
    date: date
    description: Optional[str] = None
    tenant_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_serializer("date", when_used="json")
    def serialize_date(self, v: date) -> str:
        return v.isoformat()

    @field_serializer("created_at", when_used="json")
    def serialize_created_at(self, v: datetime) -> str:
        return v.isoformat()


class TransactionInDB(TransactionCreate):
    id: str


class ForecastCreate(BaseModel):
    account_id: str
    amount: float
    expected_date: date
    description: Optional[str] = None
    tenant_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_serializer("expected_date", when_used="json")
    def serialize_expected_date(self, v: date) -> str:
        return v.isoformat()

    @field_serializer("created_at", when_used="json")
    def serialize_created_at(self, v: datetime) -> str:
        return v.isoformat()


class ForecastInDB(ForecastCreate):
    id: str
