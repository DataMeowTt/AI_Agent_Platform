from sqlalchemy import bindparam, text

from app.catalog.analytics_catalog import get_analytics_table_for_indicator
from app.db.postgres import engine
from app.tools.common import (
    normalize_country_codes,
    quote_identifier,
    require_indicator,
    rows_to_dicts,
)


def get_indicator_anomalies(
    indicator_code: str,
    country_codes: list[str] | None = None,
    threshold: float = 0.75,
    start_year: int | None = None,
    end_year: int | None = None,
    limit: int = 50,
) -> list[dict]:
    indicator = require_indicator(indicator_code)

    analytics_table = get_analytics_table_for_indicator(indicator_code)

    if not analytics_table:
        return []

    gold_table = indicator.gold_table

    actual_col = quote_identifier(f"{indicator_code}_actual")
    trend_col = quote_identifier(f"{indicator_code}_trend")
    residual_col = quote_identifier(f"{indicator_code}_residual")
    anomaly_score_col = quote_identifier(f"{indicator_code}_anomaly_score")

    countries = normalize_country_codes(country_codes)

    conditions = [
        f"a.{anomaly_score_col} IS NOT NULL",
        f"a.{anomaly_score_col} >= :threshold",
    ]

    params: dict = {
        "threshold": threshold,
        "limit": max(1, min(limit, 100)),
    }

    if countries:
        conditions.append("a.country_code IN :country_codes")
        params["country_codes"] = countries

    if start_year is not None:
        conditions.append("a.year >= :start_year")
        params["start_year"] = start_year

    if end_year is not None:
        conditions.append("a.year <= :end_year")
        params["end_year"] = end_year

    where_sql = " AND ".join(conditions)

    sql = text(
        f"""
        SELECT
            a.country_code,
            g.country,
            a.year,
            a.{actual_col} AS actual_value,
            a.{trend_col} AS trend_value,
            a.{residual_col} AS residual_value,
            a.{anomaly_score_col} AS anomaly_score
        FROM {analytics_table} a
        LEFT JOIN {gold_table} g
          ON a.country_code = g.country_code
         AND a.year = g.year
        WHERE {where_sql}
        ORDER BY anomaly_score DESC, a.year DESC
        LIMIT :limit
        """
    )

    if countries:
        sql = sql.bindparams(bindparam("country_codes", expanding=True))

    with engine.connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    return rows_to_dicts(rows)