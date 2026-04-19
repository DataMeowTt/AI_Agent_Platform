from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def validate_poverty(df: DataFrame) -> DataFrame:
    return df.withColumn(
        "poverty_headcount_ratio",
        F.coalesce(F.col("poverty_headcount_ratio"), F.lit(0.0)),
    )


def validate_unemployment(df: DataFrame) -> DataFrame:
    # Unemployment rate must be within [0, 100]
    for col in ("unemployment_total", "unemployment_youth"):
        df = df.withColumn(
            col,
            F.when((F.col(col) < 0) | (F.col(col) > 100), F.lit(None))
            .otherwise(F.col(col)),
        )
    return df


def validate_gdp(df: DataFrame) -> DataFrame:
    # GDP and GDP per capita must be positive
    for col in ("gdp", "gdp_per_capita"):
        df = df.withColumn(
            col,
            F.when(F.col(col) < 0, F.lit(None))
            .otherwise(F.col(col)),
        )
    return df


def validate_inflation(df: DataFrame) -> DataFrame:
    # Inflation above 1000% is treated as data error (hyperinflation outlier)
    for col in ("inflation_consumer_prices", "inflation_gdp_deflator"):
        df = df.withColumn(
            col,
            F.when(F.abs(F.col(col)) > 1000, F.lit(None))
            .otherwise(F.col(col)),
        )
    return df


def drop_duplicates(df: DataFrame) -> DataFrame:
    # One row per (country, year) in wide format
    return df.dropDuplicates(["country_code", "year"])


def validate_all(df: DataFrame) -> DataFrame:
    df = validate_poverty(df)
    df = validate_unemployment(df)
    df = validate_gdp(df)
    df = validate_inflation(df)
    df = drop_duplicates(df)
    return df
