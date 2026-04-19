from pyspark.sql import SparkSession, DataFrame

from src.processing.MACRO.macro_valid.macro_filter import filter_by_area, filter_by_year, filter_by_item
from src.processing.MACRO.macro_valid.macro_validate import validate_all
from src.processing.MACRO.macro_transform.macro_reshape import pivot_to_wide, unpivot_all
from src.processing.MACRO.macro_feature.macro_feature import compute_macro_features
from src.utils.logger import get_logger

log = get_logger("processing.macro")


def load_macro(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.csv(path, header=True, inferSchema=False)


def process_macro(spark: SparkSession, path: str) -> DataFrame:
    try:
        log.info("MACRO | start | path=%s", path)

        raw      = load_macro(spark, path)
        log.info("MACRO | loaded | rows=%d", raw.count())

        filtered = filter_by_area(raw)
        filtered = filter_by_year(filtered)
        filtered = filter_by_item(filtered)
        log.info("MACRO | filtered | rows=%d", filtered.count())

        wide     = pivot_to_wide(filtered)
        log.info("MACRO | pivoted to wide")

        featured  = compute_macro_features(wide)
        log.info("MACRO | features computed")

        validated = validate_all(featured)
        log.info("MACRO | validated | rows=%d", validated.count())

        result = unpivot_all(validated)
        log.info("MACRO | done | output_rows=%d", result.count())
        return result

    except Exception as e:
        log.error("MACRO | failed | error=%s", e, exc_info=True)
        raise
