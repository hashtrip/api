from typing import List

from pydantic import BaseModel, conint
from bson import ObjectId

from app.models.rwmodel import RWModel


class GeoJson(RWModel):
    type: str
    coordinates: List[int]


class Time(BaseModel):
    hour: conint(ge=0, lt=24)
    minute: conint(ge=0, lt=60)

    def __str__(self):
        return f"{self.hour}:{self.minute}"


class ObjID(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        bsoid = ObjectId()
        if not bsoid.is_valid(str(v)):
            return ValueError(f"Must be ObjectId: {v}")
        return ObjectId(str(v))
