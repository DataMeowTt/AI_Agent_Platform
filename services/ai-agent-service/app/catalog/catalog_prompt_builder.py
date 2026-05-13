from app.catalog.canonical_indicator_catalog import (
    get_supported_indicators_compact,
    get_unsupported_indicators_compact,
)
from app.catalog.country_group_catalog import list_country_groups


def build_compact_indicator_catalog_for_prompt(max_aliases_per_indicator: int = 8) -> list[dict]:
    return get_supported_indicators_compact(max_aliases_per_indicator=max_aliases_per_indicator)


def build_compact_country_group_catalog_for_prompt() -> list[dict]:
    return [
        {
            "code": group.code,
            "name_vi": group.name_vi,
            "name_en": group.name_en,
            "aliases": list(group.aliases),
            "countries": list(group.countries),
        }
        for group in list_country_groups()
    ]


def build_compact_unsupported_indicator_catalog_for_prompt() -> list[dict]:
    return get_unsupported_indicators_compact()
