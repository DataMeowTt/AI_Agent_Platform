import numpy as np
import pandas as pd

from src.utils.gold_utils import (
    pivot_indicators, get_group_join, interpolate_numeric,
    add_completeness, load_to_postgres, KEY_COLS,
)

_INDICATOR_MAP = {
    "sov_debt_crisis":    "SovDebtCrisis",
    "currency_crisis":    "CurrencyCrisis",
    "banking_crisis":     "BankingCrisis",
    "crisis_composite":   "crisis_composite",
    "crisis_any":         "crisis_any",
    "reer_deviation":     "REER_deviation",
    "spending_efficiency":"spending_efficiency",
    "govdebt_gdp":        "govdebt_GDP",
    "fiscal_balance_gdp": "fiscal_balance_GDP",
    "rgdp_growth_yoy":    "rGDP_growth_YoY",
}

_NO_INTERP = ["SovDebtCrisis", "CurrencyCrisis", "BankingCrisis", "crisis_any", "crisis_composite"]


def build(silver: pd.DataFrame) -> pd.DataFrame:
    df = pivot_indicators(silver, _INDICATOR_MAP)

    df["rGDP_growth_YoY"] = df["rGDP_growth_YoY"].clip(-50, 50)

    for col in ["SovDebtCrisis", "CurrencyCrisis", "BankingCrisis", "crisis_any", "crisis_composite"]:
        if col in df.columns:
            df[col] = df[col].round().astype("Int64")

    groups = get_group_join(silver)[["country_code", "year", "income_group", "development_group"]]
    df = df.merge(groups, on=["country_code", "year"], how="left")

    df = interpolate_numeric(df, skip_cols=_NO_INTERP)
    df = add_completeness(df)
    df = df.sort_values(["country_code", "year"]).reset_index(drop=True)
    return df


def run(silver: pd.DataFrame, engine) -> None:
    df = build(silver)
    load_to_postgres(df, "gold_crisis_risk", engine, crisis_check=True)
