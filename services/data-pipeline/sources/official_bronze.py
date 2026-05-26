from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_runtime_source_path(runtime_raw_dir: Path, source_runtime_path: str, source_name: str) -> Path:
    runtime_root = runtime_raw_dir.expanduser().resolve()
    candidate = Path(source_runtime_path).expanduser().resolve()
    try:
        candidate.relative_to(runtime_root)
    except ValueError as exc:
        raise ValueError(
            f"Official runtime path for {source_name!r} must stay under runtime raw dir: {runtime_root}"
        ) from exc
    if not candidate.exists() or not candidate.is_dir():
        raise FileNotFoundError(f"Official runtime path for {source_name!r} not found: {candidate}")
    return candidate


def _copy_runtime_files(*, runtime_source_dir: Path, bronze_source_dir: Path, present_files: list[str]) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    files_dir = bronze_source_dir / "files"
    for rel_name in sorted(present_files):
        source_path = runtime_source_dir / rel_name
        if not source_path.exists() or not source_path.is_file():
            continue
        destination = files_dir / rel_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        copied.append(
            {
                "file_name": source_path.name,
                "relative_path": destination.relative_to(bronze_source_dir).as_posix(),
                "absolute_path": str(destination.resolve()),
                "size_bytes": int(destination.stat().st_size),
            }
        )
    return copied


def _validate_official_entry(entry: dict[str, Any]) -> None:
    source_name = str(entry.get("source_name") or "").strip()
    if not source_name:
        raise ValueError("Official acquisition entry is missing source_name.")
    if str(entry.get("validation_status") or "").strip().lower() != "valid":
        raise ValueError(f"Official acquisition entry for {source_name!r} is not valid.")
    fingerprint = str(entry.get("combined_fingerprint") or "").strip()
    if not fingerprint:
        raise ValueError(f"Official acquisition entry for {source_name!r} is missing combined_fingerprint.")
    runtime_path = str(entry.get("runtime_materialized_path") or "").strip()
    if not runtime_path:
        raise ValueError(f"Official acquisition entry for {source_name!r} is missing runtime_materialized_path.")


def materialize_official_bronze_snapshot(
    *,
    acquisition_manifest: dict[str, Any],
    runtime_raw_dir: str | Path,
    output_dir: str | Path,
    run_id: str,
    run_date: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    runtime_root = Path(runtime_raw_dir).expanduser().resolve()
    output_root = Path(output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    bronze_root = output_root / "bronze"
    manifest_generated_at = generated_at or _utc_now_iso()

    source_records: list[dict[str, Any]] = []
    for entry in list(acquisition_manifest.get("sources") or []):
        if not isinstance(entry, dict):
            continue
        _validate_official_entry(entry)
        source_name = str(entry["source_name"]).strip()
        runtime_source_dir = _validate_runtime_source_path(runtime_root, str(entry["runtime_materialized_path"]), source_name)
        bronze_source_dir = bronze_root / source_name / f"run_date={run_date}"
        bronze_source_dir.mkdir(parents=True, exist_ok=True)

        present_files = [str(item) for item in list(entry.get("present_files") or [])]
        copied_files = _copy_runtime_files(
            runtime_source_dir=runtime_source_dir,
            bronze_source_dir=bronze_source_dir,
            present_files=present_files,
        )
        if not copied_files:
            raise ValueError(f"No official runtime files were copied for source {source_name!r}.")

        total_bytes = int(sum(item["size_bytes"] for item in copied_files))
        source_records.append(
            {
                "source_name": source_name,
                "source_type": "official_runtime",
                "run_id": run_id,
                "run_date": run_date,
                "status": "ingested",
                "discovery_status": "present",
                "sha256": None,
                "size_bytes": total_bytes,
                "total_bytes": total_bytes,
                "file_count": len(copied_files),
                "combined_sha256": entry.get("combined_fingerprint"),
                "snapshot_uri": str(bronze_source_dir.resolve()),
                "license_note": entry.get("license_note"),
                "missing_inputs": [],
                "files": copied_files,
                "main_file_metadata": {
                    "row_count": entry.get("main_file_row_count"),
                    "schema_signature": entry.get("main_file_schema_signature"),
                },
                "skipped": False,
                "force": False,
                "output_format": "official_runtime",
                "source_hash": entry.get("combined_fingerprint"),
                "input_kind": "official_runtime",
                "payload_path": str((bronze_source_dir / "files").resolve()),
                "metadata_path": None,
                "is_test_fixture": False,
                "official_reference": entry.get("official_reference"),
                "upstream_dataset_code": entry.get("upstream_dataset_code"),
                "upstream_dataset_name": entry.get("upstream_dataset_name"),
                "upstream_version": entry.get("upstream_version"),
                "upstream_update_date": entry.get("upstream_update_date"),
                "upstream_file_location_or_package_identifier": entry.get(
                    "upstream_file_location_or_package_identifier"
                ),
                "combined_fingerprint": entry.get("combined_fingerprint"),
                "file_hashes": entry.get("file_hashes"),
                "file_sizes": entry.get("file_sizes"),
            }
        )

    source_manifest = {
        "manifest_type": "source_manifest",
        "manifest_version": 1,
        "run_id": run_id,
        "run_date": run_date,
        "generated_at": manifest_generated_at,
        "status": "ok",
        "dry_run": False,
        "force": False,
        "registry_path": "official_runtime_materialized",
        "output_dir": str(output_root),
        "source_count": len(source_records),
        "ingested_count": len(source_records),
        "skipped_count": 0,
        "missing_count": 0,
        "planned_count": 0,
        "sources": source_records,
    }
    source_manifest_path = output_root / "source_manifest.json"
    source_manifest["manifest_path"] = str(source_manifest_path.resolve())

    pipeline_manifest = {
        "manifest_type": "pipeline_manifest",
        "manifest_version": 1,
        "run_id": run_id,
        "run_date": run_date,
        "generated_at": manifest_generated_at,
        "status": "ok",
        "dry_run": False,
        "force": False,
        "output_dir": str(output_root),
        "source_manifest_path": str(source_manifest_path.resolve()),
        "source_count": len(source_records),
        "ingested_count": len(source_records),
        "skipped_count": 0,
        "missing_count": 0,
        "planned_count": 0,
        "layout": {
            "bronze": {
                record["source_name"]: record["snapshot_uri"]
                for record in source_records
            },
            "source_manifest": str(source_manifest_path.resolve()),
            "pipeline_manifest": str((output_root / "pipeline_manifest.json").resolve()),
        },
        "sources": [
            {
                "source_name": record["source_name"],
                "status": record["status"],
                "discovery_status": record["discovery_status"],
                "source_type": record["source_type"],
                "sha256": record["sha256"],
                "size_bytes": record["size_bytes"],
                "total_bytes": record["total_bytes"],
                "file_count": record["file_count"],
                "combined_sha256": record["combined_sha256"],
                "snapshot_uri": record["snapshot_uri"],
                "skipped": record["skipped"],
                "force": record["force"],
            }
            for record in source_records
        ],
    }
    pipeline_manifest_path = output_root / "pipeline_manifest.json"
    pipeline_manifest["manifest_path"] = str(pipeline_manifest_path.resolve())

    _write_json(source_manifest_path, source_manifest)
    _write_json(pipeline_manifest_path, pipeline_manifest)
    return {
        "source_manifest": source_manifest,
        "pipeline_manifest": pipeline_manifest,
        "source_manifest_path": str(source_manifest_path.resolve()),
        "pipeline_manifest_path": str(pipeline_manifest_path.resolve()),
        "bronze_output_dir": str(bronze_root.resolve()),
    }
