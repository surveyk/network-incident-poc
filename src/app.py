import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from src.ai import get_ai_result
from src.report import build_report

BASE_DIR = Path(__file__).resolve().parent.parent
CORE_MOCK_PATH = BASE_DIR / "data" / "mock" / "core_2f.json"

app = FastAPI(title="Network Incident PoC")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def load_core():
    # 실제 Core 연결 시 이 함수만 교체한다.
    return json.loads(CORE_MOCK_PATH.read_text(encoding="utf-8"))


@app.get("/")
def index(request: Request):
    try:
        report = build_report(load_core(), get_ai_result())
    except (OSError, ValueError, KeyError, TypeError):
        # Core 입력 오류는 AI 실패와 구분해 표시한다.
        return templates.TemplateResponse(
            request, "index.html", {"error": "분석 실패: Core 분석 결과를 처리할 수 없습니다."}, status_code=500
        )
    return templates.TemplateResponse(request, "index.html", {"report": report})
