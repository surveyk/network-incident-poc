# Network Incident PoC
# 1인 D-Day Vibe Coding 실행 절차

## 1. 목적

본 문서는 Network Incident PoC를 **1인이 하루 안에 End-to-End 형태로 구현하기 위한 최종 D-Day 실행절차**를 정의한다.

기존 `JOB_261007_A.md`, `JOB_261007_B.md` 및 관련 Specification은 상세 설계 참고자료로 유지한다.

D-Day 실제 개발은 본 문서를 기준으로 진행한다.

목표는 기존 A/B 전체 기능을 모두 구현하는 것이 아니라 다음 핵심 흐름을 실제로 동작시키는 것이다.

```text
Raw Log
↓
Core Analysis
↓
Incident Reconstruction
↓
Business Impact / Priority
↓
Timeline / Facts
↓
AI Cause Hypothesis
↓
Manager Report / Web
```

---

# 2. 최종 역할 구조

1인 개발이지만 기존 역할 경계는 유지한다.

```text
Core Analysis
= Fact / Rule

AI Analysis
= Inference

Report Builder
= Composition

Web
= Presentation

Human
= Final Decision
```

Core와 AI의 판단영역을 섞지 않는다.

---

# 3. D-Day 성공 기준

하루 종료 시 다음 흐름이 동작하면 PoC 성공으로 판단한다.

```text
2층 Sample Log
↓
2층 네트워크 장애 식별
↓
112시스템 / 온나라 / 폴넷 영향 가능
↓
VERY_HIGH
↓
P1
↓
RECOVERED
↓
Timeline / Facts 생성
↓
AI 원인 후보
↓
관리자 장애 상황보고
```

1층과 3층은 Core가 2층에 하드코딩되지 않았음을 검증하는 Validation Sample로 사용한다.

---

# 4. 성공등급

## Level 1 — 최소 성공

```text
Raw Log
↓
Core Analysis
↓
Impact / Priority
↓
Timeline / Facts
↓
Web Report
```

이 수준까지 완료하면 기본 PoC 성공으로 판단한다.

## Level 2 — 목표 성공

```text
Level 1
+
Mock AI
+
AI 분석 포함 관리자 보고서
```

안정적인 Demo 가능 상태로 본다.

## Level 3 — 최상 성공

```text
Level 2
+
실제 Azure OpenAI
```

시간이 허용되는 경우 목표로 한다.

---

# 5. 기능 우선순위

## P0 — 반드시 완료

```text
1. Sample Log Parsing
2. Event Classification
3. 관련 Event 선별
4. Incident 위치 / 시간 판단
5. 영향 가능 업무 Mapping
6. Criticality / Recovery Priority
7. Timeline
8. Facts
9. Core Result
10. 2층 Golden Sample PASS
11. 1층 / 3층 Validation
12. 관리자 Report / Web
```

## P1 — 가능하면 완료

```text
13. Mock AI
14. AI 결과 Report 연결
15. AI Failure Fallback
16. Azure OpenAI 실제 연결
```

## P2 — 시간 부족 시 제외

```text
AI Summary 문장 고도화
화려한 UI
별도 Dashboard
그래프
Topology
파일 Upload
추가 Web Route
복잡한 Retry
추가 Sample
대규모 Refactoring
복잡한 Class 계층
RAG
Vector DB
Agent
자동복구
```

---

# 6. Git 시작

D-Day 작업 Branch:

```text
feature/solo-poc
```

새 노트북에서는 다음 순서로 시작한다.

```powershell
git clone https://github.com/surveyk/network-incident-poc.git

cd network-incident-poc

git checkout -b feature/solo-poc

git status

git branch -vv
```

`main`에서는 직접 개발하지 않는다.

---

# 7. Repository 확인

개발 전 다음 파일이 존재하는지 확인한다.

```text
.github/
└── copilot-instructions.md

docs/
├── data-spec.md
├── interface-spec.md
├── flowchart.md
├── report-spec.md
├── ai-spec.md
├── report-builder-spec.md
├── web-spec.md
├── azure-openai-spec.md
└── b-test-spec.md

data/
├── devices.json
├── services.json
├── sample_logs/
├── expected/
└── mock/

JOB_261007_A.md
JOB_261007_B.md
JOB_261007_SOLO.md
```

