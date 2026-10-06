import copy
import json
from pathlib import Path

import pytest

from src.report import build_report

DATA = Path(__file__).resolve().parent.parent / "data"


def load(relative):
    return json.loads((DATA / relative).read_text(encoding="utf-8"))


@pytest.fixture
def core():
    return load("mock/core_2f.json")


@pytest.fixture
def ai_ok():
    return load("mock/ai_2f.json")


@pytest.fixture
def ai_down():
    return load("mock/ai_unavailable.json")


def test_summary_2f(core, ai_ok):
    s = build_report(core, ai_ok)["summary"]

    assert s["incident_time"] == "2026.9.30. 10:21:24 ~ 10:22:13"
    assert s["detected_time"] == "10:21:02"
    assert s["location"] == "2층 네트워크"
    assert s["affected_services"] == ["112시스템", "온나라", "폴넷"]
    assert s["criticality"] == "매우 높음"
    assert s["recovery_priority"] == "P1 / 최우선"
    assert s["status"] == "복구 완료"
    assert s["recurrence"] == "확인 필요"


def test_affected_services_are_possible_impact_not_confirmed_failure(core, ai_ok):
    report = build_report(core, ai_ok)

    assert report["summary"]["affected_services_label"] == "영향 가능 업무"
    assert "확인" in report["summary"]["service_note"]
    text = json.dumps(report, ensure_ascii=False)
    for name in ("112시스템", "온나라", "폴넷"):
        assert f"{name} 장애" not in text
        assert f"{name} 서비스 중단" not in text


def test_timeline(core, ai_ok):
    timeline = build_report(core, ai_ok)["timeline"]

    assert [e["time"] for e in timeline] == [
        "10:21:02", "10:21:22", "10:21:24", "10:22:05", "10:22:13",
    ]
    assert [e["stage"] for e in timeline] == ["이상징후", "이상징후", "장애", "조치", "복구"]
    assert timeline[0]["text"] == "MAC 주소 반복 이동 감지"


def test_actions_from_action_stage_without_causal_claim(core, ai_ok):
    actions = build_report(core, ai_ok)["actions"]

    assert actions[0] == "장애 의심 포트 차단"
    assert actions[1] == "조치 이후 2층 네트워크 연결 복구"
    assert not any("확인 필요" in a or "때문" in a or "으로 복구" in a for a in actions)


def test_no_action_event_gives_no_actions():
    core = load("expected/link_1f_expected.json")

    assert build_report(core, load("mock/ai_unavailable.json"))["actions"] == []


def test_analysis_success(core, ai_ok):
    a = build_report(core, ai_ok)["analysis"]

    assert a["ai_status"] == "SUCCESS"
    assert a["available"] is True
    assert a["ai_status_label"] == "AI 분석 완료"
    assert a["probable_cause"] == "L2 Loop 가능성"
    assert 2 <= len(a["evidence"]) <= 4
    assert a["uncertainty"]
    assert a["additional_checks"] == ai_ok["additional_checks"]
    assert a["ai_summary"] == ai_ok["summary"]


def test_ai_unavailable_keeps_core_report(core, ai_down):
    report = build_report(core, ai_down)

    assert report["summary"] == build_report(core, load("mock/ai_2f.json"))["summary"]
    assert len(report["timeline"]) == 5
    assert report["actions"]
    a = report["analysis"]
    assert a["available"] is False
    assert a["ai_status_label"] == "AI 분석 사용 불가"
    assert a["message"]
    assert a["probable_cause"] is None
    assert a["evidence"] == a["additional_checks"] == []


def test_ai_error_treated_as_unavailable(core):
    ai_error = {"ai_status": "ERROR", "summary": None, "hypotheses": [], "additional_checks": []}

    a = build_report(core, ai_error)["analysis"]

    assert a["available"] is False
    assert a["ai_status_label"] == "AI 분석 사용 불가"


def test_ai_cannot_override_core_values(core, ai_ok):
    ai_tampered = dict(ai_ok, overall_criticality="HIGH", recovery_priority="P2",
                       location="3층 네트워크", status="ACTIVE")

    assert build_report(core, ai_tampered)["summary"] == build_report(core, ai_ok)["summary"]


