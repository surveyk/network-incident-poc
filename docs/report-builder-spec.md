# Network Incident PoC — Report Builder Specification

## 1. 목적

본 문서는 Developer B의 Report Builder가 Developer A의 Core 결과와 AI 분석 결과를 결합하여 관리자용 네트워크 장애 상황보고서를 생성하는 기준을 정의한다.

Report Builder는 새로운 장애 판단을 수행하지 않는다.

역할은 다음과 같다.

```text
A Core Result
+
AI Analysis Result
↓
데이터 조합
↓
중복 제거
↓
관리자용 표현 변환
↓
장애 상황보고서
```

---

# 2. 기본 원칙

Report Builder는 다음 원칙을 따른다.

1. A의 Rule 기반 결과를 우선한다.
2. AI 결과는 추정원인과 추가확인 영역에만 사용한다.
3. Fact와 AI Inference를 분리한다.
4. 동일 정보를 여러 영역에서 반복하지 않는다.
5. 관리자 본문에는 핵심정보만 표시한다.
6. 상세 기술정보는 별도 영역으로 분리한다.
7. AI가 실패하더라도 보고서 기본구조는 유지한다.
8. 실제 서비스 장애가 확인되지 않은 경우 확정적으로 표현하지 않는다.

---

# 3. Report Builder 입력

Report Builder는 두 가지 입력을 사용한다.

## A Core Result

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

## AI Result

```json
{
  "ai_status": "SUCCESS",
  "summary": "",
  "hypotheses": [],
  "additional_checks": []
}
```

---

# 4. 최종 보고서 구조

관리자용 기본 보고서는 다음 4개 영역으로 구성한다.

```text
1. 장애 요약
2. 장애경과
3. 조치내용
4. 추정원인 및 추가확인
```

기술 상세정보는 별도 상세영역으로 제공한다.

---

# 5. 장애 요약

장애 요약은 보고서 첫 화면에서 가장 먼저 확인할 정보이다.

기본 항목:

| 보고서 항목 | 데이터 출처 |
|---|---|
| 발생일시 | `incident.start_time` ~ `incident.recovery_time` |
| 최초징후 | `incident.detected_time` |
| 장애구간 | `incident.location` |
| 영향업무 | `impact.affected_services` |
| 업무 중요도 | `impact.overall_criticality` |
| 복구 우선순위 | `impact.recovery_priority` |
| 현재상태 | `incident.status` |
| 반복 장애 여부 | `recurrence.status` |

---

# 6. 발생일시 표현

기본 표시:

```text
2026.9.30. 10:21:24 ~ 10:22:13
```

의미:

```text
start_time
→ 실제 장애 발생

recovery_time
→ 네트워크 연결 복구
```

최초 이상징후는 필요한 경우 별도 항목으로 표시한다.

예:

```text
최초 이상징후: 10:21:02
```

`end_time`은 관리자 본문에서 반드시 표시하지 않아도 된다.

기술 상세정보에서 최종 정상화시각으로 사용할 수 있다.

---

# 7. 장애구간

A의 `incident.location`을 그대로 사용한다.

예:

```text
2층 네트워크
```

AI가 장애위치를 수정하거나 새로 생성하지 않는다.

---

# 8. 영향업무

`impact.affected_services`를 사용한다.

표시 예:

```text
112시스템, 온나라, 폴넷
```

단, 보고서 의미는 다음과 같다.

> 장애 위치를 기준으로 식별한 영향 가능 업무

실제 서비스 장애가 확인되지 않은 경우:

```text
영향 가능 업무
```

또는 문맥상:

```text
업무영향(확인 필요)
```

로 표현할 수 있다.

다음과 같이 확정적으로 표현하지 않는다.

```text
112시스템 장애
온나라 장애
폴넷 장애
```

---

# 9. 업무 중요도

내부값:

```text
VERY_HIGH
HIGH
NORMAL
```

관리자 화면 표시:

```text
VERY_HIGH → 매우 높음
HIGH      → 높음
NORMAL    → 보통
```

Report Builder가 별도 판단하지 않는다.

---

# 10. 복구 우선순위

내부값:

```text
P1
P2
P3
```

화면 표시:

```text
P1 → 최우선
P2 → 신속 복구
P3 → 일반 복구
```

필요하면 다음처럼 함께 표시할 수 있다.

```text
P1 / 최우선
```

---

# 11. 현재상태