---

# 8. 1단계 — Repository 분석

처음에는 코드를 작성하지 않는다.

## Prompt

```text
Network Incident PoC를 오늘 하루 안에 1인이 구현하려고 한다.

기존 문서는 2인 개발 기준으로 작성되어 있지만,
오늘은 End-to-End PoC 완성을 최우선으로 한다.

다음 문서를 확인해줘.

1. .github/copilot-instructions.md
2. docs/data-spec.md
3. docs/interface-spec.md
4. docs/report-spec.md
5. docs/ai-spec.md
6. docs/report-builder-spec.md
7. docs/web-spec.md

그리고 다음 데이터도 확인해줘.

- data/devices.json
- data/services.json
- data/sample_logs/
- data/expected/
- data/mock/

아직 코드를 작성하지 마.

다음만 정리해줘.

1. 현재 Repository 구조
2. 오늘 반드시 구현해야 할 최소 기능
3. 2층 Golden Sample End-to-End 흐름
4. 기존 설계 중 하루 개발에 불필요한 과설계
5. 가장 단순한 src / tests 구조
6. Specification 간 충돌 또는 모호점

새로운 기능은 제안하지 마.
```

---

# 9. 권장 최소 개발구조

하루 PoC이므로 구조를 단순화한다.

```text
src/
├── parser.py
├── analyzer.py
├── impact.py
├── core.py
├── ai.py
├── report.py
└── app.py

templates/
└── index.html

tests/
├── test_core.py
├── test_ai.py
└── test_app.py
```

필요한 경우에만 파일을 추가 분리한다.

파일 수 자체를 목표로 하지 않는다.

---

# 10. 2단계 — Core 최소 구현

가장 먼저 2층 Golden Sample을 기준으로 Core를 구현한다.

입력:

```text
data/sample_logs/loop_2f.log
```

출력:

```json
{
  "incident": {},
  "impact": {},
  "timeline": [],
  "facts": [],
  "recurrence": {},
  "analysis_context": {}
}
```

## Prompt

```text
이제 Network Incident Core 최소기능을 구현하자.

오늘 하루 PoC이므로
복잡한 abstraction보다 단순하고 테스트 가능한 구조를 우선한다.

먼저 2층 Golden Sample이 동작하도록 구현하되
특정 층이나 Sample 이름을 하드코딩하면 안 된다.

반드시 다음 데이터를 사용한다.

data/devices.json
data/services.json

입력:
data/sample_logs/loop_2f.log

출력:
docs/interface-spec.md 구조

{
  "incident": {},
  "impact": {},
  "timeline": [],
  "facts": [],
  "recurrence": {},
  "analysis_context": {}
}

Core 내부에는 최소 다음 기능이 필요하다.

- Parsing
- Event Classification
- 관련 Event 선별
- Incident 위치 / 시간 판단
- 영향 가능 업무 Mapping
- Criticality / Recovery Priority
- Timeline
- Facts
- Recurrence
- Analysis Context

우선 구현 후
data/expected/loop_2f_expected.json과 비교하는
test_core.py를 작성해줘.

AI나 Web은 아직 구현하지 마.
```

---

# 11. Core 필수 Event

지원 Event:

```text
MAC_FLAPPING
LOOP_DETECTED
BROADCAST_HIGH
CPU_HIGH
LINK_DOWN
LINK_UP
PORT_DISABLED
WARNING
UNKNOWN
```

장비정보는 `data/devices.json`을 사용한다.

업무정보는 `data/services.json`을 사용한다.

Python 코드에서 층, 업무명, 중요도를 하드코딩하지 않는다.

---

# 12. 2층 Golden Sample 성공기준

Incident:

```text
location
= 2층 네트워크

status
= RECOVERED
```

Impact:

