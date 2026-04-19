from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from processing.schema.processed_schema import PROCESSED_SCHEMA, SOURCE_WDI

YEAR_COLS = [str(y) for y in range(1980, 2026)]

_country_code, _country, _year, _indicator, _value, _source = PROCESSED_SCHEMA.fieldNames()

_ID_COLS = {_country_code, _country, _year, _source}


def flatten_years(df: DataFrame) -> DataFrame:
    unpivoted = df.unpivot(
        ids=["Country Name", "Country Code", "Indicator Name"],
        values=YEAR_COLS,
        variableColumnName=_year,
        valueColumnName=_value,
    )
    return unpivoted.select(
        F.col("Country Code").alias(_country_code),
        F.col("Country Name").alias(_country),
        F.col(_year).cast("int"),
        F.col("Indicator Name").alias(_indicator),
        F.col(_value).cast("double"),
        F.lit(SOURCE_WDI).alias(_source),
    )


def pivot_wide(df: DataFrame) -> DataFrame:
    return (
        df.groupBy(_country_code, _country, _year, _source)
        .pivot(_indicator)
        .agg(F.first(_value))
    )


def unpivot_all(wide: DataFrame) -> DataFrame:
    value_cols = [c for c in wide.columns if c not in _ID_COLS]
    stack_expr = "stack({n}, {pairs}) as (indicator, value)".format(
        n=len(value_cols),
        pairs=", ".join([f"'{c}', `{c}`" for c in value_cols]),
    )
    return wide.select(_country_code, _country, _year, F.expr(stack_expr), _source)
