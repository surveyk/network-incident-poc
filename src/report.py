from datetime import datetime

CRITICALITY_LABELS = {"VERY_HIGH": "매우 높음", "HIGH": "높음", "NORMAL": "보통"}
PRIORITY_LABELS = {"P1": "P1 / 최우선", "P2": "P2 / 신속 복구", "P3": "P3 / 일반 복구"}
STATUS_LABELS = {
    "ACTIVE": "장애 지속",
    "RECOVERING": "복구 중",
    "RECOVERED": "복구 완료",
    "UNKNOWN": "확인 필요",
}
STATUS_CLASSES = {"RECOVERED": "recovered", "ACTIVE": "active"}  # 그 외는 warning
RECURRENCE_LABELS = {
    "REPEATED": "반복 장애",
    "NOT_REPEATED": "반복 없음",
    "UNKNOWN": "확인 필요",
}
STAGE_LABELS = {
    "PRECURSOR": "이상징후",
    "INCIDENT": "장애발생",
    "ACTION": "조치",
    "RECOVERY": "복구",
    "NORMALIZED": "정상화",
}

UNKNOWN_TEXT = "확인 불가"
AI_UNAVAILABLE_TEXT = "AI 분석을 사용할 수 없어 추정원인 자동분석은 제공되지 않습니다."
NO_CAUSE_TEXT = "현재 로그만으로 구체적인 장애원인을 특정하기 어려움."
MAX_EVIDENCE = 4
MAX_UNCERTAINTY = 2


def _dt(value):
    return datetime.fromisoformat(value) if value else None


def _hms(value):
    dt = _dt(value)
    return dt.strftime("%H:%M:%S") if dt else None


def _incident_time(start, recovery):
    start_dt, recovery_dt = _dt(start), _dt(recovery)
    if not start_dt:
        return UNKNOWN_TEXT
    text = f"{start_dt.year}.{start_dt.month}.{start_dt.day}. {start_dt:%H:%M:%S}"
    return f"{text} ~ {recovery_dt:%H:%M:%S}" if recovery_dt else f"{text} ~"


def _duration(start, recovery):
    start_dt, recovery_dt = _dt(start), _dt(recovery)
    if not start_dt or not recovery_dt or recovery_dt < start_dt:
        return None
    hours, rest = divmod(int((recovery_dt - start_dt).total_seconds()), 3600)
    minutes, seconds = divmod(rest, 60)
    parts = [f"{hours}시간"] if hours else []
    if minutes:
        parts.append(f"{minutes}분")
    if seconds or not parts:
        parts.append(f"{seconds}초")
    return " ".join(parts)


def _require(core, section, key):
    value = (core.get(section) or {}).get(key)
    if value in (None, "", []):
        raise ValueError(f"Core Result에 필수값이 없음: {section}.{key}")
    return value


def _build_summary(core):
    incident, impact = core["incident"], core["impact"]
    services = _require(core, "impact", "affected_services")
    status = _require(core, "incident", "status")

    summary = {
        "incident_time": _incident_time(incident.get("start_time"), incident.get("recovery_time")),
        "duration": _duration(incident.get("start_time"), incident.get("recovery_time")),
        "detected_time": _hms(incident.get("detected_time")) or UNKNOWN_TEXT,
        "location": _require(core, "incident", "location"),
        "affected_services_label": "영향 가능 업무",
        "affected_services": [s["name"] for s in services],
        "criticality": CRITICALITY_LABELS.get(impact.get("overall_criticality"), UNKNOWN_TEXT),
        "recovery_priority": PRIORITY_LABELS.get(impact.get("recovery_priority"), UNKNOWN_TEXT),
        "status": STATUS_LABELS.get(status, STATUS_LABELS["UNKNOWN"]),
        "status_class": STATUS_CLASSES.get(status, "warning"),
        "recurrence": RECURRENCE_LABELS.get(
            (core.get("recurrence") or {}).get("status"), RECURRENCE_LABELS["UNKNOWN"]
        ),
    }
    if impact.get("verification_status") == "UNVERIFIED":
        summary["service_note"] = "실제 서비스 상태는 확인되지 않음(확인 필요)"
    return summary


def _build_timeline(core):
    return [
        {
            "time": _hms(e.get("timestamp")),
            "stage": STAGE_LABELS.get(e.get("stage"), e.get("stage")),
            "stage_code": e.get("stage"),
            "device": e.get("device"),
            "text": e.get("summary"),
        }
        for e in core.get("timeline", [])
    ]


def _build_actions(core):
    events = core.get("timeline", [])
    actions = [e["summary"] for e in events if e.get("stage") == "ACTION"]
    if not actions:
        return []
    # 선후관계만 표현하고 인과관계는 확정하지 않는다.
    actions += [f"조치 이후 {e['summary']}" for e in events if e.get("stage") == "RECOVERY"]
    actions += [e["summary"] for e in events if e.get("stage") == "NORMALIZED"]
    return actions


def _build_analysis(ai):
    status = ai.get("ai_status")
    analysis = {
        "ai_status": status,
        "ai_status_label": "AI 분석 완료" if status == "SUCCESS" else "AI 분석 사용 불가",
        "available": status == "SUCCESS",
        "ai_summary": None,
        "probable_cause": None,
        "evidence": [],
        "uncertainty": [],
        "additional_checks": [],
        "message": None,
    }
    if status != "SUCCESS":
        analysis["message"] = AI_UNAVAILABLE_TEXT
        return analysis

    analysis["ai_summary"] = ai.get("summary")
    analysis["additional_checks"] = list(ai.get("additional_checks") or [])
    hypotheses = ai.get("hypotheses") or []
    if hypotheses:
        top = hypotheses[0]
        analysis["probable_cause"] = top["cause"]
        analysis["evidence"] = list(top["evidence"][:MAX_EVIDENCE])
        analysis["uncertainty"] = list(top["uncertainty"][:MAX_UNCERTAINTY])
    else:
        analysis["message"] = NO_CAUSE_TEXT
    return analysis


def _build_details(core, ai):
    context = core.get("analysis_context") or {}
    devices = list(context.get("devices_analyzed") or [])
    return {
        "facts": [
            {
                "time": _hms(f.get("timestamp")),
                "device": f.get("device"),
                "type": f.get("type"),
                "text": f.get("text"),
                "source_line": f.get("source_line"),
            }
            for f in core.get("facts", [])
        ],
        "analysis_context": {
            "devices": devices,
            "device_count": context.get("log_source_count", len(devices)),
            "related_event_count": context.get("related_event_count"),
        },
        "hypotheses": [
            {
                "cause": h["cause"],
                "evidence": list(h["evidence"]),
                "uncertainty": list(h["uncertainty"]),
            }
            for h in (ai.get("hypotheses") or [])
        ]
        if ai.get("ai_status") == "SUCCESS"
        else [],
    }


def build_report(core, ai):
    """Core Result와 AI Result를 조합해 Template용 View Model(dict)을 만든다."""
    return {
        "summary": _build_summary(core),
        "timeline": _build_timeline(core),
        "actions": _build_actions(core),
        "analysis": _build_analysis(ai),
        "details": _build_details(core, ai),
    }
