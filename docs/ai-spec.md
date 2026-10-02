# Network Incident PoC — AI Analysis Specification

## 1. 목적

본 문서는 Developer B가 구현하는 AI 분석 기능의 입력, 출력, 판단범위 및 제한사항을 정의한다.

AI는 네트워크 장애의 최종 원인을 자동 확정하지 않는다.

Developer A가 생성한 구조화된 Incident 데이터를 기반으로 다음 정보를 제공한다.

- 장애 원인 후보
- 원인 후보의 판단 근거
- 불확실하거나 부족한 근거
- 추가 확인사항
- 관리자용 간결한 설명

최종 장애원인은 담당자가 판단한다.

---

# 2. AI 처리 위치

전체 처리 흐름에서 AI의 위치는 다음과 같다.

```text
원본 로그
↓
Developer A Core
↓
A/B Interface JSON
↓
Developer B
↓
AI Input Builder
↓
Azure OpenAI
↓
Structured AI Result
↓
Report Builder
↓
Web / 관리자 보고서
```

AI는 A의 Core Analysis를 대체하지 않는다.

---

# 3. AI 입력 원칙

AI에는 가능한 한 원본 로그 전체를 직접 전달하지 않는다.

A가 생성한 다음 구조화 데이터를 주요 입력으로 사용한다.

```text
incident
+
impact
+
timeline
+
facts
+
recurrence
+
analysis_context
```

주요 분석 근거는 특히 다음 두 영역이다.

```text
timeline
+
facts
```

AI는 제공되지 않은 로그나 이벤트를 추측하여 생성하지 않는다.

---

# 4. 입력 데이터

## incident

AI가 참고할 수 있는 정보:

- 장애 위치
- 주요 장비
- 관련 장비
- 최초 이상징후 시각
- 실제 장애발생 시각
- 복구 시각
- 최종 정상화 시각
- 현재 네트워크 상태

예:

```json
{
  "location": "2층 네트워크",
  "primary_device": "2층 층간스위치",
  "related_devices": [
    "백본스위치"
  ],
  "detected_time": "2026-09-30T10:21:02",
  "start_time": "2026-09-30T10:21:24",
  "recovery_time": "2026-09-30T10:22:13",
  "end_time": "2026-09-30T10:22:19",
  "status": "RECOVERED"
}
```

---

# 5. impact 사용원칙

AI는 다음 값을 참고할 수 있다.

- 영향 가능 업무
- 업무 중요도
- 복구 우선순위

그러나 값을 다시 결정하거나 변경하지 않는다.

예:

```text
overall_criticality = VERY_HIGH
recovery_priority = P1
```

AI가 다음과 같이 변경해서는 안 된다.

```text
HIGH
P2
```

`affected_services`는 실제 업무서비스 장애가 아니라 **영향 가능 업무**이다.

AI가 이를 실제 장애로 확정하지 않는다.

---

# 6. timeline 사용원칙

Timeline은 장애 사건의 시간적 관계를 해석하기 위해 사용한다.

예:

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

AI는 개별 이벤트뿐 아니라 다음 관계를 고려한다.

- 어떤 이벤트가 먼저 발생했는가
- 장애 직전에 어떤 징후가 있었는가
- 어떤 조치 이후 상태가 달라졌는가
- 장애 장비와 인접 장비에서 동일 시간대에 어떤 이벤트가 있었는가

시간적 선후관계만으로 인과관계를 확정하지 않는다.

---

# 7. facts 사용원칙

`facts`는 AI 원인추정의 가장 중요한 근거이다.

Fact는 A가 원본 로그에서 직접 확인한 정보이다.

AI는 다음을 수행하지 않는다.

```text
Fact 수정
Fact 삭제
존재하지 않는 Fact 추가
Fact의 의미 변경
```

예:

```json
{
  "type": "MAC_FLAPPING",
  "timestamp": "2026-09-30T10:21:02",
  "device": "2층 층간스위치",
  "source_line": 4,
  "text": "MAC 주소 반복 이동이 확인됨"
}
```

AI는 이를 근거로 원인 후보를 추정할 수 있다.

---

# 8. analysis_context 활용

AI는 분석 근거의 범위를 확인할 수 있다.

예:

```json
{
  "log_source_count": 2,
  "devices_analyzed": [
    "2층 층간스위치",
    "백본스위치"
  ],
  "related_event_count": 17
}
```

