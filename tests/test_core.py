import json
from pathlib import Path

import pytest

from src.core import analyze
from src.impact import SERVICES_PATH, build_impact
from src.parser import DEVICES_PATH, classify_event, parse_line, parse_log

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def devices():
    entries = json.loads(DEVICES_PATH.read_text(encoding="utf-8"))["devices"]
    return {entry["device_id"]: entry for entry in entries}


@pytest.mark.parametrize("message, event_type", [
    ("%SW_MATM-4-MACFLAP_NOTIF: Host is flapping", "MAC_FLAPPING"),
    ("%SW_MATM-4-MACFLAP_NOTIF: MAC addresses are changing", "MAC_FLAPPING"),
    ("%SPANTREE-2-LOOPGUARD_BLOCK: Loop guard detected", "LOOP_DETECTED"),
    ("%STORM_CONTROL-3-ALERT: Broadcast traffic threshold exceeded", "BROADCAST_HIGH"),
    ("%SYS-4-CPUHOG: CPU utilization reached 92 percent", "CPU_HIGH"),
    ("%LINK-3-UPDOWN: Interface Gi1/0/48 changed state to down", "LINK_DOWN"),
    ("%LINEPROTO-5-UPDOWN: Line protocol on 2F uplink changed state to up", "LINK_UP"),
    ("%LINK-5-CHANGED: Interface Gi1/0/19 administratively down", "PORT_DISABLED"),
    ("%LINK-3-UPDOWN: ERR-DISABLE changed state to down", "PORT_DISABLED"),
    ("%PORT_CHANGE-3-ERR_DISABLE: errdisable on Gi1/0/19", "PORT_DISABLED"),
    ("%LINK-3-UPDOWN: loop-protect changed state to down", "PORT_DISABLED"),
    ("%SYS-5-CPU: CPU utilization decreased to 48 percent", "NORMAL_RESTORED"),
    ("%SYS-5-CPU: CPU utilization returned to normal at 31 percent", "NORMAL_RESTORED"),
    ("%STORM_CONTROL-5-CLEAR: Broadcast traffic returned to normal", "NORMAL_RESTORED"),
    ("%STORM-CONTROL-5-CLEAR: threshold cleared", "NORMAL_RESTORED"),
    ("%SYS-4-OTHER: Unrecognized warning", "WARNING"),
    ("%SYS-5-CONFIG_I: Configured from console by admin", "UNKNOWN"),
    ("Unrecognized message", "UNKNOWN"),
])
def test_event_classification(message, event_type):
    assert classify_event(message) == event_type


@pytest.mark.parametrize("sample, line_count", [
    ("link_1f", 9), ("loop_2f", 24), ("link_3f", 9),
])
def test_parse_samples_preserves_every_nonempty_line(sample, line_count):
    path = DATA_DIR / "sample_logs" / f"{sample}.log"
    lines = path.read_text(encoding="utf-8").splitlines()
    events = parse_log(path)

    assert len(lines) == len(events) == line_count
    assert all(line.strip() for line in lines)
    assert [event["source_line"] for event in events] == list(range(1, line_count + 1))
    assert [event["raw"] for event in events] == lines
    assert all(event["timestamp"] is not None for event in events)


@pytest.mark.parametrize("sample", ["link_1f", "loop_2f", "link_3f"])
def test_expected_facts_match_parsed_source_lines(sample):
    expected = json.loads(
        (DATA_DIR / "expected" / f"{sample}_expected.json").read_text(encoding="utf-8")
    )
    events = parse_log(DATA_DIR / "sample_logs" / f"{sample}.log")
    for fact in expected["facts"]:
        event = events[fact["source_line"] - 1]
        assert event["event_type"] == fact["type"]
        assert event["timestamp"] == fact["timestamp"]
        assert event["device_name"] == fact["device"]


def test_normalized_event_fields(devices):
    raw = "2026-09-30 10:21:11 SW-ACCESS-02 %SYS-4-CPUHOG: CPU utilization reached 92 percent"
    event = parse_line(raw + "\n", 8, devices)

    assert event == {
        "timestamp": "2026-09-30T10:21:11",
        "device_id": "SW-ACCESS-02",
        "device_name": devices["SW-ACCESS-02"]["display_name"],
        "location": devices["SW-ACCESS-02"]["location"],
        "event_type": "CPU_HIGH",
        "severity": "WARNING",
        "interface": None,
        "message": raw.split(" ", 3)[3],
        "source_line": 8,
        "raw": raw,
    }


