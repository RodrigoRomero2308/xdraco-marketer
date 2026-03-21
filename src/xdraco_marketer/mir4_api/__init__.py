"""Adaptadores para la API web pública MIR4 / XDraco (webapi.mir4global.com)."""

from xdraco_marketer.mir4_api.client import Mir4Client
from xdraco_marketer.mir4_api.constants import CLASS_ID_TO_SLUG, grade_to_rarity_label
from xdraco_marketer.mir4_api.errors import Mir4ApiError, Mir4HttpError
from xdraco_marketer.mir4_api.list_row import list_row_to_profile_stub
from xdraco_marketer.mir4_api.listing_build import listing_from_row_and_details
from xdraco_marketer.mir4_api.merge import with_stats
from xdraco_marketer.mir4_api.parsing import parse_stat_value
from xdraco_marketer.mir4_api.stats_parse import stats_response_to_stat_map
from xdraco_marketer.mir4_api.summary_profile import summary_data_to_profile
from xdraco_marketer.stat_labels import normalize_stat_label

__all__ = [
    "CLASS_ID_TO_SLUG",
    "Mir4ApiError",
    "Mir4Client",
    "Mir4HttpError",
    "grade_to_rarity_label",
    "list_row_to_profile_stub",
    "listing_from_row_and_details",
    "normalize_stat_label",
    "parse_stat_value",
    "stats_response_to_stat_map",
    "summary_data_to_profile",
    "with_stats",
]