이를 통해 단일 장비 이벤트인지 여러 장비의 관련 이벤트인지 파악할 수 있다.

다만 `log_source_count`가 많다는 이유만으로 판단 신뢰도를 수치화하지 않는다.

---

# 9. AI 출력 최상위 구조

AI 분석 결과는 구조화된 JSON으로 반환한다.

권장 구조:

```json
{
  "ai_status": "SUCCESS",
  "summary": "",
  "hypotheses": [],
  "additional_checks": []
}
```

---

# 10. ai_status

가능한 값:

```text
SUCCESS
UNAVAILABLE
ERROR
```

의미:

| 값 | 의미 |
|---|---|
| SUCCESS | 정상적으로 AI 분석 완료 |
| UNAVAILABLE | Azure OpenAI 사용 불가 |
| ERROR | 응답 또는 처리 중 오류 발생 |

AI 실패 여부와 A Core 결과는 별개이다.

---

# 11. summary

`summary`는 AI 분석 내용을 관리자 또는 운영자가 이해하기 쉽게 간결하게 설명한다.

권장 길이:

```text
2~4문장
```

예:

```text
2층 네트워크에서 MAC 주소 반복 이동과 Broadcast 증가가 발생한 후 연결이 중단되었습니다.
의심 포트 차단 이후 연결과 주요 이상상태가 정상화되었습니다.
현재 로그 흐름에서는 L2 Loop 가능성을 우선 검토할 수 있습니다.
```

확정적 표현은 사용하지 않는다.

---

# 12. hypotheses

원인 후보 목록이다.

구조:

```json
{
  "cause": "L2 Loop 가능성",
  "evidence": [],
  "uncertainty": []
}
```

전체 구조 예:

```json
{
  "hypotheses": [
    {
      "cause": "L2 Loop 가능성",
      "evidence": [
        "MAC 주소 반복 이동이 확인됨",
        "Broadcast 증가가 확인됨",
        "의심 포트 차단 이후 네트워크가 정상화됨"
      ],
      "uncertainty": [
        "실제 물리적 연결상태는 확인되지 않음"
      ]
    }
  ]
}
```

PoC에서는 원인 후보를 1~3개 수준으로 제한한다.

---

# 13. cause 작성원칙

`cause`는 최종 원인이 아니라 **원인 후보**이다.

권장:

```text
L2 Loop 가능성
물리 회선 또는 포트 이상 가능성
장비 상태 이상 가능성
```

금지:

```text
장애 원인은 L2 Loop이다.
케이블 오류가 원인이다.
담당자의 설정 실수가 원인이다.
```

---

# 14. evidence

원인 후보를 뒷받침하는 근거이다.

`evidence`는 반드시 A의 다음 데이터에 근거해야 한다.

```text
facts
또는
timeline
```

예:

```text
MAC 주소 반복 이동
Broadcast 증가
Loop 관련 이벤트
의심 포트 차단 이후 복구
```

AI가 새로운 기술적 사건을 만들어서 근거로 사용할 수 없다.

---

# 15. uncertainty

원인 후보를 최종 확정할 수 없는 이유를 표시한다.

예:

```text
실제 케이블 연결상태 미확인
해당 포트의 물리 구성 미확인
동일 VLAN 전체 구성정보 미확인
서비스 상태정보 미확인
```

원인 후보에는 가능하면 최소 한 개 이상의 불확실성 또는 확인 제한사항을 제공한다.

---

# 16. additional_checks

담당자가 다음 단계에서 확인해야 할 사항이다.

예:

```json
{
  "additional_checks": [
    "의심 포트의 실제 연결상태 확인",
    "동일 VLAN의 스위치 연결구성 확인",
    "112시스템 실제 서비스 정상 여부 확인",
    "동일 구간의 과거 유사 장애이력 확인"
  ]
}
```

이미 수행된 조치는 추가확인 항목으로 반복하지 않는다.

---

# 17. 2층 Golden Sample 기대 방향

2층 Golden Sample에서 AI는 최소 다음 정도를 도출할 수 있어야 한다.

```text
원인 후보
L2 Loop 가능성

근거
- MAC Flapping
- Loop 관련 이벤트
- Broadcast 증가
- 포트 차단 이후 정상화

불확실성
- 실제 물리 연결상태 미확인

추가확인
- 의심 포트 연결상태
- VLAN 구성
- 실제 112시스템 정상 여부
- 유사 장애이력
```

