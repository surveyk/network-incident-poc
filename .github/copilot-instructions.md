# Network Incident PoC — GitHub Copilot Instructions

## 1. Project Goal

본 프로젝트는 여러 네트워크 장비에서 발생한 이벤트를 하나의 Incident로 재구성하고 다음 정보를 제공하는 1일 PoC이다.

- 장애 위치
- 영향 가능 업무
- 업무 중요도
- 복구 우선순위
- 장애 관련 시간
- 현재 네트워크 상태
- 반복 장애 여부
- 핵심 Timeline
- 로그 기반 Fact 및 근거
- AI 기반 원인 후보 및 추가 확인사항

최종 목적은 장애원인을 자동 확정하는 것이 아니라 담당자의 장애 판단과 보고를 지원하는 것이다.

현재 D-Day 개발은 기존 2인 병렬개발 계획에서 **1인 개발 방식**으로 변경되었다.

기존 `JOB_261007_A.md`, `JOB_261007_B.md`는 상세 설계 참고자료로 유지하며, 실제 D-Day 실행순서와 우선순위는 다음 문서를 따른다.

```text
JOB_261007_SOLO.md
```

---

# 2. Mandatory Specifications

코드를 작성하거나 수정하기 전에 반드시 다음 문서를 확인한다.

1. `docs/data-spec.md`
2. `docs/interface-spec.md`
3. `docs/flowchart.md`
4. `docs/report-spec.md`
5. `docs/ai-spec.md`
6. `docs/report-builder-spec.md`
7. `docs/web-spec.md`

각 문서의 역할:

- `data-spec.md`
  - 데이터 구조
  - 업무 Mapping
  - 중요도
  - 복구 우선순위
  - 이벤트 판단기준

- `interface-spec.md`
  - Core Result 데이터 계약

- `flowchart.md`
  - 전체 처리흐름과 기술적 역할구분

- `report-spec.md`
  - 최종 관리자 보고서 기준

- `ai-spec.md`
  - AI 분석 범위와 금지사항

- `report-builder-spec.md`
  - Core Result와 AI Result 조합기준

- `web-spec.md`
  - 관리자 Web 화면 기준

세부값은 위 문서를 기준으로 한다.

동일 내용을 코드나 본 지침에 중복 정의하지 않는다.

---

# 3. D-Day Development Mode

현재 PoC는 1인이 하나의 Branch에서 개발한다.

실제 D-Day 작업 Branch:

```text
feature/solo-poc
```

`main`에서 직접 개발하지 않는다.

기존 Branch:

```text
feature/core-analysis
feature/web-ai-report
```

는 기존 2인 개발계획의 참고용이며 실제 D-Day에서는 사용하지 않는다.

개발 우선순위:

```text
Core Analysis
↓
2층 Golden Sample
↓
1층 / 3층 Validation
↓
Report / Web
↓
Mock AI
↓
Azure OpenAI
↓
전체 Test / Demo
```

시간이 부족한 경우 다음 우선순위를 유지한다.

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

---

# 4. Core Analysis Scope

Core Analysis는 다음 기능을 담당한다.

```text
여러 장비 원본 로그
→ Parsing
→ Normalization
→ Event Classification
→ 관련 이벤트 선별
→ 장비 간 이벤트 상관관계 확인
→ Incident Timeline 생성
→ 장애 위치 식별
→ 영향 가능 업무 Mapping
→ 업무 중요도
→ 복구 우선순위
→ 장애시간 판단
→ 현재 상태 판단
→ 반복 여부
→ Fact 및 Evidence
→ Core Result
```

Core는 다음 기능을 수행하지 않는다.

- AI 장애원인 확정
- Web UI 판단로직
- 자연어 원인 확정
- Database
- 실시간 NMS 연동
- 자동복구
- Topology 자동탐색

---

# 5. AI / Report / Web Scope

Core Result 이후에는 다음 흐름으로 처리한다.

```text
Core Result
→ AI Analysis
→ 원인 후보
→ 추정 근거
→ 부족하거나 반대되는 근거
→ 추가 확인사항
→ Report Builder
→ Web UI
→ 관리자 보고서
```

AI는 다음 값을 임의로 변경하지 않는다.

- 장애 위치
- 영향 가능 업무
- 업무 중요도
- 복구 우선순위
- 장애시간
- 현재 상태
- Core가 생성한 Fact
- Recurrence

---

# 6. Rule and AI Separation

다음 항목은 Rule 및 기준정보 기반으로 처리한다.

- 장애 위치
- 영향 가능 업무
- 업무 중요도
- 복구 우선순위
- 장애시간
- 현재 네트워크 상태
- 반복 여부
- Timeline
- Fact

다음 항목은 AI 영역이다.

- 장애 원인 후보
- 추정 근거 설명
- 부족한 근거
- 추가 확인사항
- 자연어 보고 지원

AI가 Rule 결과를 변경하지 않는다.

기술적 역할 경계:

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

---

# 7. Impact Interpretation

