from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ops.source_fingerprint import load_baseline_manifest
from sources.gcs_runtime_client import read_gcs_object_text


DEFAULT_METADATA_TABLE = "gov_ai_ops.pipeline_run_metadata"


def _parse_utc_timestamp(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_valid_success_row(row: dict[str, Any]) -> bool:
    if str(row.get("status") or "").strip().upper() != "SUCCESS":
        return False
    if row.get("warehouse_publish_performed") is not True:
        return False
    if row.get("publish_performed") is not True:
        return False
    if row.get("last_successful_updated") is not True:
        return False
    if _parse_utc_timestamp(str(row.get("published_at") or "")) is None:
        return False
    candidate_source_manifest_path = str(row.get("candidate_source_manifest_path") or "").strip()
    return candidate_source_manifest_path.startswith("gs://")


def read_latest_success_metadata_rows(
    *,
    project_id: str,
    table_id: str | None = None,
    row_limit: int = 500,
    client_factory: Callable[[str], Any] | None = None,
) -> list[dict[str, Any]]:
    resolved_table_id = str(table_id or f"{project_id}.{DEFAULT_METADATA_TABLE}").strip()
    if "." not in resolved_table_id:
        raise ValueError(f"Invalid metadata table id: {resolved_table_id!r}")

    if client_factory is None:
        from google.cloud import bigquery

        client = bigquery.Client(project=project_id)
    else:
        client = client_factory(project_id)

    query = (
        "SELECT run_id, status, warehouse_publish_performed, publish_performed, "
        "last_successful_updated, published_at, candidate_source_manifest_path, baseline_success_manifest_path "
        f"FROM `{resolved_table_id}` "
        "WHERE status = 'SUCCESS' "
        "ORDER BY published_at DESC, run_id DESC "
        f"LIMIT {int(row_limit)}"
    )
    job = client.query(query)
    return [dict(row.items()) for row in job.result()]


def fetch_manifest_text_from_gcs(manifest_uri: str) -> str:
    return read_gcs_object_text(source_gcs_uri=manifest_uri)


def select_latest_success_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    valid_rows = [row for row in rows if isinstance(row, dict) and is_valid_success_row(row)]
    if not valid_rows:
        return None

    def sort_key(row: dict[str, Any]) -> tuple[datetime, str]:
        published_at = _parse_utc_timestamp(str(row.get("published_at") or "")) or datetime(1970, 1, 1, tzinfo=timezone.utc)
        run_id = str(row.get("run_id") or "")
        return (published_at, run_id)

    return sorted(valid_rows, key=sort_key, reverse=True)[0]


def _ensure_valid_local_manifest(path: Path) -> tuple[bool, str | None]:
    _, error = load_baseline_manifest(str(path))
    return error is None, error


def resolve_baseline_manifest_for_run(
    *,
    runtime_dir: str | Path,
    explicit_baseline_path: str | None = None,
    metadata_rows: list[dict[str, Any]] | None = None,
    metadata_reader: Callable[[], list[dict[str, Any]]] | None = None,
    manifest_fetcher: Callable[[str], str | bytes] | None = None,
) -> dict[str, Any]:
    runtime_root = Path(runtime_dir).expanduser().resolve()
    runtime_root.mkdir(parents=True, exist_ok=True)

    if explicit_baseline_path:
        baseline_path = Path(explicit_baseline_path).expanduser().resolve()
        if not baseline_path.exists():
            return {
                "status": "BASELINE_INVALID",
                "reason": "baseline_file_not_found",
                "baseline_path": str(baseline_path),
                "baseline_source_uri": str(baseline_path),
            }
        is_valid, error = _ensure_valid_local_manifest(baseline_path)
        if not is_valid:
            return {
                "status": "BASELINE_INVALID",
                "reason": str(error or "baseline_manifest_invalid"),
                "baseline_path": str(baseline_path),
                "baseline_source_uri": str(baseline_path),
            }
        return {
            "status": "BASELINE_READY",
            "reason": "explicit_baseline_path",
            "baseline_path": str(baseline_path),
            "baseline_source_uri": str(baseline_path),
            "resolved_from_success_run_id": None,
        }

    rows = list(metadata_rows or [])
    if not rows and metadata_reader is not None:
        rows = list(metadata_reader())
    latest_success = select_latest_success_row(rows)
    if latest_success is None:
        return {
            "status": "NO_BASELINE",
            "reason": "no_success_metadata",
            "baseline_path": None,
            "baseline_source_uri": None,
            "resolved_from_success_run_id": None,
        }

    manifest_uri = str(latest_success.get("candidate_source_manifest_path") or "").strip()
    if not manifest_uri:
        return {
            "status": "BASELINE_INVALID",
            "reason": "missing_candidate_source_manifest_path",
            "baseline_path": None,
            "baseline_source_uri": None,
            "resolved_from_success_run_id": str(latest_success.get("run_id") or ""),
        }
    if manifest_fetcher is None:
        return {
            "status": "BASELINE_INVALID",
            "reason": "baseline_fetcher_not_configured",
            "baseline_path": None,
            "baseline_source_uri": manifest_uri,
            "resolved_from_success_run_id": str(latest_success.get("run_id") or ""),
        }

    raw_manifest = manifest_fetcher(manifest_uri)
    local_path = runtime_root / "baseline_success_manifest.json"
    if isinstance(raw_manifest, bytes):
        payload_text = raw_manifest.decode("utf-8")
    else:
        payload_text = str(raw_manifest)
    local_path.write_text(payload_text, encoding="utf-8")

    is_valid, error = _ensure_valid_local_manifest(local_path)
    if not is_valid:
        return {
            "status": "BASELINE_INVALID",
            "reason": str(error or "baseline_manifest_invalid"),
            "baseline_path": str(local_path),
            "baseline_source_uri": manifest_uri,
            "resolved_from_success_run_id": str(latest_success.get("run_id") or ""),
        }

    parsed = json.loads(local_path.read_text(encoding="utf-8"))
    return {
        "status": "BASELINE_READY",
        "reason": "latest_success_metadata",
        "baseline_path": str(local_path),
        "baseline_source_uri": manifest_uri,
        "resolved_from_success_run_id": str(latest_success.get("run_id") or ""),
        "baseline_manifest": parsed,
    }
