from pyspark.sql import SparkSession, DataFrame

from src.processing.WDI.processing_wdi import process_wdi
from src.processing.GMD.processing_gmd import process_gmd
from src.processing.MACRO.processing_macro import process_macro
from src.utils.logger import get_logger

log = get_logger("processing.job")

_RAW_DIR       = "/opt/dataset"
_PROCESSED_DIR = "/opt/workspace/data/processed_data"

_WDI_INPUT   = f"{_RAW_DIR}/WDICSV.csv"
_GMD_INPUT   = f"{_RAW_DIR}/GMD.csv"
_MACRO_INPUT = f"{_RAW_DIR}/Macro.csv"

_WDI_OUTPUT   = f"{_PROCESSED_DIR}/WDI_processed.csv"
_GMD_OUTPUT   = f"{_PROCESSED_DIR}/GMD_processed.csv"
_MACRO_OUTPUT = f"{_PROCESSED_DIR}/MACRO_processed.csv"
_UNION_OUTPUT = f"{_PROCESSED_DIR}/processed.csv"


def _save(df: DataFrame, path: str) -> None:
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(path)
    log.info("JOB | saved | path=%s", path)


def run(spark: SparkSession) -> None:
    log.info("JOB | ===== pipeline start =====")
    try:
        wdi   = process_wdi(spark,   _WDI_INPUT)
        macro = process_macro(spark, _MACRO_INPUT)
        gmd   = process_gmd(spark,   _GMD_INPUT)

        _save(wdi,   _WDI_OUTPUT)
        _save(macro, _MACRO_OUTPUT)
        _save(gmd,   _GMD_OUTPUT)

        log.info("JOB | building union")
        union = wdi.union(macro).union(gmd).orderBy("country", "year")
        _save(union, _UNION_OUTPUT)

        log.info("JOB | ===== pipeline done =====")

    except Exception as e:
        log.error("JOB | pipeline failed | error=%s", e, exc_info=True)
        raise
