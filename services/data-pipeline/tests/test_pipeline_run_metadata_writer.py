from __future__ import annotations

from typing import Any

import pytest

from ops.pipeline_run_metadata_writer import append_pipeline_run_metadata_row


def _valid_record() -> dict[str, Any]:
    return {
        "run_id": "run-1",
        "run_date": "2026-05-24",
        "execution_mode": "execute",
        "status": "SUCCESS",
        "source_changed": True,
        "change_reason": "candidate_differs_from_last_successful_baseline",
        "candidate_source_manifest_path": "gs://bucket/manifests/source_manifest/run_date=2026-05-24/source_manifest.json",
        "baseline_success_manifest_path": None,
        "warehouse_publish_performed": True,
        "publish_performed": True,
        "last_successful_updated": True,
        "published_at": "2026-05-24T02:10:00Z",
        "latest_data_year": 2025,
        "sources_json": '[{"source_name":"wdi"}]',
    }


def test_append_rejects_invalid_payload_before_write() -> None:
    record = _valid_record()
    record["publish_performed"] = False
    writes: list[dict[str, Any]] = []

    def fake_appender(*, table_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        writes.append({"table_id": table_id, "rows": rows})
        return {"ok": True}

    with pytest.raises(ValueError, match="validation failed"):
        append_pipeline_run_metadata_row(
            row=record,
            project_id="western-pivot-452008-a6",
            env_getter=lambda _: "true",
            row_appender=fake_appender,
        )
    assert writes == []


def test_append_writes_one_row_after_validation() -> None:
    record = _valid_record()
    writes: list[dict[str, Any]] = []

    def fake_appender(*, table_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        writes.append({"table_id": table_id, "rows": rows})
        return {"table_id": table_id, "inserted_row_count": len(rows)}

    payload = append_pipeline_run_metadata_row(
        row=record,
        project_id="western-pivot-452008-a6",
        env_getter=lambda _: "true",
        row_appender=fake_appender,
    )

    assert payload["validation"]["status"] == "passed"
    assert len(writes) == 1
    assert writes[0]["table_id"] == "western-pivot-452008-a6.gov_ai_ops.pipeline_run_metadata"
    assert len(writes[0]["rows"]) == 1


@pytest.mark.parametrize(
    ("candidate_source_manifest_path", "drop_field"),
    [
        (None, True),
        ("   ", False),
        ("/tmp/source_manifest.json", False),
        ("https://example.com/source_manifest.json", False),
    ],
)
def test_append_rejects_invalid_success_candidate_source_manifest_path(
    candidate_source_manifest_path: str | None, drop_field: bool
) -> None:
    record = _valid_record()
    writes: list[dict[str, Any]] = []

    if drop_field:
        record.pop("candidate_source_manifest_path")
    else:
        record["candidate_source_manifest_path"] = candidate_source_manifest_path

    def fake_appender(*, table_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        writes.append({"table_id": table_id, "rows": rows})
        return {"ok": True}

    with pytest.raises(ValueError, match="validation failed"):
        append_pipeline_run_metadata_row(
            row=record,
            project_id="western-pivot-452008-a6",
            env_getter=lambda _: "true",
            row_appender=fake_appender,
        )
    assert writes == []