A의 `incident.status`를 사용한다.

화면 표시:

| 내부값 | 화면 표시 |
|---|---|
| ACTIVE | 장애 지속 |
| RECOVERING | 복구 중 |
| RECOVERED | 복구 완료 |
| UNKNOWN | 확인 필요 |

AI가 상태를 변경하지 않는다.

---

# 12. 반복 장애 여부

`recurrence.status`를 사용한다.

표시:

```text
REPEATED     → 반복 장애
NOT_REPEATED → 반복 없음
UNKNOWN      → 확인 필요
```

1일 PoC에서는 기본적으로 `UNKNOWN`이 정상이다.

---

# 13. 장애경과

장애경과는 A의 `timeline`을 사용한다.

원칙:

```text
이상징후
→ 장애
→ 조치
→ 복구
```

관리자 본문에는 4~6개 핵심 이벤트만 표시한다.

예:

```text
10:21:02  MAC 주소 반복 이동 감지
10:21:22  2층 방향 Broadcast 증가
10:21:24  2층 네트워크 연결 중단
10:22:05  장애 의심 포트 차단
10:22:13  2층 네트워크 연결 복구
```

전체 원본 로그를 장애경과에 표시하지 않는다.

---

# 14. 조치내용 생성

조치내용은 `timeline`에서 `stage = ACTION`인 이벤트를 우선 사용한다.

필요하면 이후 RECOVERY 또는 NORMALIZED 이벤트와 결합하여 결과를 설명한다.

예:

```text
- 장애 의심 포트 차단
- 조치 이후 2층 네트워크 연결 복구
- Broadcast 및 장비 상태 정상화 확인
```

조치내용에는 이미 수행된 조치만 포함한다.

다음은 포함하지 않는다.

```text
포트 연결상태 확인 필요
서비스 상태 확인 필요
과거 장애이력 확인 필요
```

이는 `추가확인` 영역에 넣는다.

---

# 15. 추정원인

AI 결과의 `hypotheses`를 사용한다.

관리자 보고서에는 기본적으로 가장 우선적인 원인 후보 1개를 표시한다.

예:

```text
현재 로그 흐름에서는 2층 내부 L2 Loop 가능성을 우선 검토할 수 있음.
```

원인 후보가 여러 개 존재하더라도 관리자 본문에는 지나치게 많이 표시하지 않는다.

상세보기에서는 1~3개 후보를 모두 보여줄 수 있다.

---

# 16. 추정근거

관리자 본문에서는 핵심 근거 2~4개만 사용한다.

예:

```text
- MAC 주소 반복 이동
- Broadcast 증가
- Loop 관련 이벤트
- 의심 포트 차단 이후 정상화
```

근거는 AI가 새로 만든 사실이 아니라 A의 Fact 또는 Timeline에 연결되어 있어야 한다.

---

# 17. 불확실성

AI의 `uncertainty`는 원인 후보를 최종 확정할 수 없는 이유를 표시한다.

예:

```text
실제 물리적 연결상태와 전체 VLAN 구성이 확인되지 않아 최종 원인 확정은 추가 점검 필요
```

관리자 본문에는 1~2개 핵심 제한사항만 간단하게 표현한다.

---

# 18. 추가확인

AI의 `additional_checks`를 사용한다.

예:

```text
- 의심 포트의 실제 연결상태 확인
- VLAN 구성 확인
- 112시스템 실제 서비스 정상 여부 확인
- 동일 구간 과거 유사 장애이력 확인
```

이미 수행된 조치는 추가확인에 다시 포함하지 않는다.

---

# 19. AI Summary 사용원칙

AI의 `summary`를 보고서 전체 본문으로 그대로 사용하지 않는다.

`summary`는 다음 용도로 제한한다.

```text
- 추정원인 영역 보조 문장
- 화면 상단 AI 분석 요약
- 기술 상세정보 요약
```

보고서의 핵심 값은 A 데이터를 기반으로 Report Builder가 직접 구성한다.

---

# 20. AI 정상상태 보고서

`ai_status = SUCCESS`인 경우:

```text
장애 요약
→ A 데이터

장애경과
→ A Timeline

조치내용
→ A ACTION / RECOVERY

추정원인
→ AI hypotheses

추정근거
→ AI evidence + A Fact

추가확인
→ AI additional_checks
```

---

# 21. AI 실패상태 보고서

