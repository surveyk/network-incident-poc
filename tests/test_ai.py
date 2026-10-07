import json
import tempfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIError, APITimeoutError

from src import ai


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")
    for variable in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"):
        monkeypatch.delenv(variable, raising=False)

    def unexpected_client(*args, **kwargs):
        pytest.fail("Real Azure clients must not be created during tests")

    monkeypatch.setattr(ai, "OpenAI", unexpected_client)


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


@pytest.fixture
def core_result():
    return json.loads(
        (ai.MOCK_DIR.parent / "expected" / "loop_2f_expected.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def success_result():
    return {
        "ai_status": "SUCCESS",
        "summary": "연결 중단과 이후 복구가 확인되며 최종 원인은 추가 확인이 필요합니다.",
        "hypotheses": [{
            "cause": "네트워크 구성 이상 가능성",
            "evidence": ["MAC 주소 반복 이동이 확인됨"],
            "uncertainty": ["실제 연결 구성은 확인되지 않음"],
        }],
        "additional_checks": ["실제 연결 구성 확인"],
    }


@pytest.fixture
def azure_client(monkeypatch, success_result):
    monkeypatch.setenv("AI_MODE", "azure")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com///")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake-test-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "incident-analysis-deployment")
    client = MagicMock()
    client.__enter__.return_value = client
    client.chat.completions.create.return_value = SimpleNamespace(choices=[
        SimpleNamespace(message=SimpleNamespace(content=json.dumps(success_result, ensure_ascii=False)))
    ])
    constructor = MagicMock(return_value=client)
    monkeypatch.setattr(ai, "OpenAI", constructor)
    return constructor, client


def test_azure_success_sends_only_core_json(azure_client, core_result, success_result, monkeypatch):
    constructor, client = azure_client
    core_result.update(raw="raw-sentinel", INCIDENT_LOG_PATH="path-sentinel", filename="filename-sentinel")
    original = deepcopy(core_result)
    monkeypatch.setenv("INCIDENT_LOG_PATH", "environment-path-sentinel")

    def unexpected_file_read(*args, **kwargs):
        pytest.fail("Azure mode must not read logs or mock files")

    monkeypatch.setattr(Path, "read_text", unexpected_file_read)
    result = ai.get_ai_result(core_result)

    assert result == success_result
    assert ai._is_valid(result)
    assert core_result == original
    constructor.assert_called_once_with(
        api_key="fake-test-key", base_url="https://example.openai.azure.com/openai/v1/",
        timeout=30, max_retries=0,
    )
    client.chat.completions.create.assert_called_once()
    request = client.chat.completions.create.call_args.kwargs
    assert request["model"] == "incident-analysis-deployment"
    assert request["response_format"] == {"type": "json_object"}
    assert request["messages"][0] == {"role": "system", "content": ai.SYSTEM_PROMPT}
    content = request["messages"][1]["content"]
    assert request["messages"][1]["role"] == "user"
    assert json.loads(content) == {field: core_result[field] for field in ai.CORE_FIELDS}
    assert "2층" in content
    for forbidden in ("raw-sentinel", "path-sentinel", "filename-sentinel", "environment-path-sentinel"):
        assert forbidden not in json.dumps(request, ensure_ascii=False)


@pytest.mark.parametrize("variable", [
    "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT",
])
@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_azure_configuration_skips_client(azure_client, core_result, monkeypatch, variable, value):
    constructor, client = azure_client
    if value is None:
        monkeypatch.delenv(variable)
    else:
        monkeypatch.setenv(variable, value)

    assert ai.get_ai_result(core_result) == ai._fallback("UNAVAILABLE")
    constructor.assert_not_called()
    client.chat.completions.create.assert_not_called()


@pytest.mark.parametrize("content", [
    None, "", "   ", "not json", "null", "[]", "{}",
    '{"ai_status":"SUCCESS","summary":"s","hypotheses":[],"additional_checks":"invalid"}',
    '{"ai_status":"SUCCESS","hypotheses":[],"additional_checks":[]}',
    '{"ai_status":"UNAVAILABLE","summary":null,"hypotheses":[],"additional_checks":[]}',
])
def test_azure_bad_response_returns_error(azure_client, core_result, content):
    constructor, client = azure_client
    client.chat.completions.create.return_value.choices[0].message.content = content

    assert ai.get_ai_result(core_result) == ai._fallback("ERROR")
    constructor.assert_called_once()
    client.chat.completions.create.assert_called_once()


@pytest.mark.parametrize("error", [
    APITimeoutError(request=httpx.Request("POST", "https://example.invalid")),
    APIError("fake SDK error", request=httpx.Request("POST", "https://example.invalid"), body=None),
])
def test_azure_sdk_error_is_contained_without_output(azure_client, core_result, error, capsys, caplog):
    constructor, client = azure_client
    client.chat.completions.create.side_effect = error

    assert ai.get_ai_result(core_result) == ai._fallback("ERROR")
    constructor.assert_called_once()
    client.chat.completions.create.assert_called_once()
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert caplog.records == []


def test_azure_client_creation_failure_returns_error(azure_client, core_result):
    constructor, client = azure_client
    constructor.side_effect = RuntimeError("fake client failure")

    assert ai.get_ai_result(core_result) == ai._fallback("ERROR")
    client.chat.completions.create.assert_not_called()


@pytest.mark.parametrize("core", [None, "2f", {}, {field: object() for field in ai.CORE_FIELDS}])
def test_azure_requires_serializable_passed_core(azure_client, core):
    constructor, client = azure_client

    assert ai.get_ai_result(core) == ai._fallback("ERROR")
    constructor.assert_not_called()
    client.chat.completions.create.assert_not_called()


@pytest.mark.parametrize("field", ["ai_status", "summary", "hypotheses", "additional_checks"])
def test_validator_rejects_missing_success_fields(success_result, field):
    del success_result[field]
    assert not ai._is_valid(success_result)


@pytest.mark.parametrize("summary", [None, "", "   ", 123])
def test_validator_rejects_empty_success_summary(success_result, summary):
    success_result["summary"] = summary
    assert not ai._is_valid(success_result)


@pytest.mark.parametrize("field", ["cause", "evidence", "uncertainty"])
def test_validator_rejects_missing_hypothesis_fields(success_result, field):
    del success_result["hypotheses"][0][field]
    assert not ai._is_valid(success_result)


@pytest.mark.parametrize("field,value", [
    ("cause", ""), ("cause", "   "), ("cause", None),
    ("evidence", "text"), ("evidence", [1]),
    ("uncertainty", None), ("uncertainty", [1]),
])
def test_validator_rejects_invalid_hypothesis_values(success_result, field, value):
    success_result["hypotheses"][0][field] = value
    assert not ai._is_valid(success_result)


@pytest.mark.parametrize("status", ["ERROR", "UNAVAILABLE"])
@pytest.mark.parametrize("field,value", [
    ("summary", "unexpected"), ("hypotheses", [{}]), ("additional_checks", ["unexpected"]),
])
def test_validator_requires_empty_failure_result(status, field, value):
    result = ai._fallback(status)
    assert ai._is_valid(result)
    result[field] = value
    assert not ai._is_valid(result)


def test_azure_allows_insufficient_evidence_without_hypotheses(azure_client, core_result, success_result):
    constructor, client = azure_client
    success_result["hypotheses"] = []
    client.chat.completions.create.return_value.choices[0].message.content = json.dumps(success_result)

    assert ai.get_ai_result(core_result) == success_result
    assert ai._is_valid(success_result)


def test_mock_accepts_core_and_keyword_scenario(core_result):
    assert ai.get_ai_result(core_result) == ai.get_ai_result("2f")
    assert ai.get_ai_result(core_result, scenario="unavailable") == ai._fallback("UNAVAILABLE")


@pytest.mark.parametrize("mode", ["off", "other"])
def test_other_modes_keep_unavailable_fallback(monkeypatch, core_result, mode):
    monkeypatch.setenv("AI_MODE", mode)
    assert ai.get_ai_result(core_result) == ai._fallback("UNAVAILABLE")