AI가 다음과 같이 표현해서는 안 된다.

```text
L2 Loop가 장애 원인으로 확정되었습니다.
```

---

# 18. 1층 / 3층 단순 Link Sample

1층과 3층 Sample은 원인 판단 근거가 제한적이다.

예:

```text
양단에서 Link Down 및 이후 Link Up은 확인되지만
현재 로그만으로 장애 원인을 특정하기에는 근거가 부족합니다.
```

가능한 추가확인:

```text
물리 회선 상태
포트 오류 Counter
장비 상태
작업 이력
인접 장비 이벤트
```

AI가 단순 Link Down만으로 다음을 추정하지 않는다.

```text
케이블 불량
장비 고장
관리자 실수
```

---

# 19. AI가 판단하지 않는 항목

AI는 다음 정보를 변경하거나 새로 판단하지 않는다.

```text
장애 위치
주요 장비
관련 장비

detected_time
start_time
recovery_time
end_time

영향 가능 업무
업무 중요도
복구 우선순위

현재 상태
반복 장애 여부

A Fact
```

해당 값은 A 결과를 그대로 사용한다.

---

# 20. 실제 서비스 장애 표현

A의:

```text
affected_services
```

는 영향 가능 업무이다.

AI는 다음 표현을 사용하지 않는다.

```text
112시스템 장애 발생
KICS 서비스 중단
TCS 시스템 장애
```

실제 서비스 상태 확인정보가 없는 경우 다음과 같이 표현한다.

```text
112시스템 영향 가능
실제 서비스 상태 확인 필요
```

---

# 21. 책임 또는 과실 추정 금지

네트워크 로그만으로 개인 또는 조직의 책임을 추정하지 않는다.

금지:

```text
운영자 실수
담당자 과실
잘못된 작업으로 발생
```

Configuration Change 로그가 있더라도 직접적인 인과관계가 확인되지 않는 한 책임 추정에 사용하지 않는다.

---

# 22. AI Prompt 기본원칙

Azure OpenAI에 전달하는 System 또는 Developer Prompt에는 최소 다음 지침을 포함한다.

```text
1. 제공된 incident, impact, timeline, facts, analysis_context만을 주요 근거로 사용한다.

2. 제공되지 않은 로그 또는 이벤트를 생성하지 않는다.

3. A가 계산한 장애 위치, 업무 중요도, 복구 우선순위를 변경하지 않는다.

4. affected_services를 실제 서비스 중단으로 확정하지 않는다.

5. Fact와 원인추정을 명확하게 구분한다.

6. 원인 후보에는 evidence와 uncertainty를 제공한다.

7. 근거가 부족하면 판단이 어렵다고 명시한다.

8. 최종 장애원인을 확정하지 않는다.

9. 개인 또는 조직의 책임을 추정하지 않는다.

10. 지정된 JSON 구조로 응답한다.
```

---

# 23. AI 입력 데이터 최소화

Azure OpenAI에는 필요한 정보만 전달한다.

우선순위:

```text
incident
timeline
facts
analysis_context
impact
```

전체 원본 로그를 기본 Prompt에 넣지 않는다.

이유:

- 불필요한 Token 사용 감소
- 무관 로그로 인한 분석 혼선 감소
- A가 선별한 Fact 중심 분석
- 근거 추적 용이

---

# 24. Raw Log 추가 사용

PoC 기본구조에서는 Raw Log를 AI에 전달하지 않는다.

향후 상세분석이 필요하면 특정 `source_line`에 해당하는 로그만 선택적으로 추가할 수 있다.

예:

```text
AI
↓
Fact #4 확인
↓
source_line 11
↓
필요 시 원본 로그 상세조회
```

1일 PoC에서는 구현하지 않아도 된다.

---

# 25. AI Failure

Azure OpenAI 호출 실패 시 전체 프로그램이 실패해서는 안 된다.

Fallback:

```json
{
  "ai_status": "UNAVAILABLE",
  "summary": null,
  "hypotheses": [],
  "additional_checks": []
}
```

A Core 결과는 그대로 유지한다.

---

# 26. 잘못된 AI 응답

다음 상황을 고려한다.

