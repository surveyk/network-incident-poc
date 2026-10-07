import json
from pathlib import Path

SERVICES_PATH = Path(__file__).resolve().parent.parent / "data" / "services.json"


def build_impact(floor, services_path=SERVICES_PATH):
    catalog = json.loads(Path(services_path).read_text(encoding="utf-8"))
    services = [
        service for service in catalog["services"]
        if service.get("enabled", True) and floor in service["floors"]
    ]
    if not services:
        raise ValueError("No services mapped to incident location")
    services.sort(key=lambda service: service["scope"] == "COMMON")
    levels = catalog["criticality_levels"]
    criticality = min(
        (service["criticality"] for service in services),
        key=lambda level: int(levels[level]["recovery_priority"][1:]),
    )
    return {
        "affected_services": [
            {
                "category": service["category"],
                "name": service["display_name"],
                "criticality": service["criticality"],
            }
            for service in services
        ],
        "impact_basis": "LOCATION_MAPPING",
        "verification_status": "UNVERIFIED",
        "overall_criticality": criticality,
        "recovery_priority": levels[criticality]["recovery_priority"],
    }