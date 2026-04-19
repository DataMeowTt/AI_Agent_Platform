from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from processing.schema.processed_schema import PROCESSED_SCHEMA, SOURCE_GMD
from src.processing.GMD.gmd_transform.gmd_clean import NUMERIC_COLS, STRING_COLS

_cc, _c, _y, _, _, _src = PROCESSED_SCHEMA.fieldNames()

_ID_COLS    = frozenset({_cc, _c, _y, _src})
_HELPER_COLS = frozenset({"reer", "hcons_usd", "income_group"})


def select_and_rename(df: DataFrame) -> DataFrame:
    raw_cols = (
        ["countryname", "ISO3", "year"]
        + list(NUMERIC_COLS.keys())
        + list(STRING_COLS.keys())
    )
    df = df.select(*raw_cols)

    for raw, clean in NUMERIC_COLS.items():
        df = df.withColumnRenamed(raw, clean).withColumn(clean, F.col(clean).cast("double"))

    return (
        df
        .withColumnRenamed("countryname", _c)
        .withColumnRenamed("ISO3", _cc)
        .withColumn(_y, F.col("year").cast("int"))
        .withColumn(_src, F.lit(SOURCE_GMD))
    )


def unpivot_all(df: DataFrame) -> DataFrame:
    skip = _ID_COLS | _HELPER_COLS
    value_cols = [c for c in df.columns if c not in skip]
    df = df.drop(*_HELPER_COLS)
    stack_expr = "stack({n}, {pairs}) as (indicator, value)".format(
        n=len(value_cols),
        pairs=", ".join([f"'{c}', `{c}`" for c in value_cols]),
    )
    return df.select(_cc, _c, _y, F.expr(stack_expr), _src)
