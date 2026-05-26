from __future__ import annotations

import json
from pathlib import Path

import pytest

from sources.official_bronze import materialize_official_bronze_snapshot


def _prepare_runtime_tree(tmp_path: Path) -> Path:
    runtime_raw = tmp_path / "runtime" / "raw"
    (runtime_raw / "worldBank").mkdir(parents=True, exist_ok=True)
    (runtime_raw / "gmd").mkdir(parents=True, exist_ok=True)
    (runtime_raw / "Macro-Statistics_Key_Indicators_E_All_Data_(Normalized)").mkdir(parents=True, exist_ok=True)
    (runtime_raw / "worldBank" / "WDICSV.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (runtime_raw / "gmd" / "GMD.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (runtime_raw / "Macro-Statistics_Key_Indicators_E_All_Data_(Normalized)" / "Macro-Statistics_Key_Indicators_E_All_Data_(Normalized).csv").write_text(
        "a,b\n1,2\n",
        encoding="utf-8",
    )
    return runtime_raw


def _manifest(runtime_raw: Path) -> dict:
    return {
        "run_id": "r1",
        "run_date": "2026-05-24",
        "status": "valid",
        "sources": [
            {
                "source_name": "wdi",
                "validation_status": "valid",
                "runtime_materialized_path": str((runtime_raw / "worldBank").resolve()),
                "present_files": ["WDICSV.csv"],
                "combined_fingerprint": "fp-wdi",
                "main_file_row_count": 1,
                "main_file_schema_signature": "sig-wdi",
            },
            {
                "source_name": "gmd",
                "validation_status": "valid",
                "runtime_materialized_path": str((runtime_raw / "gmd").resolve()),
                "present_files": ["GMD.csv"],
                "combined_fingerprint": "fp-gmd",
                "main_file_row_count": 1,
                "main_file_schema_signature": "sig-gmd",
            },
        ],
    }


def test_materialize_official_bronze_snapshot_writes_layout(tmp_path: Path) -> None:
    runtime_raw = _prepare_runtime_tree(tmp_path)
    payload = materialize_official_bronze_snapshot(
        acquisition_manifest=_manifest(runtime_raw),
        runtime_raw_dir=runtime_raw,
        output_dir=tmp_path / "out",
        run_id="r1",
        run_date="2026-05-24",
    )

    source_manifest_path = Path(payload["source_manifest_path"])
    pipeline_manifest_path = Path(payload["pipeline_manifest_path"])
    assert source_manifest_path.exists()
    assert pipeline_manifest_path.exists()
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    assert source_manifest["source_count"] == 2
    assert {item["source_name"] for item in source_manifest["sources"]} == {"wdi", "gmd"}
    assert source_manifest["sources"][0]["combined_sha256"] in {"fp-wdi", "fp-gmd"}


def test_materialize_official_bronze_rejects_paths_outside_runtime_raw(tmp_path: Path) -> None:
    runtime_raw = _prepare_runtime_tree(tmp_path)
    unsafe_manifest = _manifest(runtime_raw)
    unsafe_manifest["sources"][0]["runtime_materialized_path"] = str((tmp_path / "elsewhere").resolve())

    with pytest.raises(ValueError, match="must stay under runtime raw dir"):
        materialize_official_bronze_snapshot(
            acquisition_manifest=unsafe_manifest,
            runtime_raw_dir=runtime_raw,
            output_dir=tmp_path / "out",
            run_id="r1",
            run_date="2026-05-24",
        )
