import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src import ai, app as app_module
from src.core import analyze

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def actual_core_input(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")
    monkeypatch.setenv("INCIDENT_LOG_PATH", str(app_module.BASE_DIR / "data" / "sample_logs" / "loop_2f.log"))
    for variable in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"):
        monkeypatch.delenv(variable, raising=False)

    def unexpected_client(*args, **kwargs):
        pytest.fail("Real Azure clients must not be created during tests")

    monkeypatch.setattr(ai, "OpenAI", unexpected_client)


def test_index_shows_core_report():
    r = client.get("/")

    assert r.status_code == 200
    html = r.text
    for text in (
        "네트워크 장애 상황보고",
        "2층 네트워크",
        "112시스템",
        "온나라",
        "폴넷",
        "영향 가능 업무",
        "매우 높음",
        "P1 / 최우선",
        "복구 완료",
        "10:21:24",
        "장애 의심 포트 차단",
    ):
        assert text in html


def test_index_has_five_sections():
    html = client.get("/").text

    for title in ("1. 장애 요약", "2. 장애경과", "3. 조치내용", "4. 추정원인 및 추가확인", "5. 기술 상세정보"):
        assert title in html


def test_index_shows_ai_analysis():
    html = client.get("/").text

    assert "AI 분석 완료" in html
    assert "L2 Loop 가능성" in html
    assert "불확실성" in html
    assert "의심 포트의 실제 물리적 연결상태가 확인되지 않음" in html
    assert "추가확인" in html
    assert "112시스템, 온나라, 폴넷의 실제 서비스 정상 여부 확인" in html


def test_index_shows_facts_with_source_line():
    html = client.get("/").text

    assert "MAC 주소 반복 이동이 확인됨" in html
    assert "Line 4" in html
    assert "2층 층간스위치, 백본스위치" in html


def test_index_does_not_state_confirmed_service_failure():
    html = client.get("/").text

    for name in ("112시스템", "온나라", "폴넷"):
        assert f"{name} 장애" not in html
        assert f"{name} 서비스 중단" not in html


def test_ai_unavailable_keeps_core_report(monkeypatch):
    monkeypatch.setattr(app_module, "get_ai_result", lambda core_result: json.loads(
        (app_module.BASE_DIR / "data" / "mock" / "ai_unavailable.json").read_text(encoding="utf-8")
    ))

    r = client.get("/")

    assert r.status_code == 200
    for text in ("2층 네트워크", "112시스템", "매우 높음", "P1 / 최우선", "복구 완료", "장애 의심 포트 차단"):
        assert text in r.text
    assert "AI 분석 사용 불가" in r.text
    assert "L2 Loop 가능성" not in r.text


def test_core_error_returns_analysis_failure_not_ai_unavailable(monkeypatch):
    monkeypatch.setattr(app_module, "load_core", lambda: {"incident": {}, "impact": {}})

    r = client.get("/")

    assert r.status_code == 500
    assert "분석 실패" in r.text
    assert "AI 분석 사용 불가" not in r.text


def test_timeline_renders_vertical_flow_in_order():
    html = client.get("/").text
    section = html.split("2. 장애경과")[1].split("3. 조치내용")[0]

    assert 'class="timeline"' in section
    steps = (
        "MAC 주소 반복 이동 감지",
        "2층 방향 Broadcast 트래픽 증가",
        "2층 네트워크 연결 중단",
        "장애 의심 포트 차단",
        "2층 네트워크 연결 복구",
    )
    positions = [section.index(s) for s in steps]
    assert positions == sorted(positions)
    for text in ("10:21:02", "10:21:24", "10:22:05", "10:22:13",
                 "이상징후", "장애발생", "조치", "복구", "백본스위치", "2층 층간스위치"):
        assert text in section
    assert section.count('<li class="stage-') == 5
    assert 'class="stage-normalized"' not in section
    assert "10:22:19" not in section
    assert "정상화" not in section
    assert "Line " not in section and "%SW_MATM" not in section


def test_summary_primary_cards_for_recovered_actual_core():
    html = client.get("/").text
    section = html.split("1. 장애 요약")[1].split("2. 장애경과")[0]

    for text in ("장애장소", "2층 네트워크", "장애시간", "10:21:24", "10:22:13", "총 장애시간", "49초",
                 "최초 이상징후 10:21:02", "현재상태", "복구 완료", "summary-card status-recovered",
                 "영향 가능 업무", "112시스템", "온나라", "폴넷", "매우 높음", "P1 / 최우선"):
        assert text in section
    assert "발생일시" not in section


@pytest.mark.parametrize(
    "status, css, label",
    [("ACTIVE", "status-active", "장애 지속"), ("RECOVERING", "status-warning", "복구 중"),
     ("UNKNOWN", "status-warning", "확인 필요")],
)
def test_status_card_css_class_and_text(monkeypatch, status, css, label):
    core = app_module.load_core()
    core["incident"]["status"] = status
    monkeypatch.setattr(app_module, "load_core", lambda: core)

    html = client.get("/").text

    assert f"summary-card {css}" in html
    assert label in html
    assert "summary-card status-recovered" not in html


CORE_TEXTS = (
    "2층 네트워크",
    "112시스템",
    "온나라",
    "폴넷",
    "영향 가능 업무",
    "매우 높음",
    "P1 / 최우선",
    "복구 완료",
    "10:21:02",
    "10:22:13",
    "장애시간",
    "총 장애시간",
    "49초",
    "summary-card status-recovered",
    "MAC 주소 반복 이동 감지",
    "장애 의심 포트 차단",
    "조치 이후 2층 네트워크 연결 복구",
    "MAC 주소 반복 이동이 확인됨",
    "Line 4",
    "2층 층간스위치, 백본스위치",
)
AI_ONLY_TEXTS = ("L2 Loop 가능성", "Gi1/0/18", "VLAN20")


def assert_core_report_without_ai(response):
    assert response.status_code == 200
    for text in CORE_TEXTS + ("AI 분석 사용 불가",):
        assert text in response.text
    for text in AI_ONLY_TEXTS:
        assert text not in response.text


def test_ai_unavailable_via_ai_mode_renders_full_core_report(monkeypatch):
    monkeypatch.setenv("AI_MODE", "azure")

    assert_core_report_without_ai(client.get("/"))


def test_ai_unavailable_mock_file_renders_full_core_report(monkeypatch):
    from src import ai

    real = ai.get_ai_result
    monkeypatch.setattr(app_module, "get_ai_result", lambda core_result: real(core_result, scenario="unavailable"))

    assert_core_report_without_ai(client.get("/"))


def test_ai_error_response_does_not_fail_application(monkeypatch):
    from src import ai

    monkeypatch.setattr(ai, "MOCK_DIR", app_module.BASE_DIR / "no_such_dir")

    assert_core_report_without_ai(client.get("/"))


def test_ai_unavailable_shows_state_in_header_and_analysis_section(monkeypatch):
    monkeypatch.setenv("AI_MODE", "azure")

    html = client.get("/").text

    assert html.count("AI 분석 사용 불가") == 1
    assert "AI 분석을 사용할 수 없어 추정원인 자동분석은 제공되지 않습니다." in html


def test_actual_core_report_matches_expected_and_preserves_facts():
    expected = json.loads(
        (app_module.BASE_DIR / "data" / "expected" / "loop_2f_expected.json").read_text(encoding="utf-8")
    )
    response = client.get("/")

    assert response.status_code == 200
    report = response.context["report"]
    assert report == app_module.build_report(expected, app_module.get_ai_result())
    assert len(report["timeline"]) == 5
    assert report["timeline"][-1]["stage_code"] == "RECOVERY"
    assert [fact["source_line"] for fact in report["details"]["facts"]] == [
        fact["source_line"] for fact in expected["facts"]
    ]
    for fact in expected["facts"]:
        assert f"Line {fact['source_line']}" in response.text
    assert report["details"]["analysis_context"]["related_event_count"] == 17


@pytest.mark.parametrize("sample, location, service", [
    ("link_1f", "1층 네트워크", "KICS(킥스)"),
    ("link_3f", "3층 네트워크", "TCS"),
])
def test_link_samples_use_actual_core_with_ai_fallback(monkeypatch, sample, location, service):
    monkeypatch.setenv("INCIDENT_LOG_PATH", f"data/sample_logs/{sample}.log")
    monkeypatch.setenv("AI_MODE", "off")

    response = client.get("/")

    assert response.status_code == 200
    for text in (location, service, "온나라", "폴넷", "높음", "P2 / 신속 복구", "복구 완료", "AI 분석 사용 불가"):
        assert text in response.text
    for text in AI_ONLY_TEXTS + ("2층 네트워크", "112시스템"):
        assert text not in response.text
    report = response.context["report"]
    assert report["analysis"]["ai_status"] == "UNAVAILABLE"
    assert len(report["timeline"]) == 4
    assert all(event["stage_code"] != "NORMALIZED" for event in report["timeline"])
    assert len(report["details"]["facts"]) == 4
    assert report["details"]["analysis_context"]["related_event_count"] == 4


def test_relative_input_path_is_resolved_from_repository(monkeypatch, tmp_path):
    calls = []

    def tracked_analyze(log_path, incident_sequence):
        calls.append((log_path, incident_sequence))
        return analyze(log_path, incident_sequence=incident_sequence)

    monkeypatch.setenv("INCIDENT_LOG_PATH", "data/sample_logs/loop_2f.log")
    monkeypatch.setattr(app_module, "analyze", tracked_analyze)
    monkeypatch.chdir(tmp_path)

    assert client.get("/").status_code == 200
    assert calls == [(app_module.BASE_DIR / "data" / "sample_logs" / "loop_2f.log", 1)]


def test_absolute_renamed_log_input_does_not_depend_on_sample_name(monkeypatch, tmp_path):
    source = app_module.BASE_DIR / "data" / "sample_logs" / "loop_2f.log"
    path = tmp_path / "arbitrary.log"
    path.write_bytes(source.read_bytes())
    monkeypatch.setenv("INCIDENT_LOG_PATH", str(path))

    response = client.get("/")

    assert response.status_code == 200
    assert response.context["report"] == app_module.build_report(analyze(source), app_module.get_ai_result())


@pytest.mark.parametrize("configured_path", [None, "", "   ", "data/sample_logs/missing.log", "data/sample_logs"])
def test_invalid_input_returns_core_failure_without_calling_ai(monkeypatch, configured_path):
    if configured_path is None:
        monkeypatch.delenv("INCIDENT_LOG_PATH", raising=False)
    else:
        monkeypatch.setenv("INCIDENT_LOG_PATH", configured_path)

    def unexpected_ai_call(core_result):
        pytest.fail("AI must not run after Core input failure")

    monkeypatch.setattr(app_module, "get_ai_result", unexpected_ai_call)
    response = client.get("/")

    assert response.status_code == 500
    assert "분석 실패" in response.text
    assert "AI 분석 사용 불가" not in response.text
    assert "Traceback" not in response.text


@pytest.mark.parametrize("error_type", [OSError, ValueError, KeyError, TypeError])
def test_analyze_failure_uses_existing_core_error_policy(monkeypatch, error_type):
    def failed_analyze(log_path, incident_sequence):
        raise error_type("Core analysis failed")

    monkeypatch.setattr(app_module, "analyze", failed_analyze)
    response = client.get("/")

    assert response.status_code == 500
    assert "분석 실패" in response.text
    assert "AI 분석 사용 불가" not in response.text
    assert "Core analysis failed" not in response.text


@pytest.mark.parametrize("content", ["", "2026-09-30 10:21:00 SW-ACCESS-02 %SYS-5-CONFIG_I: Configured from console\n"])
def test_actual_unanalyzable_input_returns_core_failure(monkeypatch, tmp_path, content):
    path = tmp_path / "input.log"
    path.write_text(content, encoding="utf-8")
    monkeypatch.setenv("INCIDENT_LOG_PATH", str(path))

    response = client.get("/")

    assert response.status_code == 500
    assert "분석 실패" in response.text
    assert "AI 분석 사용 불가" not in response.text


@pytest.mark.parametrize("status", ["UNAVAILABLE", "ERROR"])
def test_actual_core_sections_are_unchanged_by_ai_failure(monkeypatch, status):
    successful = client.get("/").context["report"]
    failed_ai = {"ai_status": status, "summary": None, "hypotheses": [], "additional_checks": []}
    monkeypatch.setattr(app_module, "get_ai_result", lambda core_result: failed_ai)

    response = client.get("/")

    assert_core_report_without_ai(response)
    failed = response.context["report"]
    for section in ("summary", "timeline", "actions"):
        assert failed[section] == successful[section]
    for section in ("facts", "analysis_context"):
        assert failed["details"][section] == successful["details"][section]
    assert failed["analysis"]["ai_status"] == status
    assert failed["details"]["hypotheses"] == []


def test_index_passes_same_core_result_to_ai(monkeypatch):
    core_result = app_module.load_core()
    calls = []
    real_ai = app_module.get_ai_result

    def tracked_ai(passed_core):
        calls.append(passed_core)
        return real_ai(passed_core)

    monkeypatch.setattr(app_module, "load_core", lambda: core_result)
    monkeypatch.setattr(app_module, "get_ai_result", tracked_ai)

    response = client.get("/")

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0] is core_result
    assert response.context["report"] == app_module.build_report(core_result, real_ai(core_result))


def test_azure_sdk_failure_keeps_http_200_and_core_report(monkeypatch):
    successful = client.get("/").context["report"]
    monkeypatch.setenv("AI_MODE", "azure")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake-test-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "incident-analysis-deployment")
    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.chat.completions.create.side_effect = TimeoutError("fake SDK failure")
    constructor = MagicMock(return_value=fake_client)
    monkeypatch.setattr(ai, "OpenAI", constructor)

    response = client.get("/")

    assert_core_report_without_ai(response)
    failed = response.context["report"]
    assert failed["analysis"]["ai_status"] == "ERROR"
    for section in ("summary", "timeline", "actions"):
        assert failed[section] == successful[section]
    for section in ("facts", "analysis_context"):
        assert failed["details"][section] == successful["details"][section]
    constructor.assert_called_once()
    fake_client.chat.completions.create.assert_called_once()
