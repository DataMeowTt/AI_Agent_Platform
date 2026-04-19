from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.processing.MACRO.macro_transform.macro_clean import COUNTRY_ISO3_MAP

_ALLOWED_AREAS  = frozenset(COUNTRY_ISO3_MAP.keys())
_ALLOWED_ITEMS  = {"22008", "22015", "22011", "22016", "22075", "22076"}
_YEAR_MIN, _YEAR_MAX = 1980, 2025


def filter_by_area(df: DataFrame) -> DataFrame:
    return df.filter(F.col("Area").isin(list(_ALLOWED_AREAS)))


def filter_by_year(df: DataFrame) -> DataFrame:
    return df.filter(F.col("Year").cast("int").between(_YEAR_MIN, _YEAR_MAX))


def filter_by_item(df: DataFrame) -> DataFrame:
    return df.filter(F.col("Item Code").isin(list(_ALLOWED_ITEMS)))