`ai_status = UNAVAILABLE` 또는 `ERROR`인 경우에도 다음 영역은 정상적으로 생성한다.

```text
1. 장애 요약
2. 장애경과
3. 조치내용
```

추정원인 영역은 다음처럼 처리한다.

```text
AI 분석을 사용할 수 없어 추정원인 자동분석은 제공되지 않습니다.
로그 기반 장애정보와 조치내용은 정상적으로 확인할 수 있습니다.
```

추가확인 목록은 빈 값으로 처리할 수 있다.

---

# 22. AI Failure 예시

```text
[장애 요약]
정상 표시

[장애경과]
정상 표시

[조치내용]
정상 표시

[추정원인 및 추가확인]
AI 분석 사용 불가
```

AI Failure 때문에 전체 페이지를 오류화하지 않는다.

---

# 23. Report View Model

Web과 Report Builder 사이에는 최종 화면용 View Model을 사용할 수 있다.

권장 예:

```json
{
  "summary": {
    "incident_time": "2026.9.30. 10:21:24 ~ 10:22:13",
    "detected_time": "10:21:02",
    "location": "2층 네트워크",
    "affected_services": [
      "112시스템",
      "온나라",
      "폴넷"
    ],
    "criticality": "매우 높음",
    "recovery_priority": "P1 / 최우선",
    "status": "복구 완료",
    "recurrence": "확인 필요"
  },

  "timeline": [],

  "actions": [],

  "analysis": {
    "ai_status": "SUCCESS",
    "probable_cause": "L2 Loop 가능성",
    "evidence": [],
    "uncertainty": [],
    "additional_checks": []
  }
}
```

Web Template은 A JSON과 AI JSON을 직접 각각 해석하기보다 이 View Model을 사용하는 것을 권장한다.

---

# 24. View Model 목적

View Model을 사용하는 이유:

```text
A JSON 구조
+
AI JSON 구조
↓
Report Builder
↓
화면에 필요한 단순 구조
```

장점:

- HTML Template 단순화
- A/B 구조변경 영향 최소화
- AI Failure 처리 단순화
- 화면 표시값 변환 일원화

---

# 25. 2층 Golden Sample 최종 보고서 예시

```text
네트워크 장애 상황보고

1. 장애 요약

발생일시
2026.9.30. 10:21:24 ~ 10:22:13

최초 이상징후
10:21:02

장애구간
2층 네트워크

영향 가능 업무
112시스템, 온나라, 폴넷

업무 중요도
매우 높음

복구 우선순위
P1 / 최우선

현재상태
복구 완료

반복 장애 여부
확인 필요


2. 장애경과

10:21:02  MAC 주소 반복 이동 감지
10:21:22  2층 방향 Broadcast 증가
10:21:24  2층 네트워크 연결 중단
10:22:05  장애 의심 포트 차단
10:22:13  2층 네트워크 연결 복구


3. 조치내용

- 장애 의심 포트 차단
- 조치 이후 2층 네트워크 연결 복구
- Broadcast 및 장비 상태 정상화 확인


4. 추정원인 및 추가확인

추정원인
현재 로그 흐름에서는 2층 내부 L2 Loop 가능성을 우선 검토할 수 있음.

주요근거
- MAC 주소 반복 이동
- Loop 관련 이벤트
- Broadcast 증가
- 의심 포트 차단 이후 정상화

확인 한계
실제 물리적 연결상태와 전체 VLAN 구성은 확인되지 않음.

추가확인
- 의심 포트의 실제 연결상태
- VLAN 구성
- 112시스템 등 실제 서비스 정상 여부
- 동일 구간 과거 유사 장애이력
```

---

# 26. 중복 제거 원칙

다음 정보를 여러 영역에서 반복하지 않는다.

예:

```text
2층 네트워크
P1
112시스템
```

는 기본적으로 장애 요약에서 한 번 명확하게 표시한다.

추정원인 영역에서 다시 반복할 필요가 없다.

Timeline과 조치내용도 동일 문장을 그대로 복사하지 않는다.

---

# 27. 기술 상세정보

관리자 본문과 별도로 기술 상세영역을 제공할 수 있다.

포함 가능:

```text
- 전체 Fact
- Fact timestamp
- Fact device
- source_line
- analysis_context
- 전체 AI hypothesis
- uncertainty 상세
```

기술 상세정보는 기본적으로 접거나 별도 화면영역으로 분리하는 것을 권장한다.