`affected_services`는 실제 서비스 장애가 확인되었다는 뜻이 아니다.

다음 의미로 사용한다.

> 장애 위치와 사전 정의 업무정보를 이용하여 식별한 영향 가능 업무

PoC 기본값:

```text
impact_basis = LOCATION_MAPPING
verification_status = UNVERIFIED
```

실제 업무서비스 장애를 네트워크 로그만으로 확정하지 않는다.

---

# 8. Multi-device Analysis

가능한 경우 단일 장비 이벤트만으로 Incident를 판단하지 않는다.

기본 분석 대상:

```text
장애 발생 장비
+
직접 연결된 상위 또는 인접 장비
+
조치 및 복구 이벤트
```

예:

```text
2층 층간스위치
+
백본스위치
```

관련 없는 다른 층 장비 이벤트는 Parsing할 수 있으나 최종 Incident Timeline과 Fact에서 제외한다.

상위 또는 인접 장비 로그가 없다는 이유만으로 분석을 실패시키지 않는다.

다만 근거가 부족한 장애원인을 확정하지 않는다.

---

# 9. Incident Time

시간 정의는 `data-spec.md`와 `interface-spec.md`를 따른다.

기본 필드:

```text
detected_time
start_time
recovery_time
end_time
```

의미를 임의로 변경하지 않는다.

단순 Link 장애에서는:

```text
detected_time = start_time
```

이 가능하다.

별도 정상화 이벤트가 없는 경우:

```text
end_time = recovery_time
```

이 가능하다.

---

# 10. Fact and Evidence

Fact는 원본 로그에서 직접 확인 가능한 내용만 사용한다.

가능한 경우 다음 정보를 포함한다.

```text
type
timestamp
device
source_line
text
```

원인추정은 Fact에 넣지 않는다.

금지 예:

```text
Loop가 최종 장애원인이다.
케이블 연결 오류 때문이다.
112시스템이 실제로 중단되었다.
```

---

# 11. Source Line Rule

`source_line`은 원본 로그 파일의 실제 행 번호이다.

Sample 로그 파일은 테스트 정합성을 위해 빈 줄 없이 유지한다.

로그파일 편집 시 행 번호가 달라지면 Expected JSON도 반드시 함께 검토한다.

---

# 12. Core Result Interface

Core Result의 최상위 구조는 `interface-spec.md`를 따른다.

기본 구조:

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

필드명과 의미를 임의로 변경하지 않는다.

`interface-spec.md`의 JSON은 데이터 구조 계약을 의미한다.

실제 실행 시에는 해당 구조를 만족하는 Python `dict` 또는 Pydantic Object를 사용할 수 있으며 중간 JSON 파일 저장은 필수가 아니다.

Interface 변경이 필요한 경우:

1. `interface-spec.md` 수정
2. `data-spec.md` 정합성 확인
3. Expected JSON 수정
4. 구현 수정
5. 테스트 재실행

순서를 따른다.

---

# 13. Sample Strategy

다음 3개 Sample을 지원한다.

## 1층 Validation

```text
data/sample_logs/link_1f.log
```

검증:

```text
1층
→ KICS(킥스) + 온나라 + 폴넷
→ HIGH
→ P2
→ RECOVERED
```

## 2층 Golden Sample

```text
data/sample_logs/loop_2f.log
```

검증:

```text
2층
→ 112시스템 + 온나라 + 폴넷
→ VERY_HIGH
→ P1
→ RECOVERED
```

복합 이벤트와 다중장비 상관분석까지 검증한다.

## 3층 Validation

```text
data/sample_logs/link_3f.log
```

검증:

```text
3층
→ TCS + 온나라 + 폴넷
→ HIGH
→ P2
→ RECOVERED
```

---

# 14. Hardcoding Prohibition

다음 형태의 구현을 금지한다.

```python
if "loop_2f" in filename:
    location = "2층"
```

또는:

```python
if floor == 2:
    services = ["112시스템", "온나라", "폴넷"]
```

서비스 Mapping과 중요도는 반드시 `data/services.json`을 사용한다.

장비 위치는 `data/devices.json`을 사용한다.

1·2·3층 Sample이 모두 통과해야 한다.

---

# 15. Coding Principles

다음 원칙을 따른다.

- 구현 전에 관련 문서를 먼저 읽는다.
- 현재 repository 구조를 확인한다.
- 최소 구현을 우선한다.
- 1일 PoC 범위를 넘지 않는다.
- 불필요한 abstraction을 만들지 않는다.
- 새로운 핵심 기능에는 테스트를 작성한다.
- 기존 테스트를 깨뜨리지 않는다.
- API Key를 코드에 넣지 않는다.
- 무관한 파일을 수정하지 않는다.
- 요청하지 않은 대규모 리팩터링을 하지 않는다.
- Golden Sample에만 맞춘 예외처리를 만들지 않는다.
- Specification 또는 Expected를 코드에 맞추기 위해 임의로 변경하지 않는다.

---