@pytest.mark.parametrize("floor", [1, 2, 3])
def test_backbone_location_uses_floor_lookup(devices, floor):
    raw = f"2026-09-30 10:21:24 BACKBONE-SW %LINEPROTO-5-UPDOWN: Line protocol on {floor}F uplink changed state to down"
    event = parse_line(raw, 1, devices)

    assert event["device_name"] == devices["BACKBONE-SW"]["display_name"]
    assert event["location"] == devices[f"SW-ACCESS-{floor:02d}"]["location"]
    assert event["interface"] == f"{floor}F uplink"
    assert event["event_type"] == "LINK_DOWN"


def test_physical_interface_and_critical_severity(devices):
    events = parse_log(DATA_DIR / "sample_logs" / "loop_2f.log")
    assert events[5]["interface"] == "Gi1/0/19"
    assert events[5]["severity"] == "CRITICAL"
    assert events[16]["event_type"] == "PORT_DISABLED"
    assert events[16]["interface"] == "Gi1/0/19"
    assert events[17]["event_type"] == "NORMAL_RESTORED"
    assert events[20]["event_type"] == "NORMAL_RESTORED"
    assert events[21]["event_type"] == "NORMAL_RESTORED"
    assert events[8]["event_type"] == "UNKNOWN"


@pytest.mark.parametrize("raw", [
    "malformed log", "", "2026-02-30 10:00:00 SW-ACCESS-02 message",
])
def test_malformed_logs_are_preserved_as_unknown(devices, raw):
    event = parse_line(raw, 7, devices)
    assert event["event_type"] == "UNKNOWN"
    assert event["timestamp"] is None
    assert event["raw"] == raw
    assert event["source_line"] == 7


def test_unknown_device_does_not_invent_location(devices):
    event = parse_line(
        "2026-09-30 10:21:24 OTHER-SW %LINK-3-UPDOWN: Interface Gi1/0/48 changed state to down",
        1, devices,
    )
    assert event["device_id"] == "OTHER-SW"
    assert event["device_name"] is None
    assert event["location"] is None
    assert event["event_type"] == "LINK_DOWN"


def test_backbone_without_known_floor_keeps_its_inventory_location(devices):
    for message in ("Configured from console", "Line protocol on 99F uplink changed state to up"):
        event = parse_line(f"2026-09-30 10:21:24 BACKBONE-SW {message}", 1, devices)
        assert event["location"] == devices["BACKBONE-SW"]["location"]


def test_blank_lines_do_not_renumber_source_lines(tmp_path):
    path = tmp_path / "input.log"
    path.write_text(
        "2026-09-30 10:21:02 SW-ACCESS-02 unknown\n\n"
        "2026-09-30 10:21:03 SW-ACCESS-02 unknown\n",
        encoding="utf-8",
    )
    assert [event["source_line"] for event in parse_log(path)] == [1, 3]


def test_golden_sample_core_matches_expected():
    expected = json.loads(
        (DATA_DIR / "expected" / "loop_2f_expected.json").read_text(encoding="utf-8")
    )
    result = analyze(DATA_DIR / "sample_logs" / "loop_2f.log")

    assert result == expected


@pytest.mark.parametrize("sample, sequence", [("link_1f", 2), ("link_3f", 3)])
def test_link_sample_core_matches_expected(sample, sequence):
    expected = json.loads(
        (DATA_DIR / "expected" / f"{sample}_expected.json").read_text(encoding="utf-8")
    )
    assert analyze(DATA_DIR / "sample_logs" / f"{sample}.log", incident_sequence=sequence) == expected


def test_core_does_not_depend_on_filename(tmp_path):
    source = DATA_DIR / "sample_logs" / "loop_2f.log"
    renamed = tmp_path / "arbitrary.log"
    renamed.write_bytes(source.read_bytes())
    assert analyze(renamed) == analyze(source)


def test_core_uses_changed_device_and_service_catalogs(tmp_path):
    inventory = json.loads(DEVICES_PATH.read_text(encoding="utf-8"))
    services = json.loads(SERVICES_PATH.read_text(encoding="utf-8"))
    for device in inventory["devices"]:
        if device["device_id"] == "SW-ACCESS-02":
            device.update(device_id="EDGE-X", display_name="Renamed access", location="Wing-A", floor=42)
    for service in services["services"]:
        service["floors"] = [42 if floor == 2 else floor for floor in service["floors"]]
        if service["service_id"] == "112SYSTEM":
            service.update(display_name="Mapped service", criticality="HIGH")
    inventory_path, services_path = tmp_path / "devices.json", tmp_path / "services.json"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    services_path.write_text(json.dumps(services), encoding="utf-8")
    source = (DATA_DIR / "sample_logs" / "loop_2f.log").read_text(encoding="utf-8")
    source_path = tmp_path / "arbitrary.log"
    source_path.write_text(source.replace("SW-ACCESS-02", "EDGE-X").replace("2F", "42F"), encoding="utf-8")

    result = analyze(source_path, devices_path=inventory_path, services_path=services_path)
    assert result["incident"]["primary_device"] == "Renamed access"
    assert result["incident"]["location"].startswith("Wing-A")
    assert result["impact"]["affected_services"][0]["name"] == "Mapped service"
    assert result["impact"]["overall_criticality"] == "HIGH"
    assert result["impact"]["recovery_priority"] == "P2"
    assert result["analysis_context"]["related_event_count"] == 17


