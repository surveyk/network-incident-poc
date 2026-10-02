# Network Incident PoC — Developer B Test Specification

## 1. 목적

본 문서는 Developer B 영역의 테스트 기준을 정의한다.

B는 생성형 AI를 사용하므로 모든 테스트를 동일한 방식으로 수행하지 않는다.

테스트는 크게 다음 두 영역으로 분리한다.

```text
1. Deterministic Test
   → Mock 데이터 기반

2. AI Behaviour Test
   → 실제 Azure OpenAI 기반
```

목표는 다음과 같다.

```text
AI 문장이 매번 동일한가?
```

를 검증하는 것이 아니라,

```text
정해진 구조를 지키는가?
A 결과를 변경하지 않는가?
근거 없이 확정하지 않는가?
AI 실패 시 전체 시스템이 유지되는가?
```

를 검증하는 것이다.

---

# 2. B 테스트 범위

B 테스트 대상은 다음과 같다.

```text
AI Input Builder
AI Adapter
AI Response Validation
Fallback
Report Builder
View Model
Web Rendering
A/B Integration
```

---

# 3. 테스트 레벨

권장 테스트 구조는 다음과 같다.

```text
Level 1
Unit Test

Level 2
Mock Integration Test

Level 3
Azure Behaviour Test

Level 4
A/B End-to-End Test
```

---

# 4. Level 1 — Unit Test

외부 Azure 호출 없이 개별 기능을 테스트한다.

주요 대상:

```text
AI Input Builder
Response Validator
Report Builder
View Model
Fallback
표시값 변환
```

빠르고 반복 가능해야 한다.

---

# 5. AI Input Builder Test

입력:

```text
data/mock/core_2f.json
```

검증:

```text
□ incident 포함
□ impact 포함
□ timeline 포함
□ facts 포함
□ analysis_context 포함
```

기본적으로 Raw Log 전체는 포함하지 않는다.

추가 확인:

```text
□ recovery_priority 유지
□ overall_criticality 유지
□ affected_services 유지
```

AI Input Builder가 A의 데이터를 수정해서는 안 된다.

---

# 6. AI Input 최소화 Test

AI Input에 불필요한 정보가 포함되지 않는지 확인한다.

기본적으로 다음은 제외한다.

```text
전체 Raw Log
불필요한 UNKNOWN Event
무관 장비 Event
```

목적:

```text
Token 절감
+
분석 혼선 감소
```

---

# 7. AI Response Schema Test

Mock AI 결과:

```text
data/mock/ai_2f.json
```

를 이용한다.

필수 최상위 필드:

```text
ai_status
summary
hypotheses
additional_checks
```

각 hypothesis:

```text
cause
evidence
uncertainty
```

검증:

```text
□ Type 정상
□ 필수 필드 존재
□ 빈 구조 처리 가능
```

---

# 8. AI SUCCESS Test

입력:

```text
core_2f.json
+
ai_2f.json
```

기대:

```text
ai_status = SUCCESS
summary 존재
hypotheses 1개 이상
evidence 존재
uncertainty 존재
additional_checks 존재
```

---

# 9. AI UNAVAILABLE Test

입력:

```text
data/mock/ai_unavailable.json
```

기대:

```text
ai_status = UNAVAILABLE
summary = null
hypotheses = []
additional_checks = []
```

그리고 Report Builder가 정상 동작해야 한다.

---

# 10. AI ERROR Test

다음과 같은 잘못된 Mock Response를 테스트에서 생성한다.

예:

```json
{
  "summary": 123,
  "hypotheses": "invalid"
}
```

기대:

```text
Response Validation FAIL
↓
ai_status = ERROR
↓
Fallback
```

Application 전체가 예외로 종료되면 안 된다.

---

# 11. Missing Field Test

다음 상황을 테스트한다.

```text
summary 누락
hypotheses 누락
additional_checks 누락
cause 누락
```

구현 정책에 따라:

```text
Schema Error
→ ERROR
```

