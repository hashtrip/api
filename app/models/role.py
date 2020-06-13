from enum import IntFlag
from typing import Optional

from app.models.rwmodel import RWModel


class Right(IntFlag):
    """
    __X bit for
    _X_ bit for
    X__ bit for
    """
    PUBLIC = 0b001
    KOL = 0b010
    BUSINESS = 0b100


class Role(RWModel):
    role: str
    description: Optional[str]
    rights: Right = 0b1
