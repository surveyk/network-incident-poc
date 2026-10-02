Developer A의 Network Incident PoC Core Analysis를 구현한다.

바로 코딩하지 말고 먼저 repository와 Specification을 확인한다.

반드시 다음 문서를 순서대로 읽는다.

1. `.github/copilot-instructions.md`
2. `docs/data-spec.md`
3. `docs/interface-spec.md`
4. `docs/flowchart.md`
5. `docs/report-spec.md`

다음 데이터도 확인한다.

```text
data/devices.json
data/services.json

data/sample_logs/link_1f.log
data/sample_logs/loop_2f.log
data/sample_logs/link_3f.log

data/expected/link_1f_expected.json
data/expected/loop_2f_expected.json
data/expected/link_3f_expected.json
```

---

# 목표

여러 네트워크 장비의 원본 로그를 하나의 Incident로 재구성하고 `docs/interface-spec.md`에 정의된 A/B JSON을 생성한다.

Azure OpenAI 또는 다른 LLM을 사용하지 않는다.

---

# 먼저 보고할 내용

코드를 작성하기 전에 다음을 보고한다.

1. 현재 repository 구조
2. A 개발에 필요한 파일
3. 제안하는 `src/` 구조
4. 제안하는 `tests/` 구조
5. 모듈 간 데이터 흐름
6. 현재 Specification 사이의 충돌 또는 모호점
7. 1일 PoC에서 과도하다고 판단되는 구조

가능한 단순한 구조를 제안한다.

---

# A 구현 범위

```text
여러 장비 로그
→ Parsing
→ Normalization
→ Event Classification
→ 관련 이벤트 선별
→ 장비 간 상관관계 확인
→ Incident Timeline
→ 장애 위치
→ 영향 가능 업무
→ 업무 중요도
→ 복구 우선순위
→ 장애시간
→ 현재 상태
→ 반복 여부
→ Facts + Evidence
→ analysis_context
→ A/B JSON
```

---

# 구현하지 않을 기능

다음을 구현하지 않는다.

```text
Azure OpenAI
AI 원인추정
Web UI
HTML
최종 자연어 보고서
Database
실시간 NMS
SNMP Polling
Topology 자동탐색
자동 장애복구
```

---

# 핵심 원칙

## 1. 다중장비 분석

가능한 경우 장애 장비와 직접 연결된 상위 또는 인접 장비의 이벤트를 함께 사용한다.

예:

```text
SW-ACCESS-02
+
BACKBONE-SW
```

단일 장비 이벤트 하나만으로 장애원인을 확정하지 않는다.

---

## 2. 영향 가능 업무

`affected_services`는 실제 서비스 중단이 아니다.

장애 위치와 기준정보를 기반으로 생성한 영향 가능 업무다.

PoC에서는:

```text
impact_basis = LOCATION_MAPPING
verification_status = UNVERIFIED
```

를 사용한다.

---

## 3. Fact

Fact에는 로그로 직접 확인 가능한 정보만 넣는다.

가능하면 다음 값을 포함한다.

```text
type
timestamp
device
source_line
text
```

장애원인 추정을 Fact에 넣지 않는다.

---

## 4. 시간

다음 필드의 의미를 Specification과 동일하게 유지한다.

```text
detected_time
start_time
recovery_time
end_time
```

단순 Link 장애에서는:

```text
detected_time = start_time
```

일 수 있다.

별도 정상화 이벤트가 없는 경우:

```text
end_time = recovery_time
```

일 수 있다.

---

# Sample 검증

## 1층

```text
link_1f.log

기대:
1층 네트워크
KICS(킥스)
온나라
폴넷
HIGH
P2
RECOVERED
```

## 2층

```text
loop_2f.log

기대:
2층 네트워크
112시스템
온나라
폴넷
VERY_HIGH
P1
RECOVERED
```

2층 Sample에서는:

```text
MAC Flapping
Loop 관련 이벤트
Broadcast 증가
Link Down
Port Disable
Link Up
정상화
```

의 흐름을 재구성해야 한다.

## 3층

```text
link_3f.log

기대:
3층 네트워크
TCS
온나라
폴넷
HIGH
P2
RECOVERED
```

---

# Hardcoding 금지

Sample 파일명이나 특정 층을 기준으로 최종 결과를 하드코딩하지 않는다.

장비 위치:

```text
data/devices.json
```

업무 및 중요도:

```text
data/services.json
```

을 사용한다.

---

# 테스트

pytest 테스트를 작성한다.

최소 테스트:

```text
Parser
Normalizer
Classifier
관련 이벤트 선별
다중장비 상관분석
Timeline
Location
Impact
Priority
Incident Time
Status
Facts
Evidence
Recurrence
Analysis Context
Final Interface JSON
```

3개 Sample 모두 검증한다.

```text
link_1f.log
loop_2f.log
link_3f.log
```

Expected 결과:

```text
link_1f_expected.json
loop_2f_expected.json
link_3f_expected.json
```

---

# 최종 검증

작업 완료 전:

```bash
pytest -q
```

를 실행한다.

그 다음 3개 Sample 각각에 대해 Core를 실행하고 Expected JSON과 비교한다.

결과를 다음 형식으로 보고한다.

```text
1층 Validation
PASS / FAIL

2층 Golden Sample
PASS / FAIL

3층 Validation
PASS / FAIL

Interface Contract
PASS / FAIL

pytest
PASS / FAIL
```

FAIL이 있다면 완료라고 보고하지 않는다.

---

# Git

다음 Branch에서 작업한다.

```text
feature/core-analysis
```

`main`에 직접 Commit하지 않는다.

작은 단위 Commit을 사용한다.

---

# Definition of Done

다음을 모두 만족하면 Developer A를 완료한다.

```text
□ 여러 장비 로그 Parsing
□ 관련 이벤트 선별
□ 무관 장비 이벤트 제외
□ 다중장비 Incident 재구성

□ 1층 Validation PASS
□ 2층 Golden Sample PASS
□ 3층 Validation PASS

□ 장애 위치 식별
□ 영향 가능 업무 Mapping
□ 중요도 판단
□ 복구 우선순위 판단

□ detected_time
□ start_time
□ recovery_time
□ end_time

□ Timeline
□ Status

□ Facts
□ Evidence
□ Recurrence
□ Analysis Context

□ A/B JSON 생성
□ Expected JSON 일치
□ pytest PASS
```

A Core가 완료되면 작업을 종료한다.

Developer B 영역을 구현하지 않는다.