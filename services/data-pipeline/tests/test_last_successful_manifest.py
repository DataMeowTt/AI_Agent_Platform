from __future__ import annotations

import json
from pathlib import Path

from ops.last_successful_manifest import resolve_baseline_manifest_for_run, select_latest_success_row


def _success_row(*, run_id: str, published_at: str, manifest_uri: str, baseline_uri: str | None = None) -> dict:
    return {
        "run_id": run_id,
        "status": "SUCCESS",
        "warehouse_publish_performed": True,
        "publish_performed": True,
        "last_successful_updated": True,
        "published_at": published_at,
        "candidate_source_manifest_path": manifest_uri,
        "baseline_success_manifest_path": baseline_uri,
    }


def _manifest_payload(fingerprint: str) -> dict:
    return {
        "run_id": "r1",
        "run_date": "2026-05-24",
        "status": "valid",
        "sources": [{"source_name": "wdi", "combined_fingerprint": fingerprint}],
    }


def test_select_latest_success_row_is_deterministic() -> None:
    rows = [
        _success_row(
            run_id="run-a",
            published_at="2026-05-24T01:00:00Z",
            manifest_uri="gs://bucket/a.json",
        ),
        _success_row(
            run_id="run-b",
            published_at="2026-05-24T01:00:00Z",
            manifest_uri="gs://bucket/b.json",
        ),
    ]
    picked = select_latest_success_row(rows)
    assert picked is not None
    assert picked["run_id"] == "run-b"


def test_resolver_uses_candidate_source_manifest_path_not_baseline_field(tmp_path: Path) -> None:
    rows = [
        _success_row(
            run_id="run-older",
            published_at="2026-05-24T00:00:00Z",
            manifest_uri="gs://bucket/older.json",
        ),
        _success_row(
            run_id="run-latest",
            published_at="2026-05-24T02:00:00Z",
            manifest_uri="gs://bucket/latest.json",
            baseline_uri="gs://bucket/should-not-be-used.json",
        ),
    ]
    fetch_calls: list[str] = []

    def fetch(uri: str) -> str:
        fetch_calls.append(uri)
        return json.dumps(_manifest_payload("fp-latest"))

    payload = resolve_baseline_manifest_for_run(
        runtime_dir=tmp_path / "runtime",
        metadata_rows=rows,
        manifest_fetcher=fetch,
    )

    assert payload["status"] == "BASELINE_READY"
    assert payload["baseline_source_uri"] == "gs://bucket/latest.json"
    assert fetch_calls == ["gs://bucket/latest.json"]


def test_resolver_uses_metadata_reader_when_rows_not_provided(tmp_path: Path) -> None:
    rows = [
        _success_row(
            run_id="run-latest",
            published_at="2026-05-24T02:00:00Z",
            manifest_uri="gs://bucket/latest.json",
        )
    ]
    reads = {"metadata": 0}

    payload = resolve_baseline_manifest_for_run(
        runtime_dir=tmp_path / "runtime",
        metadata_reader=lambda: (reads.__setitem__("metadata", reads["metadata"] + 1) or rows),
        manifest_fetcher=lambda _: json.dumps(_manifest_payload("fp-latest")),
    )

    assert payload["status"] == "BASELINE_READY"
    assert reads["metadata"] == 1


def test_resolver_returns_baseline_invalid_for_malformed_manifest(tmp_path: Path) -> None:
    rows = [
        _success_row(
            run_id="run-latest",
            published_at="2026-05-24T02:00:00Z",
            manifest_uri="gs://bucket/latest.json",
        )
    ]

    payload = resolve_baseline_manifest_for_run(
        runtime_dir=tmp_path / "runtime",
        metadata_rows=rows,
        manifest_fetcher=lambda _: json.dumps({"bad": "shape"}),
    )
    assert payload["status"] == "BASELINE_INVALID"


def test_resolver_explicit_baseline_path_first_run_behavior(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(_manifest_payload("fp-explicit")), encoding="utf-8")
    payload = resolve_baseline_manifest_for_run(
        runtime_dir=tmp_path / "runtime",
        explicit_baseline_path=str(baseline_path),
    )

    assert payload["status"] == "BASELINE_READY"
    assert payload["baseline_path"] == str(baseline_path.resolve())


def test_resolver_no_prior_success_returns_no_baseline(tmp_path: Path) -> None:
    payload = resolve_baseline_manifest_for_run(runtime_dir=tmp_path / "runtime", metadata_rows=[])
    assert payload["status"] == "NO_BASELINE"
