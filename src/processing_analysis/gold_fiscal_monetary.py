import numpy as np
import pandas as pd

from src.utils.gold_utils import (
    pivot_indicators, get_group_join, interpolate_numeric,
    add_completeness, load_to_postgres, KEY_COLS,
)

_INDICATOR_MAP = {
    "govdebt_gdp":          "govdebt_GDP",
    "debt_change_yoy":      "debt_change_YoY",
    "govrev_gdp":           "govrev_GDP",
    "govexp_gdp":           "govexp_GDP",
    "fiscal_balance_gdp":   "fiscal_balance_GDP",
    "cumulative_deficit_5yr":"cumulative_deficit_5yr",
    "ltrate":               "ltrate",
    "infl":                 "infl",
    "real_interest_rate":   "real_interest_rate",
    "tax_revenue_gdp":      "tax_revenue_pct_GDP",
    "inflation_consumer_prices": "inflation_cpi",
    "inflation_gdp_deflator":    "inflation_deflator",
    "inflation_gap":        "inflation_gap",
    "rolling_3yr_avg_cpi":  "rolling_3yr_avg_cpi",
}


def build(silver: pd.DataFrame) -> pd.DataFrame:
    df = pivot_indicators(silver, _INDICATOR_MAP)

    groups = get_group_join(silver)[["country_code", "year", "income_group", "development_group"]]
    df = df.merge(groups, on=["country_code", "year"], how="left")

    df = interpolate_numeric(df)
    df = add_completeness(df)
    df = df.sort_values(["country_code", "year"]).reset_index(drop=True)
    return df


def run(silver: pd.DataFrame, engine) -> None:
    df = build(silver)
    load_to_postgres(df, "gold_fiscal_monetary", engine)
