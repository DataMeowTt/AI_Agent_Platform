from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.config.countries import ALLOWED_ISO3

_YEAR_MIN = 1980
_YEAR_MAX = 2025


def filter_by_country(df: DataFrame) -> DataFrame:
    return df.filter(F.col("ISO3").isin(list(ALLOWED_ISO3)))


def filter_by_year(df: DataFrame) -> DataFrame:
    return df.filter(F.col("year").between(_YEAR_MIN, _YEAR_MAX))