---

# 28. analysis_context 표시

관리자 본문에는 기본적으로 표시하지 않는다.

기술 상세영역 예:

```text
분석 장비
2층 층간스위치, 백본스위치

분석 장비 수
2대

관련 이벤트
17건
```

이는 분석 근거 범위를 확인하는 용도로 사용한다.

---

# 29. Fact Source 표시

기술 상세정보에서는 다음처럼 표시할 수 있다.

```text
10:21:02
2층 층간스위치
MAC 주소 반복 이동
원본 로그: Line 4
```

이를 통해:

```text
AI 추정
↓
근거
↓
Fact
↓
원본 로그
```

추적성을 제공한다.

---

# 30. Report Builder가 하지 않는 일

Report Builder는 다음 기능을 수행하지 않는다.

```text
로그 Parsing
Event Classification
장애 위치 판단
업무 중요도 판단
복구 우선순위 판단
AI 원인추정
실제 서비스 장애판단
```

Report Builder는 이미 생성된 데이터를 조합하고 표현하는 역할만 한다.

---

# 31. 표시값 변환

Report Builder에서 화면 표시값 변환을 담당할 수 있다.

예:

```text
VERY_HIGH → 매우 높음
HIGH      → 높음
NORMAL    → 보통

P1 → 최우선
P2 → 신속 복구
P3 → 일반 복구

RECOVERED → 복구 완료
UNKNOWN   → 확인 필요
```

가능하면 변환 규칙을 한곳에 모은다.

---

# 32. 데이터 누락 처리

일부 값이 없더라도 보고서 전체 생성을 실패시키지 않는다.

예:

```text
detected_time = null
→ 최초 이상징후 항목 미표시 또는 "확인 불가"

additional_checks = []
→ 추가확인 항목 없음

AI unavailable
→ AI 분석 사용 불가
```

단, 다음 핵심값이 없으면 오류로 판단할 수 있다.

```text
incident.location
impact.affected_services
incident.status
```

처리기준은 구현단계에서 단순하게 유지한다.

---

# 33. Report Builder 테스트

최소 다음을 검증한다.

```text
□ 정상 A + 정상 AI

□ 정상 A + AI UNAVAILABLE

□ 장애 요약 값 정확

□ 영향업무를 실제 장애로 표현하지 않음

□ 업무 중요도 표시 변환

□ 복구 우선순위 표시 변환

□ Timeline 생성

□ ACTION 기반 조치내용 생성

□ AI 원인 후보 표시

□ uncertainty 표시

□ additional_checks 표시

□ AI 실패 시 기본 보고서 유지

□ 중복정보 최소화

□ View Model 생성
```

---

# 34. 1층 / 3층 보고서

단순 Link 장애에서는 AI가 원인을 특정하지 못할 수 있다.

이 경우 보고서는 정상이다.

예:

```text
추정원인
현재 로그만으로 구체적인 장애원인을 특정하기 어려움.

추가확인
- 물리 회선상태
- 포트 오류정보
- 장비 상태
- 작업이력
```

원인 후보가 없다고 해서 Report Builder가 임의로 원인을 생성하지 않는다.

---

# 35. Definition of Done

Report Builder는 다음 조건을 만족하면 완료한다.

```text
□ A Core JSON 입력

□ AI Result 입력

□ Summary View Model 생성

□ 장애 요약 생성

□ 장애경과 생성

□ 조치내용 생성

□ 추정원인 생성

□ 근거 표시

□ 불확실성 표시

□ 추가확인 표시

□ AI Failure Fallback

□ 기술 상세정보 구성

□ 2층 Golden Sample 보고서 생성

□ 1층 단순 Link 보고서 생성

□ 3층 단순 Link 보고서 생성

□ Test PASS
```

---

# 36. 최종 원칙

Report Builder는 판단 엔진이 아니다.

역할은 다음과 같다.

```text
A
사실 및 Rule 판단
        ↓

B AI
원인 후보 및 추가확인
        ↓

Report Builder
정보 조합 및 표현
        ↓

관리자
최종 판단
```

최종 보고서는 기술 로그를 그대로 보여주는 문서가 아니라,

> 장애 위치, 영향 가능 업무, 복구 우선순위, 장애경과 및 원인 후보를 관리자가 빠르게 파악할 수 있도록 정리한 판단지원 문서

를 목표로 한다.