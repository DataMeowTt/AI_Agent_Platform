from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def validate_rgdp(df: DataFrame) -> DataFrame:
    # Real GDP and GDP per capita must be positive
    for col in ("rgdp", "rgdp_pc_usd"):
        df = df.withColumn(col, F.when(F.col(col) < 0, F.lit(None)).otherwise(F.col(col)))
    return df


def validate_inflation(df: DataFrame) -> DataFrame:
    # |infl| > 1000% treated as data error
    return df.withColumn(
        "infl",
        F.when(F.abs(F.col("infl")) > 1000, F.lit(None)).otherwise(F.col("infl")),
    )


def validate_rates(df: DataFrame) -> DataFrame:
    # Long-term rate outside [-20%, 200%] treated as outlier
    return df.withColumn(
        "ltrate",
        F.when(
            (F.col("ltrate") < -20) | (F.col("ltrate") > 200),
            F.lit(None),
        ).otherwise(F.col("ltrate")),
    )


def validate_debt(df: DataFrame) -> DataFrame:
    # Debt > 500% GDP is extreme — likely data error
    return df.withColumn(
        "govdebt_gdp",
        F.when(F.col("govdebt_gdp") > 500, F.lit(None)).otherwise(F.col("govdebt_gdp")),
    )


def validate_crisis_flags(df: DataFrame) -> DataFrame:
    # Crisis flags must be 0 or 1
    for col in ("sov_debt_crisis", "currency_crisis", "banking_crisis"):
        df = df.withColumn(
            col,
            F.when(F.col(col).isin(0.0, 1.0), F.col(col)).otherwise(F.lit(None)),
        )
    return df


def drop_duplicates(df: DataFrame) -> DataFrame:
    return df.dropDuplicates(["country_code", "year"])


def validate_all(df: DataFrame) -> DataFrame:
    df = validate_rgdp(df)
    df = validate_inflation(df)
    df = validate_rates(df)
    df = validate_debt(df)
    df = validate_crisis_flags(df)
    df = drop_duplicates(df)
    return df
