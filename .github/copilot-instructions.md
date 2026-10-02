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

---

# 2. Mandatory Specifications

코드를 작성하거나 수정하기 전에 반드시 다음 문서를 확인한다.

1. `docs/data-spec.md`
2. `docs/interface-spec.md`
3. `docs/flowchart.md`
4. `docs/report-spec.md`

각 문서의 역할:

- `data-spec.md`
  - 데이터 구조
  - 업무 Mapping
  - 중요도
  - 복구 우선순위
  - 이벤트 판단기준

- `interface-spec.md`
  - A/B JSON 계약

- `flowchart.md`
  - 전체 처리흐름 및 A/B 역할구분

- `report-spec.md`
  - 최종 관리자 보고서 기준

세부값은 위 문서를 기준으로 한다.

동일 내용을 코드나 본 지침에 중복 정의하지 않는다.

---

# 3. Developer A Scope

Developer A는 다음 Core Analysis를 담당한다.

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
→ A/B JSON
```

A는 다음 기능을 구현하지 않는다.

- Azure OpenAI
- AI 장애원인 추정
- Web UI
- 최종 자연어 보고서
- Database
- 실시간 NMS 연동
- 자동복구
- Topology 자동탐색

---

# 4. Developer B Scope

Developer B는 A의 JSON을 입력으로 사용한다.

B의 역할:

```text
A Core JSON
→ Azure OpenAI
→ 원인 후보
→ 추정 근거
→ 부족하거나 반대되는 근거
→ 추가 확인사항
→ Web UI
→ 관리자 보고서
```

B는 다음 값을 임의로 변경하지 않는다.

- 장애 위치
- 영향 가능 업무
- 업무 중요도
- 복구 우선순위
- A가 생성한 Fact

---

# 5. Rule and AI Separation

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

---

# 6. Impact Interpretation

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

# 7. Multi-device Analysis

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

# 8. Incident Time

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

# 9. Fact and Evidence

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

# 10. Source Line Rule

`source_line`은 원본 로그 파일의 실제 행 번호이다.

Sample 로그 파일은 테스트 정합성을 위해 빈 줄 없이 유지한다.

로그파일 편집 시 행 번호가 달라지면 Expected JSON도 반드시 함께 검토한다.

---

# 11. A/B Interface

A의 최상위 JSON 구조는 `interface-spec.md`를 따른다.

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

Interface 변경이 필요한 경우:

1. `interface-spec.md` 수정
2. `data-spec.md` 정합성 확인
3. Expected JSON 수정
4. A/B 구현 수정
5. 테스트 재실행

순서를 따른다.

---

# 12. Sample Strategy

A는 다음 3개 Sample을 지원해야 한다.

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

---

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

---

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

# 13. Hardcoding Prohibition

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

# 14. Coding Principles

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

---

# 15. Testing

pytest를 사용한다.

최소 검증:

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

□ 최종 A/B JSON
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

---

# 16. Git Rules

`main`에서 직접 개발하지 않는다.

Developer A:

```text
feature/core-analysis
```

Developer B:

```text
feature/web-ai-report
```

작은 단위로 Commit한다.

예:

```text
feat: add multi-device log parser
test: add parser tests

feat: add incident correlation
test: add incident tests

feat: add business impact mapping
test: validate floor mappings

feat: add core result builder
test: validate golden samples
```

A/B 공유 Interface를 임의로 변경하지 않는다.

---

# 17. One-Day PoC Constraint

다음은 구현하지 않는다.

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

현재 설계된 3개 Sample이 안정적으로 동작하는 것을 우선한다.

---

# 18. Copilot Working Procedure

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

---

# 19. Definition of Done

Developer A는 다음 조건을 만족하면 완료한다.

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
```

A가 완료되면 B 영역으로 확장하지 않고 작업을 종료한다.