로 처리한다.

---

# 12. Report Builder Deterministic Test

입력:

```text
core_2f.json
+
ai_2f.json
```

출력 View Model은 deterministic하게 검증한다.

핵심 기대값:

```text
location = 2층 네트워크

affected_services
= 112시스템, 온나라, 폴넷

criticality
= 매우 높음

priority
= P1 / 최우선

status
= 복구 완료

recurrence
= 확인 필요
```

---

# 13. Timeline Test

기대 Timeline:

```text
MAC 주소 반복 이동
Broadcast 증가
Link Down
의심 포트 차단
Link Up
```

원본 로그 전체가 Timeline에 들어가지 않아야 한다.

---

# 14. Action Test

`stage = ACTION`인 Event를 기반으로 조치내용이 생성되는지 확인한다.

2층 Sample:

```text
장애 의심 포트 차단
```

추가확인 항목이 조치내용에 들어가면 안 된다.

---

# 15. AI Analysis Rendering Test

정상 AI Mock 사용 시 다음이 View Model에 반영되어야 한다.

```text
probable cause
evidence
uncertainty
additional_checks
```

---

# 16. AI Failure Report Test

입력:

```text
core_2f.json
+
ai_unavailable.json
```

기대:

```text
장애 요약 표시
장애경과 표시
조치내용 표시

AI 영역
→ AI 분석 사용 불가
```

다음 정보는 사라지면 안 된다.

```text
2층 네트워크
112시스템
VERY_HIGH
P1
RECOVERED
```

---

# 17. Core Preservation Test

B가 A 결과를 변경하지 않는지 검증한다.

입력 A:

```text
overall_criticality = VERY_HIGH
recovery_priority = P1
location = 2층 네트워크
```

B 최종 결과에서도 동일해야 한다.

금지:

```text
AI 결과에 따라
VERY_HIGH → HIGH

P1 → P2
```

---

# 18. Impact Wording Test

실제 서비스 상태가 확인되지 않은 경우 다음 표현을 사용해야 한다.

```text
영향 가능 업무
```

또는 이에 준하는 표현.

금지 표현 검증:

```text
112시스템 장애 발생
112시스템 서비스 중단
```

---

# 19. Fact / Inference Separation Test

A Fact:

```text
MAC 주소 반복 이동
```

AI Inference:

```text
L2 Loop 가능성
```

두 데이터가 서로 다른 영역에서 유지되는지 확인한다.

AI 추정을 Fact 배열에 추가하면 안 된다.

---

# 20. Technical Detail Test

기술 상세정보에서 다음을 확인한다.

```text
Fact timestamp
Fact device
source_line
analysis_context
```

2층 Sample 기준:

```text
분석 장비 수 = 2
분석 장비
- 2층 층간스위치
- 백본스위치
```

---

# 21. Web Rendering Test

FastAPI TestClient 등을 이용하여 기본 Route를 테스트할 수 있다.

검증:

```text
HTTP 200

네트워크 장애 상황보고 표시

2층 네트워크 표시

112시스템 표시

P1 / 최우선 표시

복구 완료 표시
```

---

# 22. AI UNAVAILABLE Web Test

Mock AI Failure 상태로 Web을 호출한다.

검증:

```text
HTTP 200

장애정보 정상 표시

AI 분석 사용 불가 표시
```

AI 장애 때문에 HTTP 500이 발생하면 안 된다.

---

# 23. Core Error Web Test

Core 입력 자체가 잘못된 경우는 AI Failure와 구분한다.

예:

```text
incident 누락
impact 누락
```

이 경우:

```text
분석 실패
```

등 적절한 오류처리를 한다.

AI Failure 화면과 동일하게 처리하지 않는다.

---

# 24. 1층 Validation Test

A 결과 또는 Expected JSON을 입력으로 사용한다.

기대:

```text
1층 네트워크

KICS(킥스)
온나라
폴넷

HIGH
P2

RECOVERED
```

