import json
import tempfile
from pathlib import Path

import pytest

from src import ai


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")


@pytest.fixture
def tmp_path():
    # pytest 기본 tmp_path의 임시 경로 권한 문제를 피하기 위해 tempfile을 직접 사용
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def test_mock_success_returns_ai_2f():
    result = ai.get_ai_result("2f")
    expected = json.loads((ai.MOCK_DIR / "ai_2f.json").read_text(encoding="utf-8"))

    assert result == expected
    assert result["ai_status"] == "SUCCESS"
    assert result["summary"]
    assert len(result["hypotheses"]) >= 1
    h = result["hypotheses"][0]
    assert h["cause"] and h["evidence"] and h["uncertainty"]
    assert result["additional_checks"]


def test_default_scenario_is_2f(monkeypatch):
    monkeypatch.delenv("AI_MODE", raising=False)
    assert ai.get_ai_result()["ai_status"] == "SUCCESS"


def test_unavailable_returns_ai_unavailable():
    result = ai.get_ai_result("unavailable")

    assert result == {
        "ai_status": "UNAVAILABLE",
        "summary": None,
        "hypotheses": [],
        "additional_checks": [],
    }


def test_result_has_ai_spec_top_level_fields():
    for scenario in ("2f", "unavailable"):
        assert set(ai.get_ai_result(scenario)) == {
            "ai_status",
            "summary",
            "hypotheses",
            "additional_checks",
        }


def test_unknown_scenario_returns_error():
    result = ai.get_ai_result("nonexistent")

    assert result["ai_status"] == "ERROR"
    assert result["hypotheses"] == []


def test_non_mock_mode_returns_unavailable_without_exception(monkeypatch):
    monkeypatch.setenv("AI_MODE", "azure")

    assert ai.get_ai_result("2f")["ai_status"] == "UNAVAILABLE"


def test_invalid_response_returns_error(monkeypatch, tmp_path):
    (tmp_path / "ai_2f.json").write_text(
        json.dumps({"summary": 123, "hypotheses": "invalid"}), encoding="utf-8"
    )
    monkeypatch.setattr(ai, "MOCK_DIR", tmp_path)

    assert ai.get_ai_result("2f")["ai_status"] == "ERROR"


def test_missing_hypothesis_field_returns_error(monkeypatch, tmp_path):
    bad = {
        "ai_status": "SUCCESS",
        "summary": "s",
        "hypotheses": [{"cause": "L2 Loop 가능성", "evidence": []}],
        "additional_checks": [],
    }
    (tmp_path / "ai_2f.json").write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(ai, "MOCK_DIR", tmp_path)

    assert ai.get_ai_result("2f")["ai_status"] == "ERROR"


def test_missing_or_broken_file_returns_error(monkeypatch, tmp_path):
    monkeypatch.setattr(ai, "MOCK_DIR", tmp_path)
    assert ai.get_ai_result("2f")["ai_status"] == "ERROR"

    (tmp_path / "ai_2f.json").write_text("not json", encoding="utf-8")
    assert ai.get_ai_result("2f")["ai_status"] == "ERROR"


@pytest.mark.parametrize("content", ["", "[]", "null", "{}"])
def test_empty_or_non_object_response_returns_error(monkeypatch, tmp_path, content):
    (tmp_path / "ai_2f.json").write_text(content, encoding="utf-8")
    monkeypatch.setattr(ai, "MOCK_DIR", tmp_path)

    result = ai.get_ai_result("2f")

    assert result == {
        "ai_status": "ERROR",
        "summary": None,
        "hypotheses": [],
        "additional_checks": [],
    }


def test_failure_results_never_raise_and_have_no_hypotheses(monkeypatch):
    for mode, scenario in (("mock", "unavailable"), ("mock", "x"), ("azure", "2f")):
        monkeypatch.setenv("AI_MODE", mode)
        result = ai.get_ai_result(scenario)

        assert result["ai_status"] in ("UNAVAILABLE", "ERROR")
        assert result["hypotheses"] == [] and result["additional_checks"] == []
