from typing import List

from pydantic import BaseModel, conint

from app.models.rwmodel import RWModel


class GeoJson(RWModel):
    type: str
    coordinates: List[int]


class Time(BaseModel):
    hour: conint(ge=0, lt=24)
    minute: conint(ge=0, lt=60)

    def __str__(self):
        return f"{self.hour}:{self.minute}"
