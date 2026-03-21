"""Detección de gangas: precio bajo respecto al cohorte que cumple la misma regla."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median

from pydantic import BaseModel, Field

from xdraco_marketer.models.listing import Currency, Listing
from xdraco_marketer.rules.ast import RuleExpr
from xdraco_marketer.rules.evaluate import matches


class BargainSettings(BaseModel):
    """precio <= median(otros del cohorte) * median_ratio_max."""

    median_ratio_max: Decimal = Field(default=Decimal("0.92"), ge=0, le=1)
    min_comparables: int = Field(default=3, ge=2)
    """Tamaño mínimo del cohorte (todos los que cumplen la regla) para calcular gangas."""
    same_currency_only: bool = True


@dataclass(frozen=True)
class BargainCandidate:
    listing: Listing
    cohort_size: int
    median_peer_price: Decimal
    """Mediana de precios del cohorte excluyendo este listado."""
    ratio_to_median: Decimal
    """listing.price / median_peer_price."""


class BargainDetector:
    def __init__(self, rule: RuleExpr, settings: BargainSettings | None = None) -> None:
        self.rule = rule
        self.settings = settings or BargainSettings()

    def cohort(self, listings: list[Listing]) -> list[Listing]:
        return [li for li in listings if matches(li.character, self.rule)]

    def find(
        self,
        listings: list[Listing],
        *,
        currency: Currency | None = None,
    ) -> list[BargainCandidate]:
        cohort = self.cohort(listings)
        if currency is not None:
            cohort = [x for x in cohort if x.currency == currency]

        if self.settings.same_currency_only and len({x.currency for x in cohort}) > 1:
            results: list[BargainCandidate] = []
            for ccy in sorted({x.currency for x in cohort}, key=lambda x: x.value):
                group = [x for x in cohort if x.currency == ccy]
                results.extend(self._find_in_group(group))
            return results

        return self._find_in_group(cohort)

    def _find_in_group(self, cohort: list[Listing]) -> list[BargainCandidate]:
        if len(cohort) < self.settings.min_comparables:
            return []

        out: list[BargainCandidate] = []
        for li in cohort:
            others = [x.price for x in cohort if x.listing_id != li.listing_id]
            if len(others) < self.settings.min_comparables - 1:
                continue
            med_peer = median(others)
            if med_peer <= 0:
                continue
            if li.price <= med_peer * self.settings.median_ratio_max:
                ratio = li.price / med_peer
                out.append(
                    BargainCandidate(
                        listing=li,
                        cohort_size=len(cohort),
                        median_peer_price=med_peer,
                        ratio_to_median=ratio,
                    )
                )
        return out
