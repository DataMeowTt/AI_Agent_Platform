from dataclasses import asdict, dataclass

from app.catalog.canonical_indicator_catalog import (
    detect_unsupported_indicator,
    normalize_catalog_text,
    resolve_indicator_alias,
    resolve_indicator_aliases,
)
from app.catalog.indicator_catalog import INDICATORS, IndicatorMeta
from app.catalog.analytics_catalog import get_indicator_analytics_metadata


UNSUPPORTED_INDICATOR_ALIASES: dict[str, tuple[str, ...]] = {
    "cán cân vãng lai/GDP": (
        "current account/GDP",
        "current account balance/GDP",
        "current account GDP",
        "current account",
        "current_account_GDP",
        "curr_account_GDP",
        "cán cân vãng lai/GDP",
        "can can vang lai/GDP",
    ),
    "nợ nước ngoài/GNI": (
        "external debt/GNI",
        "external debt to GNI",
        "external debt",
        "external_debt_GNI",
        "nợ nước ngoài/GNI",
        "no nuoc ngoai/GNI",
    ),
}


@dataclass(frozen=True)
class IndicatorMatch:
    indicator: IndicatorMeta
    confidence: float
    matched_alias: str


def normalize_text(text: str) -> str:
    return normalize_catalog_text(text)


def resolve_indicator(message: str) -> IndicatorMatch | None:
    match = resolve_indicator_alias(message)
    if not match:
        return None

    indicator = INDICATORS.get(match.indicator.code)
    if not indicator:
        return None

    return IndicatorMatch(
        indicator=indicator,
        confidence=match.confidence,
        matched_alias=match.matched_alias,
    )


def resolve_indicators(message: str, limit: int = 3) -> list[IndicatorMatch]:
    matches: list[IndicatorMatch] = []
    for match in resolve_indicator_aliases(message, limit=limit):
        indicator = INDICATORS.get(match.indicator.code)
        if not indicator:
            continue
        matches.append(
            IndicatorMatch(
                indicator=indicator,
                confidence=match.confidence,
                matched_alias=match.matched_alias,
            )
        )
    return matches


def detect_unsupported_indicator_label(message: str) -> str | None:
    match = detect_unsupported_indicator(message)
    return match.label_vi if match else None


def indicator_match_to_dict(match: IndicatorMatch) -> dict:
    data = asdict(match.indicator)
    analytics_metadata = get_indicator_analytics_metadata(match.indicator.code)

    data["confidence"] = match.confidence
    data["matched_alias"] = match.matched_alias
    data["analytics"] = analytics_metadata
    if analytics_metadata["analytics_table"]:
        data["analytics_table"] = analytics_metadata["analytics_table"]

    return data
