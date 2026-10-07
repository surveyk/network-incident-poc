import json
from pathlib import Path

from src.impact import SERVICES_PATH, build_impact
from src.parser import DEVICES_PATH, parse_log

PRECURSOR_TYPES = {"MAC_FLAPPING", "LOOP_DETECTED", "BROADCAST_HIGH", "CPU_HIGH"}
ABNORMAL_TYPES = PRECURSOR_TYPES | {"LINK_DOWN", "PORT_DISABLED", "WARNING"}
SEVERITY_RANK = {"CRITICAL": 3, "ERROR": 2, "WARNING": 1}
FACT_TEXT = {
    "MAC_FLAPPING": "MAC 주소 반복 이동이 확인됨",
    "LOOP_DETECTED": "Loop Guard 관련 이벤트가 확인됨",
    "CPU_HIGH": "CPU 사용률 상승이 확인됨",
    "BROADCAST_HIGH": "{location} 방향 Broadcast 증가가 확인됨",
    "LINK_DOWN": "{location} 네트워크 연결 중단이 확인됨",
    "PORT_DISABLED": "장애 의심 포트가 차단됨",
    "LINK_UP": "{location} 네트워크 연결 복구가 확인됨",
}
TIMELINE_TEXT = {
    "MAC_FLAPPING": ("PRECURSOR", "MAC 주소 반복 이동 감지"),
    "BROADCAST_HIGH": ("PRECURSOR", "{location} 방향 Broadcast 트래픽 증가"),
    "LINK_DOWN": ("INCIDENT", "{location} 네트워크 연결 중단"),
    "PORT_DISABLED": ("ACTION", "장애 의심 포트 차단"),
    "LINK_UP": ("RECOVERY", "{location} 네트워크 연결 복구"),
}


def _select_primary(events, devices):
    candidates = {}
    for event in events:
        device = devices.get(event["device_id"], {})
        if device.get("device_role") != "ACCESS_SWITCH" or not device.get("enabled", True):
            continue
        if event["event_type"] in ABNORMAL_TYPES:
            candidates.setdefault(event["device_id"], []).append(event)
    if not candidates:
        raise ValueError("No incident found on a known access device")
    device_id = max(candidates, key=lambda candidate: (
        max(SEVERITY_RANK.get(event["severity"], 0) for event in candidates[candidate]),
        len(candidates[candidate]),
    ))
    return devices[device_id]


def _connection_state(events):
    links = {}
    latest = {}
    resources = {}
    for event in events:
        event_type = event["event_type"]
        key = (event["device_id"], event["interface"])
        if event_type == "LINK_DOWN":
            links[key] = event
            latest[key] = event
        elif event_type == "LINK_UP" and key in links:
            latest[key] = event
        if event_type in {"CPU_HIGH", "BROADCAST_HIGH", "NORMAL_RESTORED"}:
            message = event["message"].lower()
            resource = "cpu" if "cpu" in message else "broadcast"
            resources[(event["device_id"], resource)] = event_type
    restored = [event for event in latest.values() if event["event_type"] == "LINK_UP"]
    if not links:
        return None, "UNKNOWN"
    if len(restored) != len(links):
        return None, "RECOVERING" if restored else "ACTIVE"
    recovery = max(restored, key=lambda event: event["timestamp"])
    status = "RECOVERED" if all(
        event_type == "NORMAL_RESTORED" for event_type in resources.values()
    ) else "RECOVERING"
    return recovery, status


def _representatives(events, primary, recovery):
    selected = {}
    for event in events:
        event_type = event["event_type"]
        if event_type not in FACT_TEXT or event_type == "LINK_UP":
            continue
        previous = selected.get(event_type)
        if previous is None:
            selected[event_type] = event
        elif event_type in {"MAC_FLAPPING", "LOOP_DETECTED", "CPU_HIGH"}:
            if previous["device_id"] != primary["device_id"] and event["device_id"] == primary["device_id"]:
                selected[event_type] = event
    if recovery:
        selected["LINK_UP"] = recovery
    return sorted(selected.values(), key=lambda event: (event["timestamp"], event["source_line"]))


def _build_evidence(events, location):
    facts = []
    timeline = []
    for event in events:
        event_type = event["event_type"]
        facts.append({
            "type": event_type,
            "timestamp": event["timestamp"],
            "device": event["device_name"],
            "source_line": event["source_line"],
            "text": FACT_TEXT[event_type].format(location=location),
        })
        if event_type in TIMELINE_TEXT:
            stage, text = TIMELINE_TEXT[event_type]
            timeline.append({
                "timestamp": event["timestamp"],
                "stage": stage,
                "device": event["device_name"],
                "event_type": event_type,
                "summary": text.format(location=location),
            })
    return timeline, facts


