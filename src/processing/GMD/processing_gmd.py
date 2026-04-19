from pyspark.sql import SparkSession, DataFrame

from src.processing.GMD.gmd_valid.gmd_filter import filter_by_country, filter_by_year
from src.processing.GMD.gmd_valid.gmd_validate import validate_all
from src.processing.GMD.gmd_transform.gmd_reshape import select_and_rename, unpivot_all
from src.processing.GMD.gmd_feature.gmd_feature import compute_gmd_features
from src.utils.logger import get_logger

log = get_logger("processing.gmd")


def load_gmd(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.csv(path, header=True, inferSchema=False)


def process_gmd(spark: SparkSession, path: str) -> DataFrame:
    try:
        log.info("GMD | start | path=%s", path)

        raw      = load_gmd(spark, path)
        log.info("GMD | loaded | rows=%d", raw.count())

        filtered = filter_by_country(raw)
        filtered = filter_by_year(filtered)
        log.info("GMD | filtered | rows=%d", filtered.count())

        renamed  = select_and_rename(filtered)

        featured  = compute_gmd_features(renamed)
        log.info("GMD | features computed")

        validated = validate_all(featured)
        log.info("GMD | validated | rows=%d", validated.count())

        result = unpivot_all(validated)
        log.info("GMD | done | output_rows=%d", result.count())
        return result

    except Exception as e:
        log.error("GMD | failed | error=%s", e, exc_info=True)
        raise
