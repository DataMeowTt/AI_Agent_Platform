import traceback

from src.core.config import get_runtime_metadata
from src.core.logger import logger
from src.generated.indicator_contract import (
    CLUSTER_TARGET_YEARS,
    TABLES_INDICATORS,
)


def _build_indicator_tasks(table: str | None = None, indicator: str | None = None) -> list[dict]:
    tasks = []

    for table_name, indicators in TABLES_INDICATORS.items():
        if table and table_name != table:
            continue

        for indicator_code in indicators:
            if indicator and indicator_code != indicator:
                continue
            tasks.append({"table": table_name, "indicator": indicator_code})

    return tasks


def _build_summary(
    dry_run: bool,
    target: str,
    metadata: dict[str, str],
    indicator_tasks: list[dict],
    cluster_years: list[int],
    skip_clusters: bool,
) -> dict:
    return {
        "target": target,
        "dry_run": dry_run,
        "metadata": metadata,
        "planned": {
            "indicator_tasks": len(indicator_tasks),
            "cluster_tasks": 0 if skip_clusters else len(cluster_years),
        },
        "executed": {
            "indicator_tasks": 0,
            "cluster_tasks": 0,
        },
        "skipped": {
            "indicator_tasks": 0,
            "cluster_tasks": len(cluster_years) if skip_clusters else 0,
        },
        "errors": [],
    }


def run_all_analytics(
    target: str = "postgres",
    dry_run: bool = False,
    table: str | None = None,
    indicator: str | None = None,
    skip_clusters: bool = False,
    cluster_years: list[int] | None = None,
    n_clusters: int = 5,
    runtime_metadata: dict[str, str] | None = None,
) -> dict:
    if target != "postgres":
        raise ValueError(f"Unsupported analytics target: {target}")

    if table and table not in TABLES_INDICATORS:
        raise ValueError(f"Unknown analytics source table: {table}")

    if indicator and not any(indicator in indicators for indicators in TABLES_INDICATORS.values()):
        raise ValueError(f"Unknown analytics indicator: {indicator}")

    indicator_tasks = _build_indicator_tasks(table=table, indicator=indicator)
    selected_cluster_years = list(cluster_years or CLUSTER_TARGET_YEARS)
    metadata = runtime_metadata or get_runtime_metadata()
    summary = _build_summary(
        dry_run=dry_run,
        target=target,
        metadata=metadata,
        indicator_tasks=indicator_tasks,
        cluster_years=selected_cluster_years,
        skip_clusters=skip_clusters,
    )

    logger.info(
        "Starting analytics batch: target=%s dry_run=%s indicator_tasks=%s cluster_tasks=%s",
        target,
        dry_run,
        len(indicator_tasks),
        0 if skip_clusters else len(selected_cluster_years),
    )

    if dry_run:
        summary["planned_tasks"] = {
            "indicators": indicator_tasks,
            "clusters": [] if skip_clusters else selected_cluster_years,
        }
        logger.info("Analytics dry-run completed without database access")
        return summary

    import pandas as pd

    from src.pipelines.anomaly import update_anomaly_scores
    from src.pipelines.cluster import run_clustering
    from src.pipelines.trend import compute_trend_for_indicator, save_trends_to_analytics

    for task in indicator_tasks:
        table_name = task["table"]
        indicator_code = task["indicator"]
        logger.info(f"Batch Processing: {indicator_code} in {table_name}")
        try:
            results = compute_trend_for_indicator(table_name, indicator_code)
            if results:
                df = pd.DataFrame(results)
                save_trends_to_analytics(table_name, indicator_code, df, runtime_metadata=metadata)
                update_anomaly_scores(table_name, indicator_code, runtime_metadata=metadata)
            else:
                summary["skipped"]["indicator_tasks"] += 1
            summary["executed"]["indicator_tasks"] += 1
        except Exception as e:
            error = {
                "kind": "indicator",
                "table": table_name,
                "indicator": indicator_code,
                "error": str(e),
            }
            summary["errors"].append(error)
            logger.error(f"Error processing {indicator_code} in {table_name}: {traceback.format_exc()}")

    if not skip_clusters:
        for year in selected_cluster_years:
            logger.info(f"Batch Processing Clustering for year {year}")
            try:
                run_clustering(target_year=year, n_clusters=n_clusters, runtime_metadata=metadata)
                summary["executed"]["cluster_tasks"] += 1
            except Exception as e:
                error = {
                    "kind": "cluster",
                    "year": year,
                    "error": str(e),
                }
                summary["errors"].append(error)
                logger.error(f"Error processing clustering for {year}: {traceback.format_exc()}")

    logger.info("Full Analytics Batch Process Completed")
    return summary