def _build_link_evidence(events, primary, devices):
    selected = {}
    for event in events:
        if event["event_type"] not in {"LINK_DOWN", "LINK_UP"}:
            continue
        key = (event["device_id"], event["interface"], event["event_type"])
        if key not in selected or event["event_type"] == "LINK_UP":
            selected[key] = event
    links = sorted(selected.values(), key=lambda event: (event["timestamp"], event["source_line"]))
    first_is_backbone = devices[links[0]["device_id"]]["device_role"] == "BACKBONE_SWITCH"
    location = primary["location"]
    timeline, facts = [], []
    for position, event in enumerate(links):
        backbone = devices[event["device_id"]]["device_role"] == "BACKBONE_SWITCH"
        down = event["event_type"] == "LINK_DOWN"
        state = "단절" if down else "복구"
        particle = "이" if down else "가"
        if backbone:
            prefix = "백본스위치에서" if position == 0 else "백본스위치에서도"
            if not down and first_is_backbone:
                prefix = "백본스위치의"
            fact_text = f"{prefix} {location} 연결 {state}{particle} 확인됨"
            if down:
                text = f"백본에서 {location} 연결 단절 감지" if position == 0 else f"백본에서도 {location} 연결 단절 확인"
            else:
                text = f"백본의 {location} 연결 복구" if first_is_backbone else f"백본에서도 {location} 연결 복구 확인"
        else:
            suffix = "에서도" if down and first_is_backbone else "의"
            fact_text = f"{primary['display_name']}{suffix} Uplink {state}{particle} 확인됨"
            if down:
                text = f"{location} 네트워크 연결 단절 감지" if position == 0 else f"{primary['display_name']}에서도 연결 단절 확인"
            else:
                text = f"{primary['display_name']} 연결 복구 확인" if first_is_backbone else f"{primary['display_name']} 연결 복구"
        facts.append({
            "type": event["event_type"], "timestamp": event["timestamp"],
            "device": event["device_name"], "source_line": event["source_line"],
            "text": fact_text,
        })
        timeline.append({
            "timestamp": event["timestamp"], "stage": "INCIDENT" if down else "RECOVERY",
            "device": event["device_name"], "event_type": event["event_type"], "summary": text,
        })
    return timeline, facts


def analyze(log_path, incident_sequence=1, devices_path=DEVICES_PATH, services_path=SERVICES_PATH):
    if not isinstance(incident_sequence, int) or isinstance(incident_sequence, bool) or incident_sequence < 1:
        raise ValueError("incident_sequence must be a positive integer")
    entries = json.loads(Path(devices_path).read_text(encoding="utf-8"))["devices"]
    devices = {entry["device_id"]: entry for entry in entries}
    events = sorted(
        (event for event in parse_log(log_path, devices_path) if event["timestamp"] is not None),
        key=lambda event: (event["timestamp"], event["source_line"]),
    )
    primary = _select_primary(events, devices)
    pool = [
        event for event in events
        if event["device_id"] == primary["device_id"] or (
            devices.get(event["device_id"], {}).get("device_role") == "BACKBONE_SWITCH"
            and devices[event["device_id"]].get("enabled", True)
            and event["location"] == primary["location"]
        )
    ]
    detected = next(event["timestamp"] for event in pool if event["event_type"] in ABNORMAL_TYPES)
    pool = [event for event in pool if event["timestamp"] >= detected]
    start = next((event["timestamp"] for event in pool if event["event_type"] == "LINK_DOWN"), None)
    recovery, status = _connection_state(pool)
    recovery_time = recovery["timestamp"] if recovery else None
    end_time = None
    if status == "RECOVERED":
        end_time = max(
            [recovery_time] + [event["timestamp"] for event in pool if event["event_type"] == "NORMAL_RESTORED"]
        )
    boundary = end_time or max(
        event["timestamp"] for event in pool
        if event["event_type"] in ABNORMAL_TYPES | {"LINK_UP", "NORMAL_RESTORED"}
    )
    related = [event for event in pool if event["timestamp"] <= boundary]
    related_ids = list(dict.fromkeys(
        [primary["device_id"]] + [event["device_id"] for event in related]
    ))
    if any(event["event_type"] in PRECURSOR_TYPES for event in related):
        representatives = _representatives(related, primary, recovery)
        timeline, facts = _build_evidence(representatives, primary["location"])
    elif any(event["event_type"] == "LINK_DOWN" for event in related):
        timeline, facts = _build_link_evidence(related, primary, devices)
    else:
        timeline, facts = _build_evidence(_representatives(related, primary, recovery), primary["location"])
    return {
        "incident": {
            "incident_id": f"INC-{detected[:10].replace('-', '')}-{incident_sequence:03d}",
            "location": f"{primary['location']} 네트워크",
            "primary_device": primary["display_name"],
            "related_devices": [devices[device_id]["display_name"] for device_id in related_ids[1:]],
            "detected_time": detected,
            "start_time": start,
            "recovery_time": recovery_time,
            "end_time": end_time,
            "status": status,
        },
        "impact": build_impact(primary["floor"], services_path),
        "timeline": timeline,
        "facts": facts,
        "recurrence": {"status": "UNKNOWN", "similar_incident_count": None},
        "analysis_context": {
            "log_source_count": len(related_ids),
            "devices_analyzed": [devices[device_id]["display_name"] for device_id in related_ids],
            "related_event_count": len(related),
        },
    }