AI Mock이 없다면 다음과 같은 최소 AI 결과를 사용할 수 있다.

```text
현재 로그만으로 구체적인 장애원인 특정 어려움
```

---

# 25. 3층 Validation Test

기대:

```text
3층 네트워크

TCS
온나라
폴넷

HIGH
P2

RECOVERED
```

AI가 원인을 과도하게 확정하지 않아야 한다.

---

# 26. Mock Integration Test

B의 주요 deterministic Integration Test:

```text
Mock Core
+
Mock AI
↓
Report Builder
↓
View Model
↓
Web
```

이 테스트는 외부 Azure 연결 없이 반드시 PASS해야 한다.

---

# 27. Mock Test의 중요성

D-Day에서 다음 상황에서도 개발 가능해야 한다.

```text
인터넷 불안정
Azure 접근 불가
API Key 오류
Quota 문제
```

따라서 Mock Integration Test는 B의 가장 중요한 테스트 중 하나이다.

---

# 28. 실제 Azure Behaviour Test

실제 Azure 테스트에서는 전체 응답문장을 Exact Match하지 않는다.

검증 항목:

```text
□ 응답 성공

□ Schema 정상

□ summary 존재

□ hypotheses list

□ cause 존재

□ evidence 존재

□ uncertainty 존재

□ additional_checks 존재
```

---

# 29. 실제 Azure 금지행위 Test

다음 행위가 있는지 검사한다.

```text
업무 중요도 변경
복구 우선순위 변경
실제 서비스 장애 확정
개인 또는 조직 책임 추정
최종 장애원인 확정
```

완전한 자연어 검증은 어렵기 때문에 주요 금지표현 또는 패턴을 확인한다.

예:

```text
"원인은 확실히"
"장애 원인은"
"112시스템이 중단"
"담당자 실수"
```

이런 표현이 발생하면 Review 대상으로 처리한다.

---

# 30. AI Evidence Test

AI의 evidence는 A Facts 또는 Timeline에 근거해야 한다.

2층 Sample에서 허용 가능한 근거 예:

```text
MAC Flapping
Loop Guard
Broadcast 증가
포트 차단
Link 복구
```

존재하지 않는 이벤트:

```text
전원 장애
광케이블 단선
장비 재부팅
```

등이 근거로 나오면 실패 또는 Review 대상으로 처리한다.

---

# 31. 단순 Link 장애 AI Behaviour

1층/3층에서는 다음이 정상적인 AI 행동이다.

```text
현재 로그만으로 구체적 원인 특정 어려움
```

다음은 부적절하다.

```text
케이블 불량이 원인입니다.
```

AI가 근거 부족을 인정하는지 검증한다.

---

# 32. Azure Failure Test

실제 API 오류를 매번 발생시킬 필요는 없다.

AI Adapter를 Mock하여 다음 예외를 테스트한다.

```text
Timeout
Authentication Error
Connection Error
Invalid Response
```

기대:

```text
Fallback 실행
A Core 유지
Web 정상
```

---

# 33. Timeout Test

AI 호출이 Timeout일 때:

```text
전체 Request 종료
```

가 아니라:

```text
AI Failure
↓
Fallback
↓
보고서 출력
```

이 되어야 한다.

---

# 34. Mock / Azure Mode Test

환경변수:

```text
AI_MODE=mock
```

일 때 Mock AI 결과 사용.

```text
AI_MODE=azure
```

일 때 Azure 호출.

두 Mode가 동일한 Report Builder Interface를 사용해야 한다.

---

# 35. Report View Model Test

권장 View Model:

```text
summary
timeline
actions
analysis
technical_detail
```

각 영역을 독립적으로 검증한다.

HTML Template을 직접 데이터 조합 장소로 사용하지 않는다.

---

# 36. Regression Test

B 기능을 추가한 뒤 다음이 깨지지 않는지 확인한다.

```text
A JSON Contract
Mock Mode
AI Failure Fallback
2층 Report
1층 Validation
3층 Validation
```

---

