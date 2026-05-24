from __future__ import annotations

from pathlib import Path

import pandas as pd

from warehouse.bigquery_warehouse_publish import (
    promote_validated_candidate,
    publish_with_staging,
    stage_and_validate_candidate,
)


class _Writer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self._staging_rows = 0
        self._production_rows = 0

    def get_table_layout(self, table_id: str) -> tuple[dict[str, int | str] | None, list[str] | None]:
        self.calls.append(("layout", table_id, ""))
        return None, ["country_code", "year"]

    def load_parquet(
        self,
        *,
        parquet_path: Path,
        table_id: str,
        range_partitioning: dict[str, int | str] | None = None,
        clustering_fields: list[str] | None = None,
    ) -> str:
        del range_partitioning, clustering_fields
        frame = pd.read_parquet(parquet_path)
        self._staging_rows = int(len(frame))
        self.calls.append(("load", table_id, str(parquet_path)))
        return "load-1"

    def get_table_info(self, table_id: str) -> tuple[int, list[str]]:
        self.calls.append(("table_info", table_id, ""))
        return self._staging_rows, ["country_code", "year", "run_id"]

    def copy_table(self, *, source_table_id: str, destination_table_id: str) -> str:
        self.calls.append(("copy", source_table_id, destination_table_id))
        self._production_rows = self._staging_rows
        return "copy-1"

    def count_rows(self, table_id: str) -> int:
        self.calls.append(("count", table_id, ""))
        return self._production_rows


def _parquet_fixture(tmp_path: Path, rows: int = 2) -> Path:
    frame = pd.DataFrame(
        [
            {"country_code": "VNM", "year": 2024, "run_id": "r1"},
            {"country_code": "THA", "year": 2024, "run_id": "r1"},
        ][:rows]
    )
    path = tmp_path / "candidate.parquet"
    frame.to_parquet(path, index=False)
    return path


def test_stage_and_validate_candidate_does_not_copy(tmp_path: Path) -> None:
    writer = _Writer()
    parquet_path = _parquet_fixture(tmp_path, rows=2)
    candidate = stage_and_validate_candidate(
        project_id="western-pivot-452008-a6",
        location="asia-southeast1",
        dataset="gov_ai_gold",
        staging_table="gold_growth_dynamics_staging_run_20260524_010203",
        production_table="gold_growth_dynamics",
        parquet_path=parquet_path,
        expected_required_columns=["country_code", "year", "run_id"],
        local_row_count=2,
        writer=writer,
    )

    assert candidate.staging_row_count == 2
    assert all(call[0] != "copy" for call in writer.calls)


def test_promote_validated_candidate_copies_once(tmp_path: Path) -> None:
    writer = _Writer()
    parquet_path = _parquet_fixture(tmp_path, rows=1)
    candidate = stage_and_validate_candidate(
        project_id="western-pivot-452008-a6",
        location="asia-southeast1",
        dataset="gov_ai_analytics",
        staging_table="analytics_clusters_staging_run_20260524_010203",
        production_table="analytics_clusters",
        parquet_path=parquet_path,
        expected_required_columns=["country_code", "year", "run_id"],
        local_row_count=1,
        writer=writer,
    )
    result = promote_validated_candidate(
        project_id="western-pivot-452008-a6",
        location="asia-southeast1",
        candidate=candidate,
        writer=writer,
    )

    assert result.production_row_count == 1
    assert any(call[0] == "copy" for call in writer.calls)


def test_publish_with_staging_keeps_legacy_behavior(tmp_path: Path) -> None:
    writer = _Writer()
    parquet_path = _parquet_fixture(tmp_path, rows=2)
    result = publish_with_staging(
        project_id="western-pivot-452008-a6",
        location="asia-southeast1",
        dataset="gov_ai_gold",
        staging_table="gold_social_welfare_staging_run_20260524_010203",
        production_table="gold_social_welfare",
        parquet_path=parquet_path,
        expected_required_columns=["country_code", "year", "run_id"],
        local_row_count=2,
        writer=writer,
    )

    assert result.staging_row_count == 2
    assert result.production_row_count == 2
    assert any(call[0] == "copy" for call in writer.calls)
