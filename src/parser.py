import json
import re
from datetime import datetime
from pathlib import Path

DEVICES_PATH = Path(__file__).resolve().parent.parent / "data" / "devices.json"
LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<device_id>\S+)\s+(?P<message>.+)$"
)
SEVERITY_LABELS = {
    "0": "CRITICAL", "1": "CRITICAL", "2": "CRITICAL", "3": "ERROR",
    "4": "WARNING", "5": "NOTICE", "6": "INFO", "7": "DEBUG",
}


def classify_event(message):
    text = message.lower()
    if any(marker in text for marker in (
        "administratively down", "err-disable", "errdisable", "loop-protect",
    )):
        return "PORT_DISABLED"
    if "returned to normal" in text or (
        "cpu" in text and "decreased" in text
    ) or re.search(r"storm[-_]control.*\bclear\b", text):
        return "NORMAL_RESTORED"
    if "macflap" in text or "flapping" in text:
        return "MAC_FLAPPING"
    if "loopguard" in text or "loop guard" in text or "loop detected" in text:
        return "LOOP_DETECTED"
    if "broadcast" in text and any(
        marker in text for marker in ("threshold exceeded", "high", "storm")
    ):
        return "BROADCAST_HIGH"
    if "cpu" in text and any(
        marker in text for marker in ("cpuhog", "reached", "high")
    ):
        return "CPU_HIGH"
    if "changed state to down" in text:
        return "LINK_DOWN"
    if "changed state to up" in text:
        return "LINK_UP"
    if re.search(r"%[^\s:]+-4-[^\s:]+", message) or "warning" in text:
        return "WARNING"
    return "UNKNOWN"


def parse_line(raw, source_line, devices):
    raw = raw.rstrip("\r\n")
    event = {
        "timestamp": None,
        "device_id": None,
        "device_name": None,
        "location": None,
        "event_type": "UNKNOWN",
        "severity": None,
        "interface": None,
        "message": raw,
        "source_line": source_line,
        "raw": raw,
    }
    match = LOG_PATTERN.match(raw)
    if not match:
        return event

    device_id = match["device_id"]
    message = match["message"]
    device = devices.get(device_id, {})
    event.update(
        device_id=device_id,
        device_name=device.get("display_name"),
        location=device.get("location"),
        message=message,
    )
    try:
        event["timestamp"] = datetime.strptime(
            match["timestamp"], "%Y-%m-%d %H:%M:%S"
        ).isoformat()
    except ValueError:
        return event

    event["event_type"] = classify_event(message)
    severity = re.search(r"%[^\s:]+-([0-7])-[^\s:]+", message)
    if severity:
        event["severity"] = SEVERITY_LABELS[severity[1]]
    interface = re.search(
        r"\b(?:Gi|Fa|Te|Eth)\d+(?:/\d+)+\b|\b\d+F\s+uplink\b",
        message, re.IGNORECASE,
    )
    if interface:
        event["interface"] = interface[0]
    if device.get("device_role") == "BACKBONE_SWITCH":
        floor = re.search(r"\b(\d+)F\b", message, re.IGNORECASE)
        if floor:
            access = next((
                entry for entry in devices.values()
                if entry.get("device_role") == "ACCESS_SWITCH"
                and entry.get("floor") == int(floor[1])
            ), None)
            if access:
                event["location"] = access["location"]
    return event


def parse_log(log_path, devices_path=DEVICES_PATH):
    entries = json.loads(Path(devices_path).read_text(encoding="utf-8"))["devices"]
    devices = {entry["device_id"]: entry for entry in entries}
    with Path(log_path).open(encoding="utf-8") as source:
        return [
            parse_line(raw, source_line, devices)
            for source_line, raw in enumerate(source, start=1)
            if raw.strip()
        ]