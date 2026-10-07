import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from src.ai import get_ai_result
from src.core import analyze
from src.report import build_report

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Network Incident PoC")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def load_core():
    configured_path = os.getenv("INCIDENT_LOG_PATH", "").strip()
    if not configured_path:
        raise ValueError("INCIDENT_LOG_PATH is required")
    log_path = Path(configured_path)
    if not log_path.is_absolute():
        log_path = BASE_DIR / log_path
    return analyze(log_path, incident_sequence=1)


@app.get("/")
def index(request: Request):
    try:
        core_result = load_core()
        ai_result = get_ai_result(core_result)
        report = build_report(core_result, ai_result)
    except (OSError, ValueError, KeyError, TypeError):
        # Core 입력 오류는 AI 실패와 구분해 표시한다.
        return templates.TemplateResponse(
            request, "index.html", {"error": "분석 실패: Core 분석 결과를 처리할 수 없습니다."}, status_code=500
        )
    return templates.TemplateResponse(request, "index.html", {"report": report})
