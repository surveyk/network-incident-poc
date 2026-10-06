import json
import os
from pathlib import Path

MOCK_DIR = Path(__file__).resolve().parent.parent / "data" / "mock"

MOCK_FILES = {
    "2f": "ai_2f.json",
    "unavailable": "ai_unavailable.json",
}


def _fallback(status):
    return {
        "ai_status": status,
        "summary": None,
        "hypotheses": [],
        "additional_checks": [],
    }


def _is_str_list(value):
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def _is_valid(result):
    if not isinstance(result, dict):
        return False
    if result.get("ai_status") not in ("SUCCESS", "UNAVAILABLE", "ERROR"):
        return False
    summary = result.get("summary")
    if summary is not None and not isinstance(summary, str):
        return False
    if not _is_str_list(result.get("additional_checks")):
        return False
    hypotheses = result.get("hypotheses")
    if not isinstance(hypotheses, list):
        return False
    for h in hypotheses:
        if not isinstance(h, dict) or not isinstance(h.get("cause"), str):
            return False
        if not _is_str_list(h.get("evidence")) or not _is_str_list(h.get("uncertainty")):
            return False
    return True


def get_ai_result(scenario="2f"):
    """AI Result(docs/ai-spec.md 구조)를 반환한다. 실패 시 Core와 무관하게 Fallback을 반환한다."""
    if os.getenv("AI_MODE", "mock") != "mock":
        return _fallback("UNAVAILABLE")  # Azure 연동은 미구현

    filename = MOCK_FILES.get(scenario)
    if filename is None:
        return _fallback("ERROR")

    try:
        result = json.loads((MOCK_DIR / filename).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _fallback("ERROR")

    return result if _is_valid(result) else _fallback("ERROR")