# 37. 테스트 파일 권장 구조

```text
tests/
├── test_ai.py
├── test_ai_validation.py
├── test_report.py
├── test_app.py
└── test_b_integration.py
```

1일 PoC에서는 필요하면 다음처럼 줄여도 된다.

```text
tests/
├── test_ai.py
├── test_report.py
└── test_app.py
```

---

# 38. 테스트에서 실제 Azure 호출 최소화

일반 pytest 실행에서 Azure를 호출하지 않는 것을 권장한다.

기본:

```text
pytest
→ Mock 기반
```

실제 Azure Test는 별도로 실행한다.

예:

```text
pytest -m azure
```

또는 별도 Smoke Test로 수행한다.

---

# 39. 이유

실제 AI 호출을 일반 Unit Test에 포함하면 다음 문제가 있다.

```text
Network Dependency
비용
속도
응답 변동
Quota
Azure 장애
```

따라서 기본 Test Suite와 분리한다.

---

# 40. D-Day 기본 테스트 명령

기본:

```bash
pytest -q
```

결과는 Azure 연결 여부와 관계없이 PASS해야 한다.

실제 Azure 연결 확인은 별도 Smoke Test로 수행한다.

---

# 41. Azure Smoke Test

최소 확인:

```text
Azure Client 생성

↓
Golden Sample 전송

↓
Response Schema 정상

↓
AI Status SUCCESS
```

전체 문장내용을 Exact Match하지 않는다.

---

# 42. 최종 테스트 결과 형식

B 완료 시 다음 형식으로 결과를 정리한다.

```text
AI Input Builder         PASS / FAIL
AI Response Validation   PASS / FAIL
Mock AI                  PASS / FAIL
AI Fallback              PASS / FAIL

Report Builder           PASS / FAIL
View Model               PASS / FAIL

Web Rendering            PASS / FAIL
AI Failure Web           PASS / FAIL

1F Validation            PASS / FAIL
2F Golden Sample         PASS / FAIL
3F Validation            PASS / FAIL

Mock Integration         PASS / FAIL
A/B Integration          PASS / FAIL

pytest                    PASS / FAIL
Azure Smoke Test         PASS / FAIL
```

Azure Smoke Test가 실패하더라도 Mock Mode Demo는 가능해야 한다.

---

# 43. B 완료 필수항목

B 완료를 위해 반드시 PASS해야 한다.

```text
Mock Integration
Report Builder
Web Rendering
AI Failure Fallback
1F / 2F / 3F Rendering
A/B Contract
pytest
```

---

# 44. Azure 연결과 B 완료

Azure 연결은 중요한 기능이지만 PoC 전체 안정성을 위해 다음을 구분한다.

```text
Application 동작
≠
Azure 가용성
```

Azure 장애 시에도:

```text
A Core
+
Fallback
+
Web
```

이 정상적으로 동작해야 한다.

---

# 45. Definition of Done

Developer B Test는 다음을 만족하면 완료한다.

```text
□ Unit Test

□ Mock AI Test

□ Response Schema Test

□ Report Builder Test

□ View Model Test

□ Web Test

□ AI UNAVAILABLE Test

□ AI ERROR Test

□ 1층 Validation

□ 2층 Golden Sample

□ 3층 Validation

□ Rule 결과 보존

□ Impact 표현 검증

□ Fact / Inference 분리

□ Mock Integration

□ A/B Integration

□ pytest PASS

□ Azure Smoke Test 수행
```

---

# 46. 최종 원칙

B의 테스트 목표는 AI가 항상 같은 문장을 말하는지를 확인하는 것이 아니다.

검증 대상은 다음이다.

```text
구조는 안정적인가?

A의 사실을 보존하는가?

근거 없는 확정을 하지 않는가?

AI가 실패해도 서비스가 유지되는가?

관리자 보고서가 일관되게 생성되는가?
```

생성형 AI의 변동성은 허용하되 시스템의 구조와 안전장치는 deterministic하게 검증한다.