```text
affected_services
= 112시스템
  온나라
  폴넷

overall_criticality
= VERY_HIGH

recovery_priority
= P1

impact_basis
= LOCATION_MAPPING

verification_status
= UNVERIFIED
```

`affected_services`는 실제 서비스 장애가 아니라 **영향 가능 업무**를 의미한다.

---

# 13. 2층 Timeline

관리자용 핵심 흐름:

```text
MAC Flapping
↓
Broadcast 증가
↓
Link Down
↓
의심 포트 차단
↓
Link Up
```

전체 Event를 Timeline에 넣지 않는다.

4~6개 핵심 Event만 보여준다.

---

# 14. Facts

Facts에는 로그에서 직접 확인 가능한 사실만 포함한다.

가능하면 다음 필드를 유지한다.

```text
type
timestamp
device
source_line
text
```

금지:

```text
Loop가 최종 장애원인이다

케이블 연결 오류가 원인이다

112시스템이 실제 중단되었다
```

위 내용은 AI 또는 운영자 판단영역이다.

---

# 15. Core 테스트

실행:

```powershell
pytest -q
```

2층 Golden Sample이 PASS해야 한다.

12시 이전 목표:

```text
2F Golden Sample PASS
```

---

# 16. 3단계 — 1층 / 3층 Validation

2층 PASS 후 바로 다른 Sample을 검증한다.

## 1층

```text
1층 네트워크
KICS(킥스)
온나라
폴넷
HIGH
P2
RECOVERED
```

## 3층

```text
3층 네트워크
TCS
온나라
폴넷
HIGH
P2
RECOVERED
```

## Prompt

```text
이제 동일 Core 구현으로
1층과 3층 Validation을 수행하자.

입력:

data/sample_logs/link_1f.log
data/sample_logs/link_3f.log

Expected:

data/expected/link_1f_expected.json
data/expected/link_3f_expected.json

목적은 2층 Golden Sample에
하드코딩된 구현이 없는지 확인하는 것이다.

FAIL이 있다면
Expected를 코드에 맞춰 수정하지 말고
구현 문제인지 Specification 문제인지 먼저 구분해줘.

최소 범위만 수정해줘.
```

---

# 17. Core 완료기준

```text
2F Golden Sample PASS
1F Validation PASS
3F Validation PASS
pytest PASS
```

여기까지 완료되면 Core 개발을 종료한다.

불필요한 Refactoring을 시작하지 않는다.

---

# 18. 4단계 — 관리자 Report / Web

AI보다 먼저 Web을 구현한다.

이유:

```text
Core
↓
Report
↓
Web
```

만으로도 기본 Demo가 가능하기 때문이다.

## Prompt

```text
Core Result를 이용해
FastAPI + Jinja2 기반의 최소 관리자 장애 상황보고 화면을 구현하자.

화면에는 다음만 표시한다.

1. 장애 요약
2. 장애경과
3. 조치내용
4. 추정원인 / 추가확인
5. 기술 상세정보

아직 실제 Azure OpenAI가 없어도 동작해야 한다.

AI 분석이 없는 경우
'AI 분석 미실행' 또는 이에 준하는 상태를 표시해줘.

Dashboard나 화려한 UI는 만들지 마.

공문서형 장애 상황보고서처럼
단순하고 읽기 쉽게 구현해줘.

Report Builder는 A Core 값을 다시 판단하면 안 된다.
```

---

# 19. Web 최소 성공기준

화면에 다음이 표시되면 기본 Web 성공이다.

```text
2층 네트워크

112시스템

매우 높음

P1 / 최우선

복구 완료

Timeline

조치내용
```

---

# 20. 조치 / 복구 표현 원칙

시간적으로 조치 이후 복구가 발생했다고 해서 직접적인 인과관계로 확정하지 않는다.

사용 가능:

```text
장애 의심 포트 차단 이후
네트워크 연결 복구가 확인됨
```

사용 금지:

```text
포트 차단으로 네트워크가 복구됨
```

원칙:

```text
Before / After
≠
Confirmed Cause / Effect
```

---

# 21. 5단계 — Mock AI

