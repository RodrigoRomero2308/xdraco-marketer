from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from xdraco_marketer.models.character import CharacterProfile


class Currency(StrEnum):
    WEMIX = "WEMIX"
    DRACO = "DRACO"
    USDT = "USDT"
    UNKNOWN = "UNKNOWN"


class Listing(BaseModel):
    """Listado de mercado con personaje asociado."""

    listing_id: str
    character: CharacterProfile
    price: Decimal = Field(ge=0)
    currency: Currency = Currency.UNKNOWN
    # Metadatos opcionales (cadena, colección, URL…)
    extra: dict[str, str] = Field(default_factory=dict)
