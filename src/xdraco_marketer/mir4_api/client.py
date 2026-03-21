"""Cliente HTTP para webapi.mir4global.com (listado + detalle NFT)."""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlencode

import httpx

from xdraco_marketer.mir4_api.errors import Mir4ApiError, Mir4HttpError
from xdraco_marketer.mir4_api.listing_build import (
    assert_api_ok,
    character_from_summary_and_stats,
    listing_from_row_and_details,
)
from xdraco_marketer.models.character import CharacterProfile
from xdraco_marketer.models.listing import Listing

DEFAULT_BASE = "https://webapi.mir4global.com"
DEFAULT_HEADERS: dict[str, str] = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.xdraco.com",
    "Referer": "https://www.xdraco.com/",
    "User-Agent": (
        "Mozilla/5.0 (compatible; xdraco-marketer/0.1; +https://github.com/) "
        "httpx"
    ),
}


class Mir4Client:
    """Sin autenticación mientras la API sea pública; opcional delay entre llamadas."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE,
        *,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        delay_s: float = 0.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._delay_s = max(0.0, delay_s)
        h = {**DEFAULT_HEADERS, **(headers or {})}
        kw: dict[str, Any] = {"base_url": self.base_url, "timeout": timeout, "headers": h}
        if transport is not None:
            kw["transport"] = transport
        self._client = httpx.Client(**kw)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Mir4Client:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _sleep(self) -> None:
        if self._delay_s:
            time.sleep(self._delay_s)

    def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        self._sleep()
        q = urlencode(params)
        url = f"{path}?{q}"
        try:
            r = self._client.get(url)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise Mir4HttpError(str(e)) from e
        try:
            return r.json()
        except ValueError as e:
            raise Mir4ApiError("respuesta no es JSON") from e

    def fetch_sale_list(
        self,
        *,
        page: int = 1,
        list_type: str = "sale",
        class_id: int = 0,
        lev_min: int = 0,
        lev_max: int = 0,
        power_min: int = 0,
        power_max: int = 0,
        price_min: int = 0,
        price_max: int = 0,
        sort: str = "latest",
        language_code: str = "es",
    ) -> dict[str, Any]:
        """Devuelve el objeto `data` de /nft/lists."""

        raw = self._get_json(
            "/nft/lists",
            {
                "listType": list_type,
                "class": class_id,
                "levMin": lev_min,
                "levMax": lev_max,
                "powerMin": power_min,
                "powerMax": power_max,
                "priceMin": price_min,
                "priceMax": price_max,
                "sort": sort,
                "page": page,
                "languageCode": language_code,
            },
        )
        return assert_api_ok(raw, context="nft/lists")

    def iter_sale_rows(
        self,
        *,
        max_pages: int | None = None,
        class_id: int = 0,
        sort: str = "latest",
        language_code: str = "es",
    ) -> Iterator[dict[str, Any]]:
        """Pagina `lists[]` mientras `more` sea truthy."""

        page = 1
        while True:
            data = self.fetch_sale_list(
                page=page,
                class_id=class_id,
                sort=sort,
                language_code=language_code,
            )
            rows = data.get("lists") or []
            if not isinstance(rows, list):
                break
            yield from rows
            more = data.get("more")
            if not more:
                break
            page += 1
            if max_pages is not None and page > max_pages:
                break

    def fetch_character_summary(self, seq: int, *, language_code: str = "es") -> dict[str, Any]:
        raw = self._get_json(
            "/nft/character/summary",
            {"seq": seq, "languageCode": language_code},
        )
        return assert_api_ok(raw, context="nft/character/summary")

    def fetch_character_stats(
        self, transport_id: int, *, language_code: str = "es"
    ) -> list[dict[str, Any]]:
        raw = self._get_json(
            "/nft/character/stats",
            {"transportID": transport_id, "languageCode": language_code},
        )
        data = assert_api_ok(raw, context="nft/character/stats")
        lists = data.get("lists") or []
        if not isinstance(lists, list):
            return []
        return lists

    def fetch_character_bundle(
        self, seq: int, transport_id: int, *, language_code: str = "es"
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Summary + stats en dos GET."""

        summary = self.fetch_character_summary(seq, language_code=language_code)
        stats = self.fetch_character_stats(transport_id, language_code=language_code)
        return summary, stats

    def fetch_full_character(
        self, seq: int, transport_id: int, *, language_code: str = "es"
    ) -> CharacterProfile:
        s, st = self.fetch_character_bundle(seq, transport_id, language_code=language_code)
        return character_from_summary_and_stats(s, st)

    def fetch_listing(
        self, row: dict[str, Any], *, language_code: str = "es"
    ) -> Listing:
        """Una fila del listado → summary + stats → `Listing`."""

        seq = int(row["seq"])
        tid = int(row["transportID"])
        summary, stats_lists = self.fetch_character_bundle(
            seq, tid, language_code=language_code
        )
        return listing_from_row_and_details(row, summary, stats_lists)
