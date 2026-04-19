from pyspark.sql import SparkSession, DataFrame

from src.processing.WDI.wdi_valid.wdi_filter import filter_by_country, filter_by_indicator
from src.processing.WDI.wdi_valid.wdi_validate import validate_all
from src.processing.WDI.wdi_transform.wdi_reshape import flatten_years, unpivot_all
from src.processing.WDI.wdi_transform.wdi_clean import map_indicator_codes
from src.processing.WDI.wdi_feature.wdi_feature import compute_wdi_features
from src.utils.logger import get_logger

log = get_logger("processing.wdi")


def load_wdi(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.csv(path, header=True, inferSchema=False)


def process_wdi(spark: SparkSession, path: str) -> DataFrame:
    try:
        log.info("WDI | start | path=%s", path)

        raw      = load_wdi(spark, path)
        log.info("WDI | loaded | rows=%d", raw.count())

        filtered = filter_by_country(raw)
        filtered = filter_by_indicator(filtered)
        log.info("WDI | filtered | rows=%d", filtered.count())

        normalized = flatten_years(filtered)
        mapped     = map_indicator_codes(normalized)

        featured  = compute_wdi_features(mapped)
        log.info("WDI | features computed")

        validated = validate_all(featured)
        log.info("WDI | validated | rows=%d", validated.count())

        result = unpivot_all(validated)
        log.info("WDI | done | output_rows=%d", result.count())
        return result

    except Exception as e:
        log.error("WDI | failed | error=%s", e, exc_info=True)
        raise