```text
JSON Parsing 실패
필수 필드 누락
잘못된 데이터 Type
빈 응답
API 오류
Timeout
```

이 경우 B는 AI 결과를 실패 처리한다.

A 결과는 변경하지 않는다.

---

# 27. AI 결과 검증

AI Response를 바로 Web 또는 Report Builder에 전달하지 않는다.

최소 검증:

```text
ai_status 존재

summary
→ string 또는 null

hypotheses
→ list

additional_checks
→ list
```

각 hypothesis:

```text
cause
evidence
uncertainty
```

구조를 확인한다.

---

# 28. AI 결과의 결정성

생성형 AI 결과는 완전히 동일한 문장을 항상 반환하지 않을 수 있다.

따라서 B 테스트에서는 전체 문장 Exact Match보다 다음을 검증하는 것이 좋다.

```text
JSON Schema 정상

원인 후보 존재

근거 존재

불확실성 존재

추가확인 존재

금지사항 미포함
```

Golden Sample 전체 AI 문장을 Expected로 고정하지 않는다.

---

# 29. AI Mock

B는 실제 Azure OpenAI 호출 전 Mock AI Result로 개발할 수 있다.

예:

```json
{
  "ai_status": "SUCCESS",

  "summary": "2층 네트워크 장애는 L2 Loop 가능성을 우선 검토할 수 있습니다.",

  "hypotheses": [
    {
      "cause": "L2 Loop 가능성",
      "evidence": [
        "MAC 주소 반복 이동",
        "Broadcast 증가",
        "포트 차단 이후 복구"
      ],
      "uncertainty": [
        "실제 물리 연결상태 미확인"
      ]
    }
  ],

  "additional_checks": [
    "의심 포트 연결상태 확인",
    "VLAN 구성 확인",
    "실제 서비스 상태 확인"
  ]
}
```

이를 이용하여 Report Builder와 Web을 AI 개발과 병렬로 진행할 수 있다.

---

# 30. Azure OpenAI 환경변수

인증정보는 코드에 저장하지 않는다.

예:

```text
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT
```

`.env` 등 로컬 환경파일은 Git에 Commit하지 않는다.

---

# 31. 1일 PoC 제한

다음 기능은 구현하지 않는다.

```text
RAG
Vector DB
Fine-tuning
Agent Framework
Multi-Agent
AI 자동조치
AI 반복학습
원인 확률 계산
Knowledge Graph
```

단일 Azure OpenAI 호출 기반의 구조화 분석으로 구현한다.

---

# 32. B AI 테스트

최소 테스트:

```text
□ Mock A JSON 입력

□ 2층 Golden Sample
   - 원인 후보 존재
   - L2 Loop 가능성 표현 가능
   - evidence 존재
   - uncertainty 존재
   - additional_checks 존재

□ 1층 Link 장애
   - 원인 확정하지 않음

□ 3층 Link 장애
   - 원인 확정하지 않음

□ 업무 중요도 미변경

□ 복구 우선순위 미변경

□ 실제 서비스 장애 미확정

□ 존재하지 않는 Fact 추가 방지

□ AI Response Validation

□ Azure OpenAI 실패 Fallback
```

---

# 33. B AI Definition of Done

AI 영역은 다음 조건을 만족하면 완료한다.

```text
□ A/B Interface JSON 입력 가능

□ AI Input 생성

□ Azure OpenAI 호출

□ 구조화 JSON 응답

□ ai_status

□ summary

□ hypotheses
   □ cause
   □ evidence
   □ uncertainty

□ additional_checks

□ AI 결과 Validation

□ Fact와 Inference 분리

□ Rule 기반 결과 미변경

□ 실제 서비스 장애 미확정

□ AI Failure Fallback

□ 2층 Golden Sample 처리

□ 1층/3층 과도한 추정 방지
```

---

# 34. 최종 원칙

AI는 다음 질문에 답한다.

```text
현재 확인된 사실을 기준으로
어떤 원인을 우선 검토할 수 있는가?

그 근거는 무엇인가?

무엇이 아직 확인되지 않았는가?

담당자가 추가로 확인해야 할 것은 무엇인가?
```

AI는 다음 질문을 최종 확정하지 않는다.

```text
최종 장애원인은 무엇인가?

실제 업무서비스가 중단되었는가?

누구의 책임인가?
```

AI는 담당자의 장애 판단을 지원하는 도구이다.