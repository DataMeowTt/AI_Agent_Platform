from datetime import datetime, timezone

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from config.settings import settings
from pipeline.gmd.pipeline import process_gmd
from pipeline.macro.pipeline import process_macro
from pipeline.wdi.pipeline import process_wdi
from utils.io_paths import build_silver_output_uris
from utils.logger import get_logger

log = get_logger("pipeline.job")

_RAW_DIR = "/opt/dataset"

_WDI_INPUT = f"{_RAW_DIR}/WDICSV.csv"
_GMD_INPUT = f"{_RAW_DIR}/GMD.csv"
_MACRO_INPUT = f"{_RAW_DIR}/Macro.csv"


def _loaded_at_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _add_metadata(df: DataFrame, loaded_at: str) -> DataFrame:
    return (
        df
        .withColumn("run_id", F.lit(settings.run_id))
        .withColumn("run_date", F.lit(settings.run_date).cast("date"))
        .withColumn("loaded_at", F.lit(loaded_at).cast("timestamp"))
    )


def _save(df: DataFrame, path: str, output_format: str) -> None:
    if output_format == "csv":
        df.coalesce(1).write.mode("overwrite").option("header", True).csv(path)
    elif output_format == "parquet":
        df.write.mode("overwrite").parquet(path)
    else:
        raise ValueError(f"Unsupported output format: {output_format!r}")

    log.info("JOB | saved | format=%s | path=%s", output_format, path)


def run(spark: SparkSession) -> None:
    output_format = settings.output_format
    output_uris = build_silver_output_uris(settings.silver_output_uri)
    loaded_at = _loaded_at_utc()

    log.info("JOB | ===== pipeline start =====")
    log.info(
        "JOB | output configured | format=%s | silver_output_uri=%s | run_id=%s | run_date=%s",
        output_format,
        settings.silver_output_uri,
        settings.run_id,
        settings.run_date,
    )

    try:
        wdi = _add_metadata(process_wdi(spark, _WDI_INPUT), loaded_at)
        macro = _add_metadata(process_macro(spark, _MACRO_INPUT), loaded_at)
        gmd = _add_metadata(process_gmd(spark, _GMD_INPUT), loaded_at)

        _save(wdi, output_uris["wdi"], output_format)
        _save(macro, output_uris["macro"], output_format)
        _save(gmd, output_uris["gmd"], output_format)

        log.info("JOB | building union")
        union = wdi.unionByName(macro).unionByName(gmd).orderBy("country", "year")
        _save(union, output_uris["union"], output_format)

        log.info("JOB | ===== pipeline done =====")

    except Exception as e:
        log.error("JOB | pipeline failed | error=%s", e, exc_info=True)
        raise