Web이 완료된 후 Mock AI를 연결한다.

입력:

```text
data/mock/ai_2f.json
```

## Prompt

```text
data/mock/ai_2f.json을 이용해서
AI 분석 결과를 관리자 보고서에 연결하자.

표시:

- 원인 후보
- 근거
- 불확실성
- 추가확인

AI Summary는 보조정보로만 사용한다.

AI 정보의 중요도는 다음 순서로 본다.

1. hypotheses
2. evidence
3. uncertainty
4. additional_checks
5. summary

AI가 다음 Core 값을 변경하면 안 된다.

- 장애 위치
- 영향 가능 업무
- 중요도
- 복구 우선순위
- 현재 상태
- Facts

Mock Core + Mock AI + Report + Web이
End-to-End로 동작하는지 테스트해줘.
```

---

# 22. Mock AI 성공기준

```text
Core
+
Mock AI
↓
Report
↓
Web
```

화면에 다음이 표시된다.

```text
L2 Loop 가능성

근거

불확실성

추가 확인사항
```

이 단계까지 완료하면 **Level 2 목표 성공**으로 판단한다.

---

# 23. AI Failure Fallback

시간이 허용되면 다음도 확인한다.

입력:

```text
data/mock/ai_unavailable.json
```

기대:

```text
장애 요약 정상

장애경과 정상

조치내용 정상

P1 유지

중요도 유지

상태 유지

AI 영역만 사용 불가
```

AI 실패 때문에 Web 전체가 실패하면 안 된다.

---

# 24. 6단계 — Azure OpenAI

Mock End-to-End가 완료된 뒤에만 실제 Azure를 연결한다.

환경변수:

```text
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT
AI_MODE
```

API Key는 코드나 Git에 저장하지 않는다.

---

# 25. Azure AI 역할

AI가 생성:

```text
hypotheses
evidence
uncertainty
additional_checks
summary
```

AI가 변경하거나 확정하지 않는 것:

```text
장애 위치
업무 중요도
복구 우선순위
실제 서비스 장애 여부
최종 장애원인
책임자
```

---

# 26. Azure Prompt 원칙

System Prompt에는 최소 다음을 포함한다.

```text
제공된 데이터만 주요 근거로 사용

존재하지 않는 Fact 생성 금지

장애 위치 변경 금지

업무 중요도 변경 금지

복구 우선순위 변경 금지

affected_services를 실제 장애로 확정 금지

Fact / Inference 구분

최종 장애원인 확정 금지

책임 / 과실 추정 금지

근거 부족 시 명시

조치 이후 복구됐다는 이유만으로
직접적인 원인과 결과로 확정 금지
```

---

# 27. Azure 중단 기준

다음 문제로 시간이 과도하게 소요되면 실제 Azure 개발을 중단한다.

```text
인증 오류

SDK 버전 문제

Structured Output 문제

Deployment 설정 문제

Network 문제

복잡한 Response Parsing 문제
```

이 경우:

```text
AI_MODE=mock
```

으로 Demo를 유지한다.

Azure 실패 때문에 전체 PoC를 실패시키지 않는다.

---

# 28. 전체 테스트

최소 필수:

```text
2F Golden Sample        PASS
1F Validation           PASS
3F Validation           PASS
Core                    PASS
Report                  PASS
Web                     PASS
Mock AI                 PASS
Mock End-to-End         PASS
pytest                  PASS
```

선택:

```text
Azure Smoke Test        PASS / 미완료
AI Failure Fallback     PASS / 미완료
```

---

# 29. D-Day 시간계획

## 09:00 ~ 09:30

```text
Git Clone
Branch 생성
Python 환경 확인
Repository 분석
```

## 09:30 ~ 12:00

```text
Core 구현
2층 Golden Sample
```

12시 목표:

```text
2F Golden Sample PASS
```

## 13:00 ~ 14:00

```text
1층 / 3층 Validation
Core 보완
```

## 14:00 ~ 15:30

```text
Report
FastAPI
Web
```

15:30 목표:

```text
AI 없이 Web Demo 가능
```

