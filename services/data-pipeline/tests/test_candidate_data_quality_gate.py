from __future__ import annotations

from datetime import datetime

import pandas as pd

from warehouse.candidate_data_quality_gate import run_candidate_data_quality_gate


def _contract() -> dict:
    return {
        "gold": {
            "gold_growth_dynamics": {
                "columns": {
                    "country_code": {},
                    "country": {},
                    "year": {},
                    "run_id": {},
                    "run_date": {},
                    "loaded_at": {},
                    "completeness_score": {},
                    "SovDebtCrisis": {},
                    "CurrencyCrisis": {},
                    "BankingCrisis": {},
                    "crisis_any": {},
                    "crisis_composite": {},
                }
            }
        },
        "analytics": {
            "analytics_clusters": {
                "columns": {
                    "country_code": {},
                    "country": {},
                    "year": {},
                    "cluster_id": {},
                    "latest_valid_year": {},
                    "run_id": {},
                    "run_date": {},
                    "loaded_at": {},
                }
            }
        },
    }


def _valid_artifacts() -> dict[str, pd.DataFrame]:
    loaded_at = datetime(2026, 5, 24, 0, 0, 0)
    silver = pd.DataFrame(
        [
            {
                "country_code": "VNM",
                "country": "Viet Nam",
                "year": 2025,
                "indicator": "gdp_growth_yoy",
                "value": 6.1,
                "source": "wdi",
                "run_id": "run-1",
                "run_date": "2026-05-24",
                "loaded_at": loaded_at,
            }
        ]
    )
    gold = pd.DataFrame(
        [
            {
                "country_code": "VNM",
                "country": "Viet Nam",
                "year": 2025,
                "run_id": "run-1",
                "run_date": "2026-05-24",
                "loaded_at": loaded_at,
                "completeness_score": 0.95,
                "SovDebtCrisis": 0,
                "CurrencyCrisis": 0,
                "BankingCrisis": 0,
                "crisis_any": 0,
                "crisis_composite": 0,
            }
        ]
    )
    analytics = pd.DataFrame(
        [
            {
                "country_code": "VNM",
                "country": "Viet Nam",
                "year": 2025,
                "cluster_id": 1,
                "latest_valid_year": 2025,
                "run_id": "run-1",
                "run_date": "2026-05-24",
                "loaded_at": loaded_at,
            }
        ]
    )
    return {
        "silver_indicators": silver,
        "gold_growth_dynamics": gold,
        "analytics_clusters": analytics,
    }


def _run_gate(artifacts: dict[str, pd.DataFrame]) -> dict:
    return run_candidate_data_quality_gate(
        expected_tables=["silver_indicators", "gold_growth_dynamics", "analytics_clusters"],
        candidate_artifacts=artifacts,
        contract_payload=_contract(),
    )


def test_valid_candidate_artifacts_pass_gate() -> None:
    payload = _run_gate(_valid_artifacts())
    assert payload["status"] == "PASSED"
    assert payload["errors"] == []


def test_missing_expected_candidate_table_fails_gate() -> None:
    artifacts = _valid_artifacts()
    artifacts.pop("analytics_clusters")
    payload = _run_gate(artifacts)
    assert payload["status"] == "FAILED"


def test_missing_required_metadata_column_fails_gate() -> None:
    artifacts = _valid_artifacts()
    artifacts["gold_growth_dynamics"] = artifacts["gold_growth_dynamics"].drop(columns=["run_id"])
    payload = _run_gate(artifacts)
    assert payload["status"] == "FAILED"


def test_duplicate_key_fails_gate() -> None:
    artifacts = _valid_artifacts()
    artifacts["silver_indicators"] = pd.concat(
        [artifacts["silver_indicators"], artifacts["silver_indicators"]],
        ignore_index=True,
    )
    payload = _run_gate(artifacts)
    assert payload["status"] == "FAILED"


def test_invalid_iso3_country_code_fails_gate() -> None:
    artifacts = _valid_artifacts()
    artifacts["silver_indicators"].loc[0, "country_code"] = "VN"
    payload = _run_gate(artifacts)
    assert payload["status"] == "FAILED"


def test_invalid_year_range_fails_gate() -> None:
    artifacts = _valid_artifacts()
    artifacts["analytics_clusters"].loc[0, "year"] = 1900
    payload = _run_gate(artifacts)
    assert payload["status"] == "FAILED"


def test_invalid_completeness_score_range_fails_gate() -> None:
    artifacts = _valid_artifacts()
    artifacts["gold_growth_dynamics"].loc[0, "completeness_score"] = 1.5
    payload = _run_gate(artifacts)
    assert payload["status"] == "FAILED"


def test_invalid_crisis_binary_value_fails_gate() -> None:
    artifacts = _valid_artifacts()
    artifacts["gold_growth_dynamics"].loc[0, "crisis_any"] = 2
    payload = _run_gate(artifacts)
    assert payload["status"] == "FAILED"


def test_invalid_crisis_composite_value_fails_gate() -> None:
    artifacts = _valid_artifacts()
    artifacts["gold_growth_dynamics"].loc[0, "crisis_composite"] = 4
    payload = _run_gate(artifacts)
    assert payload["status"] == "FAILED"