# 16. Testing

pytest를 사용한다.

최소 Core 검증:

```text
□ 정상 로그 Parsing
□ UNKNOWN 처리
□ MAC_FLAPPING
□ LOOP_DETECTED
□ BROADCAST_HIGH
□ CPU_HIGH
□ LINK_DOWN
□ LINK_UP
□ PORT_DISABLED

□ 무관 장비 이벤트 제외
□ 관련 장비 이벤트 결합

□ 1층 위치 및 업무 Mapping
□ 2층 위치 및 업무 Mapping
□ 3층 위치 및 업무 Mapping

□ HIGH / P2
□ VERY_HIGH / P1

□ detected_time
□ start_time
□ recovery_time
□ end_time

□ RECOVERED

□ Fact timestamp
□ Fact device
□ Fact source_line

□ recurrence UNKNOWN

□ analysis_context

□ 최종 Core Result
```

Expected JSON:

```text
data/expected/link_1f_expected.json
data/expected/loop_2f_expected.json
data/expected/link_3f_expected.json
```

작업 완료 전 반드시 실행한다.

```bash
pytest -q
```

테스트 실패 상태를 완료로 간주하지 않는다.

AI / Report / Web 단계에서는 최소 다음을 추가 확인한다.

```text
□ Report / Web 정상 표시
□ Mock AI 결과 표시
□ AI가 Core 값을 변경하지 않음
□ AI Failure 시 Core Report 유지
□ Mock End-to-End 동작
```

---

# 17. Git Rules

`main`에서 직접 개발하지 않는다.

D-Day 작업 Branch:

```text
feature/solo-poc
```

작은 단위로 Commit한다.

예:

```text
feat: add network incident core
test: validate golden samples

feat: add incident report web
test: add web tests

feat: add mock ai analysis

feat: add azure openai integration
```

공유 Interface와 Specification을 임의로 변경하지 않는다.

---

# 18. One-Day PoC Constraint

다음은 우선 구현하지 않는다.

- Database
- 실시간 Streaming
- 실제 NMS 연결
- SNMP 실시간 Polling
- Topology 자동분석
- Multi-vendor 완전지원
- 자동 장애복구
- 반복 장애 학습
- 장애 예측
- Production 배포
- 과도한 UI Framework
- Dashboard 고도화
- 그래프
- 파일 Upload
- RAG
- Vector DB
- Agent
- 복잡한 Retry
- 대규모 Refactoring

현재 설계된 3개 Sample과 End-to-End Demo가 안정적으로 동작하는 것을 우선한다.

---

# 19. Copilot Working Procedure

작업 요청을 받으면 다음 순서를 따른다.

1. 관련 Specification 확인
2. Repository 구조 확인
3. 현재 코드 확인
4. 변경 대상 파일 확인
5. 최소 구현
6. 테스트 작성 또는 수정
7. 테스트 실행
8. Expected 결과 비교
9. 결과와 남은 위험 보고

설계와 구현이 충돌하면 임의로 Specification을 변경하지 않는다.

충돌내용을 먼저 보고한다.

한 번에 전체 시스템을 구현하지 않는다.

```text
Feature
↓
Test
↓
PASS
↓
다음 기능
```

방식으로 진행한다.

---

# 20. D-Day Stop Rules

시간이 부족한 경우 다음 기준을 따른다.

## Core가 지연될 경우

새 기능 개발을 중단하고 2층 Golden Sample을 우선 완료한다.

## Web이 지연될 경우

Azure OpenAI 개발을 보류하고 관리자 Report/Web 완성을 우선한다.

## Azure 연결이 지연될 경우

Mock AI를 사용하여 End-to-End Demo를 유지한다.

Azure 연결 실패로 전체 PoC를 실패시키지 않는다.

---

# 21. Definition of Done

1인 D-Day PoC는 다음 우선순위로 완료를 판단한다.

## 필수 완료

```text
□ 여러 장비 로그 Parsing
□ 관련 이벤트 선별
□ 다중장비 Incident 재구성

□ 1층 Validation PASS
□ 2층 Golden Sample PASS
□ 3층 Validation PASS

□ 위치 자동식별
□ 영향 가능 업무 Mapping
□ 중요도 판단
□ 복구 우선순위 판단

□ Incident 시간 생성
□ Timeline 생성
□ 상태 판단

□ Fact + Evidence 생성
□ recurrence 생성
□ analysis_context 생성

□ interface-spec 준수
□ Expected JSON 일치
□ pytest PASS

□ 관리자 Report / Web 동작
```

## 목표 완료

```text
□ Mock AI 동작
□ AI 분석 결과 Report 표시
□ Mock End-to-End PASS
```

## 시간 허용 시

```text
□ Azure OpenAI 실제 연결
□ Azure Smoke Test PASS
```

D-Day는 기존 Developer A/B 각각의 모든 기능을 완료하는 것을 목표로 하지 않는다.

핵심 시나리오가 End-to-End로 동작하면 PoC 완료로 판단한다.