## 15:30 ~ 16:00

```text
Mock AI 연결
```

16시 목표:

```text
Mock End-to-End PoC 완료
```

## 16:00 ~ 17:00

```text
Azure OpenAI 실제 연결
```

성공하면 실제 AI Demo.

실패하면 Mock 유지.

## 17:00 ~ 18:00

```text
전체 Test
Bug Fix
Demo 점검
Git Commit / Push
```

---

# 30. 시간별 Go / Stop 기준

## 12:00

2층 Core가 완료되지 않았다면:

```text
새 기능 개발 중단

2층 Golden Sample 집중
```

## 15:30

Web이 완료되지 않았다면:

```text
Azure 개발 보류

Web 완성 우선
```

## 16:30

Azure가 안정적으로 연결되지 않았다면:

```text
Azure 개발 중단

Mock Mode 확정
```

## 17:00

새로운 기능 개발 금지.

다음만 수행한다.

```text
Test
Bug Fix
Demo
Git
```

---

# 31. 개발 중 Commit 원칙

작은 기능 단위로 Commit한다.

예:

```text
feat: add network incident core

test: add golden sample validation

feat: add incident report web view

feat: add mock ai analysis

feat: add azure openai integration
```

반드시 매 기능마다 Commit해야 하는 것은 아니지만,
안정적인 단계가 완성될 때마다 저장한다.

---

# 32. 문제 발생 시 기본 Prompt

```text
현재 문제를 먼저 분석해줘.

1. 증상
2. 실패한 Test
3. 관련 Specification
4. 원인 후보
5. 최소 수정안

을 먼저 정리해줘.

Specification이나 Expected JSON을
코드에 맞추기 위해 임의로 변경하지 마.

문제를 다음 중 하나로 먼저 구분해줘.

- Parser
- Event Classification
- Incident Analysis
- Impact Mapping
- Timeline / Facts
- AI
- Report
- Web
- Interface

그 후 최소 범위만 수정해줘.

새 기능은 추가하지 마.
```

---

# 33. 개발 중 금지사항

```text
새로운 기능 추가

전체 구조 재설계

대규모 Refactoring

Golden Sample 하드코딩

업무정보 하드코딩

장비정보 하드코딩

Expected를 코드에 맞춰 임의 변경

AI가 Core 값을 변경

AI Summary로 전체 보고서 생성

실제 서비스 장애 확정

조치와 복구의 직접적 인과관계 확정
```

---

# 34. Demo 최종 흐름

최종 Demo는 2층 Golden Sample을 중심으로 한다.

```text
loop_2f.log
↓
여러 장비 Event 분석
↓
2층 네트워크 장애
↓
112시스템 / 온나라 / 폴넷 영향 가능
↓
VERY_HIGH
↓
P1
↓
RECOVERED
↓
Timeline / Facts
↓
L2 Loop 가능성
↓
근거 / 불확실성 / 추가확인
↓
관리자 장애 상황보고
```

그 후 1층과 3층 결과를 간단히 보여준다.

```text
1층
→ KICS / P2

3층
→ TCS / P2
```

이를 통해 2층 전용 하드코딩이 아님을 설명한다.

---

# 35. 최종 목표

본 PoC의 목표는 단순 Log Parser 또는 단순 GPT 호출이 아니다.

```text
기술 로그
↓
장애 사건 재구성
↓
업무 영향 판단
↓
복구 우선순위
↓
Fact 기반 AI 추정
↓
관리자 의사결정 지원
```

을 하나의 흐름으로 보여주는 것이다.

---

# 36. 최종 원칙

1인 D-Day에서는 기존 A/B 설계를 모두 완성하는 것을 목표로 하지 않는다.

개발 우선순위:

```text
Core 안정성
>
Report / Web
>
Mock AI
>
Actual Azure AI
>
부가기능
```

일부 기능이 제외되더라도 핵심 시나리오가 End-to-End로 동작하면 PoC 완료로 판단한다.

D-Day에는 새로운 설계를 추가하지 않고,
본 문서를 기준으로 개발한다.