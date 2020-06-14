from enum import IntFlag
from typing import Optional

from app.models.rwmodel import RWModel


class Right(IntFlag):
    """
    __X bit for
    _X_ bit for
    X__ bit for
    """
    CREATE_PLACE = 0
    DELETE_SELF_PLACE = 1


class RoleHaveRight(IntFlag):
    PUBLIC = 0b001
    BUSINESS = 0b100


class Role(RWModel):
    role: str
    description: Optional[str]
    rights: RoleHaveRight = 0b1
