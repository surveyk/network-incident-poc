import json

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")


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
    monkeypatch.setattr(app_module, "get_ai_result", lambda: json.loads(
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
    monkeypatch.setenv("AI_MODE", "azure")  # Azure 미구현 -> UNAVAILABLE Fallback

    assert_core_report_without_ai(client.get("/"))


def test_ai_unavailable_mock_file_renders_full_core_report(monkeypatch):
    from src import ai

    real = ai.get_ai_result
    monkeypatch.setattr(app_module, "get_ai_result", lambda: real("unavailable"))

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
