from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def validate_gdp(df: DataFrame) -> DataFrame:
    # GDP and sub-components must be positive
    for col in ("gdp_value", "gfcf_value", "gni_value", "agri_va", "manuf_va", "va_foodbev"):
        df = df.withColumn(col, F.when(F.col(col) < 0, F.lit(None)).otherwise(F.col(col)))
    return df


def validate_shares(df: DataFrame) -> DataFrame:
    # Ratio indicators should be in [0, 200] — extreme values are likely errors
    for col in ("gfcf_to_gdp", "agri_va_share", "manuf_va_share"):
        df = df.withColumn(
            col,
            F.when((F.col(col) < 0) | (F.col(col) > 200), F.lit(None))
            .otherwise(F.col(col)),
        )
    # food_bev is share within manufacturing — should be in [0, 100]
    df = df.withColumn(
        "food_bev_share_manuf",
        F.when((F.col("food_bev_share_manuf") < 0) | (F.col("food_bev_share_manuf") > 100), F.lit(None))
        .otherwise(F.col("food_bev_share_manuf")),
    )
    # GNI/GDP ratio should be in [0.5, 2.0]
    df = df.withColumn(
        "gni_to_gdp",
        F.when((F.col("gni_to_gdp") < 0.5) | (F.col("gni_to_gdp") > 2.0), F.lit(None))
        .otherwise(F.col("gni_to_gdp")),
    )
    return df


def validate_growth(df: DataFrame) -> DataFrame:
    # GDP growth beyond ±100% per year is likely a data error
    df = df.withColumn(
        "gdp_growth_yoy",
        F.when(F.abs(F.col("gdp_growth_yoy")) > 100, F.lit(None))
        .otherwise(F.col("gdp_growth_yoy")),
    )
    return df


def validate_flag_score(df: DataFrame) -> DataFrame:
    # flag_score should be in {0, 1, 2, 3}
    df = df.withColumn(
        "flag_score",
        F.when(F.col("flag_score").isin(0.0, 1.0, 2.0, 3.0), F.col("flag_score"))
        .otherwise(F.lit(None)),
    )
    return df


def drop_duplicates(df: DataFrame) -> DataFrame:
    return df.dropDuplicates(["country_code", "year"])


def validate_all(df: DataFrame) -> DataFrame:
    df = validate_gdp(df)
    df = validate_shares(df)
    df = validate_growth(df)
    df = validate_flag_score(df)
    df = drop_duplicates(df)
    return df