def test_core_excludes_other_backbone_connections(tmp_path):
    source = (DATA_DIR / "sample_logs" / "loop_2f.log").read_text(encoding="utf-8")
    path = tmp_path / "input.log"
    path.write_text(
        source + "\n2026-09-30 10:21:35 BACKBONE-SW %STORM_CONTROL-3-ALERT: Broadcast traffic threshold exceeded on 3F uplink\n",
        encoding="utf-8",
    )
    assert analyze(path) == analyze(DATA_DIR / "sample_logs" / "loop_2f.log")


def test_core_without_backbone_logs_still_analyzes(tmp_path):
    source = (DATA_DIR / "sample_logs" / "loop_2f.log").read_text(encoding="utf-8")
    path = tmp_path / "input.log"
    path.write_text("\n".join(line for line in source.splitlines() if "BACKBONE-SW" not in line), encoding="utf-8")

    result = analyze(path)
    assert result["incident"]["status"] == "RECOVERED"
    assert result["incident"]["related_devices"] == []
    assert result["incident"]["start_time"] == "2026-09-30T10:21:25"
    assert result["incident"]["recovery_time"] == "2026-09-30T10:22:11"
    assert result["analysis_context"]["log_source_count"] == 1


@pytest.mark.parametrize("removed_times, status", [
    ({"10:22:11", "10:22:13"}, "ACTIVE"),
    ({"10:22:13"}, "RECOVERING"),
    ({"10:22:16", "10:22:19", "10:22:08"}, "RECOVERING"),
])
def test_core_does_not_claim_incomplete_recovery(tmp_path, removed_times, status):
    source = (DATA_DIR / "sample_logs" / "loop_2f.log").read_text(encoding="utf-8")
    path = tmp_path / "input.log"
    path.write_text("\n".join(
        line for line in source.splitlines() if line.split()[1] not in removed_times
    ), encoding="utf-8")

    result = analyze(path)
    assert result["incident"]["status"] == status
    assert result["incident"]["end_time"] is None
    if removed_times & {"10:22:11", "10:22:13"}:
        assert result["incident"]["recovery_time"] is None


def test_new_link_down_after_recovery_keeps_incident_active(tmp_path):
    source = (DATA_DIR / "sample_logs" / "loop_2f.log").read_text(encoding="utf-8")
    path = tmp_path / "input.log"
    path.write_text(
        source + "\n2026-09-30 10:22:25 SW-ACCESS-02 %LINK-3-UPDOWN: Interface Gi1/0/48 changed state to down\n",
        encoding="utf-8",
    )
    result = analyze(path)
    assert result["incident"]["status"] == "RECOVERING"
    assert result["incident"]["recovery_time"] is None
    assert result["incident"]["end_time"] is None


def test_no_incident_is_not_fabricated(tmp_path):
    path = tmp_path / "input.log"
    path.write_text("2026-09-30 10:21:00 SW-ACCESS-02 %SYS-5-CONFIG_I: Configured from console\n", encoding="utf-8")
    with pytest.raises(ValueError, match="No incident"):
        analyze(path)


@pytest.mark.parametrize("sequence", [0, -1, True, "1"])
def test_incident_sequence_validation(sequence):
    with pytest.raises(ValueError, match="incident_sequence"):
        analyze(DATA_DIR / "sample_logs" / "loop_2f.log", incident_sequence=sequence)


def test_incident_sequence_is_supplied_by_caller():
    result = analyze(DATA_DIR / "sample_logs" / "loop_2f.log", incident_sequence=12)
    assert result["incident"]["incident_id"] == "INC-20260930-012"


def test_impact_uses_priority_from_catalog_and_ignores_disabled_services(tmp_path):
    catalog = json.loads(SERVICES_PATH.read_text(encoding="utf-8"))
    catalog["criticality_levels"]["VERY_HIGH"]["recovery_priority"] = "P0"
    path = tmp_path / "services.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")
    assert build_impact(2, path)["recovery_priority"] == "P0"

    for service in catalog["services"]:
        if service["service_id"] == "112SYSTEM":
            service["enabled"] = False
    path.write_text(json.dumps(catalog), encoding="utf-8")
    impact = build_impact(2, path)
    assert len(impact["affected_services"]) == 2
    assert impact["overall_criticality"] == "NORMAL"
    assert impact["recovery_priority"] == "P3"


def test_unmapped_services_fail_explicitly():
    with pytest.raises(ValueError, match="No services"):
        build_impact(42)