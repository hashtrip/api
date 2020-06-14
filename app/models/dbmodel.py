from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from bson import ObjectId
from .util import ObjID


class DateTimeModelMixin(BaseModel):
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")


class DBModelMixin(DateTimeModelMixin):
    id: Optional[ObjID] = Field(..., alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: lambda x: str(x),
        }
