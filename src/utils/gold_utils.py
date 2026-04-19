import numpy as np
import pandas as pd
from sqlalchemy.engine import Engine

SILVER_FILE = "data/processed_data/processed.csv/part-00000-2fc4b3eb-af18-4b45-92fa-b24e370d3854-c000.csv"
KEY_COLS    = ["country_code", "country", "year"]
PRECEDENCE     = ("gmd", "wdi", "macro")

_INCOME_GROUP_MAP = {0.0: "Low income", 1.0: "Lower middle income", 2.0: "Upper middle income", 3.0: "High income"}

NO_INTERPOLATE = {"sov_debt_crisis", "currency_crisis", "banking_crisis", "income_group",
                  "crisis_any", "flag_score", "SovDebtCrisis", "CurrencyCrisis",
                  "BankingCrisis", "crisis_any", "flag_score"}


def load_silver() -> pd.DataFrame:
    return pd.read_csv(SILVER_FILE)


def _rank_source(source_series: pd.Series) -> pd.Series:
    rank_map = {s: i for i, s in enumerate(PRECEDENCE)}
    return source_series.str.lower().map(rank_map).fillna(999)


def apply_source_precedence(silver: pd.DataFrame, indicator: str) -> pd.DataFrame:
    df = silver[silver["indicator"] == indicator].copy()
    df["_rank"] = _rank_source(df["source"])
    df = df.sort_values("_rank").drop_duplicates(subset=["country_code", "year"], keep="first")
    return df.drop(columns="_rank")


def pivot_indicators(silver: pd.DataFrame, indicator_map: dict) -> pd.DataFrame:
    wide = None
    for ind, col in indicator_map.items():
        df = apply_source_precedence(silver, ind)[KEY_COLS + ["value"]].rename(columns={"value": col})
        wide = df if wide is None else wide.merge(df, on=KEY_COLS, how="outer")
    return wide if wide is not None else pd.DataFrame(columns=KEY_COLS)


def get_group_join(silver: pd.DataFrame) -> pd.DataFrame:
    inc = (
        apply_source_precedence(silver, "income_group_encoded")[KEY_COLS + ["value"]]
        .rename(columns={"value": "income_group"})
        .assign(income_group=lambda df: df["income_group"].map(_INCOME_GROUP_MAP))
    )
    dev = (
        apply_source_precedence(silver, "development_group")[KEY_COLS + ["value"]]
        .rename(columns={"value": "development_group"})
    )
    return inc.merge(dev[["country_code", "year", "development_group"]], on=["country_code", "year"], how="outer")


def interpolate_numeric(df: pd.DataFrame, skip_cols: list = None) -> pd.DataFrame:
    skip = set(KEY_COLS) | set(skip_cols or []) | NO_INTERPOLATE
    num_cols = [c for c in df.columns if c not in skip and pd.api.types.is_numeric_dtype(df[c])]
    df = df.copy()
    for col in num_cols:
        df[col] = (
            df.groupby("country_code")[col]
            .transform(lambda s: s.interpolate(method="linear", limit=2, limit_direction="both"))
        )
    return df


def add_completeness(df: pd.DataFrame) -> pd.DataFrame:
    feature_cols = [c for c in df.columns if c not in KEY_COLS]
    df = df.copy()
    df["completeness_score"] = df[feature_cols].notna().mean(axis=1).round(4)
    return df


def safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    d = den.replace(0, np.nan)
    return num.where(d.notna()) / d


def validate(df: pd.DataFrame, table: str, crisis_check: bool = False) -> None:
    n          = len(df)
    n_countries = df["country_code"].nunique()
    yr_min     = int(df["year"].min())
    yr_max     = int(df["year"].max())
    null_rate  = df.isnull().mean().mean() * 100
    cs         = df["completeness_score"]

    print(f"\n[TABLE] {table}")
    print(f"  Rows          : {n}")
    print(f"  Countries     : {n_countries}")
    print(f"  Year range    : {yr_min} – {yr_max}")
    print(f"  Null rate     : {null_rate:.2f}%")
    print(f"  completeness  : mean={cs.mean():.4f}, min={cs.min():.4f}")

    assert df["country_code"].dropna().str.match(r"^[A-Z]{3}$").all(), "country_code format error"
    assert df["year"].notna().all(), "year has nulls"
    assert df["completeness_score"].between(0.0, 1.0).all(), "completeness_score out of [0,1]"
    if crisis_check and "crisis_composite" in df.columns:
        assert df["crisis_composite"].dropna().isin([0, 1, 2, 3]).all(), "crisis_composite out of {0,1,2,3}"


def load_to_postgres(df: pd.DataFrame, table: str, engine: Engine, crisis_check: bool = False) -> None:
    validate(df, table, crisis_check)
    df.to_sql(table, engine, if_exists="replace", index=False, method="multi", chunksize=500)
    print(f"  loaded → postgres table: {table}")