def test_inputs_are_not_mutated(core, ai_ok):
    core_before, ai_before = copy.deepcopy(core), copy.deepcopy(ai_ok)

    report = build_report(core, ai_ok)
    report["analysis"]["evidence"].append("x")
    report["details"]["facts"].append({})

    assert core == core_before
    assert ai_ok == ai_before


def test_facts_separate_from_ai_inference(core, ai_ok):
    details = build_report(core, ai_ok)["details"]

    assert len(details["facts"]) == len(core["facts"])
    assert not any("L2 Loop 가능성" in f["text"] for f in details["facts"])
    assert details["facts"][0] == {
        "time": "10:21:02",
        "device": "2층 층간스위치",
        "type": "MAC_FLAPPING",
        "text": "MAC 주소 반복 이동이 확인됨",
        "source_line": 4,
    }
    assert [h["cause"] for h in details["hypotheses"]] == ["L2 Loop 가능성"]


def test_analysis_context_in_details(core, ai_ok):
    ctx = build_report(core, ai_ok)["details"]["analysis_context"]

    assert ctx["devices"] == ["2층 층간스위치", "백본스위치"]
    assert ctx["device_count"] == 2
    assert ctx["related_event_count"] == 17


def test_success_without_hypotheses_does_not_invent_cause(core):
    ai_empty = {"ai_status": "SUCCESS", "summary": "s", "hypotheses": [],
                "additional_checks": ["물리 회선상태 확인"]}

    a = build_report(core, ai_empty)["analysis"]

    assert a["probable_cause"] is None
    assert "특정하기 어려움" in a["message"]
    assert a["additional_checks"] == ["물리 회선상태 확인"]


def test_missing_detected_time_does_not_fail(core, ai_ok):
    core["incident"]["detected_time"] = None

    assert build_report(core, ai_ok)["summary"]["detected_time"] == "확인 불가"


@pytest.mark.parametrize(
    "section, key", [("incident", "location"), ("incident", "status"), ("impact", "affected_services")]
)
def test_missing_core_required_value_raises(core, ai_ok, section, key):
    del core[section][key]

    with pytest.raises(ValueError):
        build_report(core, ai_ok)


@pytest.mark.parametrize(
    "name, location, service, criticality, priority",
    [
        ("link_1f", "1층 네트워크", "KICS(킥스)", "높음", "P2 / 신속 복구"),
        ("link_3f", "3층 네트워크", "TCS", "높음", "P2 / 신속 복구"),
    ],
)
def test_link_samples_from_expected(name, location, service, criticality, priority, ai_down):
    s = build_report(load(f"expected/{name}_expected.json"), ai_down)["summary"]

    assert s["location"] == location
    assert service in s["affected_services"]
    assert s["criticality"] == criticality
    assert s["recovery_priority"] == priority
    assert s["status"] == "복구 완료"


@pytest.mark.parametrize("status", ["UNAVAILABLE", "ERROR"])
def test_ai_failure_keeps_every_core_section(core, ai_ok, status):
    ai_failed = {"ai_status": status, "summary": None, "hypotheses": [], "additional_checks": []}

    ok, failed = build_report(core, ai_ok), build_report(core, ai_failed)

    assert failed["summary"] == ok["summary"]
    assert failed["timeline"] == ok["timeline"]
    assert failed["actions"] == ok["actions"]
    assert failed["details"]["facts"] == ok["details"]["facts"]
    assert failed["details"]["analysis_context"] == ok["details"]["analysis_context"]
    assert failed["details"]["hypotheses"] == []
    assert failed["analysis"]["ai_status_label"] == "AI 분석 사용 불가"


def test_ai_unavailable_core_values_preserved(core, ai_down):
    s = build_report(core, ai_down)["summary"]

    assert s["location"] == "2층 네트워크"
    assert s["affected_services"] == ["112시스템", "온나라", "폴넷"]
    assert s["criticality"] == "매우 높음"
    assert s["recovery_priority"] == "P1 / 최우선"
    assert s["status"] == "복구 완료"
