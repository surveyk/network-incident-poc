# Network Incident PoC — A/B Interface Specification

## 1. 목적

본 문서는 Developer A(Core Analysis)와 Developer B(AI / Web / Report) 사이의 데이터 인터페이스를 정의한다.

A는 여러 네트워크 장비의 로그를 분석하여 장애 사건을 구조화하고, B는 A의 결과를 이용하여 AI 기반 원인추정 및 관리자용 보고서를 생성한다.

A와 B는 본 문서의 JSON 구조를 공통 계약으로 사용한다.

임의로 필드명이나 의미를 변경하지 않는다.

---

# 2. 역할 구분

## Developer A

A는 Rule 및 사전 정의 데이터에 기반하여 다음 정보를 생성한다.

- 장애 위치
- 관련 장비
- 장애 관련 시간
- 영향 가능 업무
- 업무 중요도
- 복구 우선순위
- 현재 네트워크 상태
- 반복 장애 여부
- Incident Timeline
- 로그 기반 Fact
- Fact 근거정보
- 분석에 사용된 장비 및 이벤트 정보

A는 최종 장애원인을 확정하지 않는다.

---

## Developer B

B는 A가 생성한 구조화 데이터를 이용하여 다음 기능을 수행한다.

- AI 기반 장애 원인 후보 추정
- 추정 근거 정리
- 부족하거나 반대되는 근거 정리
- 추가 확인사항 생성
- Web 화면 구성
- 관리자용 장애 상황보고서 생성

B는 다음 값을 임의로 변경하지 않는다.

- 장애 위치
- 영향 가능 업무
- 업무 중요도
- 복구 우선순위
- A가 생성한 Fact

---

# 3. 최상위 JSON 구조

A의 최종 출력은 다음 구조를 기본으로 한다.

```json id="mfz84u"
{
  "incident": {},
  "impact": {},
  "timeline": [],
  "facts": [],
  "recurrence": {},
  "analysis_context": {}
}
```

각 영역의 의미는 다음과 같다.

| 영역 | 의미 |
|---|---|
| incident | 장애 위치, 장비, 시각, 현재상태 |
| impact | 영향 가능 업무, 중요도, 복구우선순위 |
| timeline | 관리자용 핵심 장애경과 |
| facts | 로그에서 직접 확인된 사실 |
| recurrence | 반복장애 여부 |
| analysis_context | 분석에 사용된 장비 및 이벤트 범위 |

---

# 4. incident

`incident`는 하나의 네트워크 장애 사건에 대한 기본정보를 제공한다.

## 구조

```json id="cb8hq0"
{
  "incident_id": "INC-20260930-001",

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

# 5. 장애 시간 정의

각 시간 필드는 다음 의미를 가진다.

| 필드 | 의미 |
|---|---|
| detected_time | Incident와 관련된 최초 이상징후 |
| start_time | 실제 네트워크 장애 발생 |
| recovery_time | 네트워크 연결 복구 |
| end_time | 관련 이상상태 최종 정상화 |

## Golden Sample

```text id="ocg2tc"
10:21:02
MAC Flapping
→ detected_time

10:21:24
2층 Link Down
→ start_time

10:22:13
2층 Link Up
→ recovery_time

10:22:19
CPU 등 관련 상태 정상화
→ end_time
```

단순 Link 장애와 같이 최초 이벤트가 바로 장애 발생인 경우:

```text id="4h0z68"
detected_time = start_time
```

으로 처리할 수 있다.

정확한 시간을 확인할 수 없는 경우 임의로 생성하지 않는다.

필요한 경우 `null`을 허용한다.

---

# 6. 장애 장비 정의

## primary_device

Incident가 직접 발생한 주요 장비를 의미한다.

예:

```text id="4nptcj"
2층 층간스위치
```

## related_devices

같은 Incident를 판단하기 위해 사용한 상위 또는 인접 장비를 의미한다.

예:

```json id="bv6kjh"
[
  "백본스위치"
]
```

`related_devices`에 포함된 장비가 장애원인이라는 의미는 아니다.

동일 시간대 관련 이벤트의 상관분석에 사용되었다는 의미이다.

---

# 7. impact

`impact`는 장애 위치를 업무 기준정보와 Mapping하여 생성한다.

## 구조

```json id="sc4d9c"
{
  "affected_services": [
    {
      "category": "112",
      "name": "112시스템",
      "criticality": "VERY_HIGH"
    },
    {
      "category": "행정",
      "name": "온나라",
      "criticality": "NORMAL"
    },
    {
      "category": "행정",
      "name": "폴넷",
      "criticality": "NORMAL"
    }
  ],

  "impact_basis": "LOCATION_MAPPING",

  "verification_status": "UNVERIFIED",

  "overall_criticality": "VERY_HIGH",

  "recovery_priority": "P1"
}
```

---

# 8. affected_services 의미

`affected_services`는 실제 서비스 장애가 확인되었다는 의미가 아니다.

다음 의미로 사용한다.

> 장애 위치와 사전에 정의된 업무정보에 따라 산출된 **영향 가능 업무**

예:

```text id="inybmg"
2층 네트워크 장애
↓
112시스템
온나라
폴넷
```

는 다음을 의미한다.

> 해당 업무가 장애 영향을 받을 가능성이 있으므로 우선 확인할 필요가 있다.

다음 의미는 아니다.

```text id="2jpi3h"
112시스템 실제 서비스 장애 확정
온나라 실제 서비스 장애 확정
폴넷 실제 서비스 장애 확정
```

실제 서비스 장애 여부는 별도의 서비스 상태정보 또는 사용자 확인이 필요하다.

---

# 9. impact_basis

PoC에서는 기본적으로 다음 값을 사용한다.

```text id="kcdecc"
LOCATION_MAPPING
```

의미:

> 장애 위치와 사전에 정의된 업무 Mapping을 이용하여 영향 가능 업무를 산출함.

향후 다른 근거가 추가될 경우 확장할 수 있으나 1일 PoC에서는 `LOCATION_MAPPING`만 사용한다.

---

# 10. verification_status

서비스 영향 확인상태를 나타낸다.

PoC 기본값:

```text id="ws1qz1"
UNVERIFIED
```

의미:

> 실제 업무서비스 장애 여부는 확인되지 않음.

향후 실제 서비스 모니터링이나 운영자 확인기능을 연결할 경우 다음과 같이 확장할 수 있다.

```text id="9ja2yj"
UNVERIFIED
CONFIRMED
NOT_AFFECTED
```

1일 PoC에서는 `UNVERIFIED`만 사용한다.

---

# 11. 업무 중요도

`overall_criticality`는 영향 가능 업무 중 가장 높은 중요도를 사용한다.

가능한 값:

```text id="njjd9e"
VERY_HIGH
HIGH
NORMAL
```

예:

```text id="d6yyf5"
112시스템 = VERY_HIGH
온나라 = NORMAL
폴넷 = NORMAL

→ overall_criticality = VERY_HIGH
```

AI가 값을 변경하지 않는다.

---

# 12. 복구 우선순위

`recovery_priority`는 `overall_criticality`에 따라 결정한다.

```text id="pbuo4c"
VERY_HIGH → P1
HIGH      → P2
NORMAL    → P3
```

업무 중요도와 복구 우선순위는 `data/services.json`에 정의된 기준을 사용한다.

---

# 13. timeline

`timeline`은 관리자에게 보여줄 핵심 장애경과이다.

전체 원본 로그를 그대로 포함하지 않는다.

## 구조

```json id="chbe1y"
[
  {
    "timestamp": "2026-09-30T10:21:02",
    "stage": "PRECURSOR",
    "device": "2층 층간스위치",
    "event_type": "MAC_FLAPPING",
    "summary": "MAC 주소 반복 이동 감지"
  },
  {
    "timestamp": "2026-09-30T10:21:22",
    "stage": "PRECURSOR",
    "device": "백본스위치",
    "event_type": "BROADCAST_HIGH",
    "summary": "2층 방향 Broadcast 트래픽 증가"
  },
  {
    "timestamp": "2026-09-30T10:21:24",
    "stage": "INCIDENT",
    "device": "백본스위치",
    "event_type": "LINK_DOWN",
    "summary": "2층 네트워크 연결 중단"
  },
  {
    "timestamp": "2026-09-30T10:22:05",
    "stage": "ACTION",
    "device": "2층 층간스위치",
    "event_type": "PORT_DISABLED",
    "summary": "장애 의심 포트 차단"
  },
  {
    "timestamp": "2026-09-30T10:22:13",
    "stage": "RECOVERY",
    "device": "백본스위치",
    "event_type": "LINK_UP",
    "summary": "2층 네트워크 연결 복구"
  }
]
```

관리자용 Timeline은 기본적으로 4~6개 핵심 이벤트를 사용한다.

---

# 14. Timeline stage

사용 가능한 값은 다음과 같다.

| stage | 의미 |
|---|---|
| PRECURSOR | 장애 전 이상징후 |
| INCIDENT | 실제 장애 발생 |
| ACTION | 운영자 또는 시스템 조치 |
| RECOVERY | 연결 또는 기능 복구 |
| NORMALIZED | 관련 상태 최종 정상화 |

`NORMALIZED` 이벤트가 존재하더라도 관리자 보고서 Timeline에서 반드시 표시할 필요는 없다.

---

# 15. facts

`facts`는 원본 로그에서 직접 확인할 수 있는 사실만 포함한다.

## 구조

```json id="cqx18g"
[
  {
    "type": "MAC_FLAPPING",
    "timestamp": "2026-09-30T10:21:02",
    "device": "2층 층간스위치",
    "source_line": 4,
    "text": "MAC 주소 반복 이동이 확인됨"
  },
  {
    "type": "BROADCAST_HIGH",
    "timestamp": "2026-09-30T10:21:22",
    "device": "백본스위치",
    "source_line": 12,
    "text": "2층 방향 Broadcast 증가가 확인됨"
  }
]
```

---

# 16. Fact 근거 추적

Fact는 가능한 경우 다음 정보를 포함한다.

- type
- timestamp
- device
- source_line
- text

`source_line`은 원본 로그 파일의 줄 번호이다.

이를 통해 다음 관계를 유지한다.

```text id="p9rzj9"
AI 추정
↓
Fact
↓
발생 시각 / 장비
↓
원본 로그
```

AI 분석결과의 신뢰성을 높이고 운영자가 근거를 다시 확인할 수 있도록 하기 위한 것이다.

---

# 17. Fact에 포함하지 않는 정보

다음은 Fact에 포함하지 않는다.

```text id="d02guo"
Loop가 최종 장애원인이다.
잘못된 케이블 연결 때문에 장애가 발생했다.
112시스템이 실제로 중단되었다.
```

이 정보는 원본 네트워크 로그만으로 확정할 수 없다.

원인 후보는 B의 AI 분석에서 처리하며, 실제 서비스 장애 여부는 별도 확인이 필요하다.

---

# 18. recurrence

반복 장애 여부를 나타낸다.

## 구조

```json id="bl52ij"
{
  "status": "UNKNOWN",
  "similar_incident_count": null
}
```

가능한 값:

```text id="5kj4gk"
REPEATED
NOT_REPEATED
UNKNOWN
```

1일 PoC에서는 장애이력 Database를 구현하지 않으므로 기본적으로:

```text id="35qeay"
UNKNOWN
```

을 반환한다.

과거 이력이 없다는 이유만으로 `NOT_REPEATED`를 반환하지 않는다.

---

# 19. analysis_context

`analysis_context`는 A가 Incident 판단에 사용한 분석 범위를 나타낸다.

## 구조

```json id="j9zw3p"
{
  "log_source_count": 2,

  "devices_analyzed": [
    "2층 층간스위치",
    "백본스위치"
  ],

  "related_event_count": 17
}
```

---

# 20. analysis_context 의미

## log_source_count

Incident 분석에 실제 사용된 장비 수이다.

예:

```text id="91g03z"
2층 층간스위치
+
백본스위치

→ 2
```

## devices_analyzed

Incident 판단에 사용된 관련 장비 목록이다.

무관 장비는 포함하지 않는다.

## related_event_count

전체 입력 로그 수가 아니라 Incident 분석에 사용된 관련 이벤트 수이다.

---

# 21. 다중장비 분석 원칙

A는 가능한 경우 단일 장비 로그 하나만으로 Incident를 판단하지 않는다.

기본 분석 구조:

```text id="kb9kjg"
장애 발생 장비
+
상위 또는 인접 장비
+
조치 및 복구 이벤트
```

예:

```text id="vxgpm0"
2층 층간스위치
MAC Flapping

+

백본스위치
2층 방향 Broadcast 증가

+

2층/백본
Link Down

+

2층 장비
포트 차단

+

백본/2층
Link Up
```

를 하나의 Incident로 재구성한다.

상위 또는 인접 장비 로그가 없을 경우에도 분석을 중단하지 않는다.

다만 근거 수준이 낮아질 수 있음을 고려하며, A는 부족한 근거를 이용해 장애원인을 확정하지 않는다.

---

# 22. 무관 로그 처리

입력 로그에는 Incident와 무관한 이벤트가 포함될 수 있다.

예:

```text id="wgj1di"
1층 정상 Interface 이벤트
3층 Configuration 이벤트
4층 Link Up 이벤트
```

전체 로그는 Parsing할 수 있으나 최종 Incident Timeline, Fact 및 `analysis_context`에는 관련 이벤트만 사용한다.

무관 이벤트가 같은 파일에 존재한다는 이유만으로 Incident에 포함하지 않는다.

---

# 23. A 최종 출력 예시

2층 Golden Sample에 대한 A의 최종 출력 예시는 다음과 같다.

```json id="0o5zmb"
{
  "incident": {
    "incident_id": "INC-20260930-001",
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
  },

  "impact": {
    "affected_services": [
      {
        "category": "112",
        "name": "112시스템",
        "criticality": "VERY_HIGH"
      },
      {
        "category": "행정",
        "name": "온나라",
        "criticality": "NORMAL"
      },
      {
        "category": "행정",
        "name": "폴넷",
        "criticality": "NORMAL"
      }
    ],
    "impact_basis": "LOCATION_MAPPING",
    "verification_status": "UNVERIFIED",
    "overall_criticality": "VERY_HIGH",
    "recovery_priority": "P1"
  },

  "timeline": [
    {
      "timestamp": "2026-09-30T10:21:02",
      "stage": "PRECURSOR",
      "device": "2층 층간스위치",
      "event_type": "MAC_FLAPPING",
      "summary": "MAC 주소 반복 이동 감지"
    },
    {
      "timestamp": "2026-09-30T10:21:22",
      "stage": "PRECURSOR",
      "device": "백본스위치",
      "event_type": "BROADCAST_HIGH",
      "summary": "2층 방향 Broadcast 트래픽 증가"
    },
    {
      "timestamp": "2026-09-30T10:21:24",
      "stage": "INCIDENT",
      "device": "백본스위치",
      "event_type": "LINK_DOWN",
      "summary": "2층 네트워크 연결 중단"
    },
    {
      "timestamp": "2026-09-30T10:22:05",
      "stage": "ACTION",
      "device": "2층 층간스위치",
      "event_type": "PORT_DISABLED",
      "summary": "장애 의심 포트 차단"
    },
    {
      "timestamp": "2026-09-30T10:22:13",
      "stage": "RECOVERY",
      "device": "백본스위치",
      "event_type": "LINK_UP",
      "summary": "2층 네트워크 연결 복구"
    }
  ],

  "facts": [
    {
      "type": "MAC_FLAPPING",
      "timestamp": "2026-09-30T10:21:02",
      "device": "2층 층간스위치",
      "source_line": 4,
      "text": "MAC 주소 반복 이동이 확인됨"
    },
    {
      "type": "LOOP_DETECTED",
      "timestamp": "2026-09-30T10:21:06",
      "device": "2층 층간스위치",
      "source_line": 6,
      "text": "Loop Guard 관련 이벤트가 확인됨"
    },
    {
      "type": "CPU_HIGH",
      "timestamp": "2026-09-30T10:21:11",
      "device": "2층 층간스위치",
      "source_line": 8,
      "text": "CPU 사용률 상승이 확인됨"
    },
    {
      "type": "BROADCAST_HIGH",
      "timestamp": "2026-09-30T10:21:22",
      "device": "백본스위치",
      "source_line": 12,
      "text": "2층 방향 Broadcast 증가가 확인됨"
    },
    {
      "type": "LINK_DOWN",
      "timestamp": "2026-09-30T10:21:24",
      "device": "백본스위치",
      "source_line": 13,
      "text": "2층 네트워크 연결 중단이 확인됨"
    },
    {
      "type": "PORT_DISABLED",
      "timestamp": "2026-09-30T10:22:05",
      "device": "2층 층간스위치",
      "source_line": 19,
      "text": "장애 의심 포트가 차단됨"
    },
    {
      "type": "LINK_UP",
      "timestamp": "2026-09-30T10:22:13",
      "device": "백본스위치",
      "source_line": 22,
      "text": "2층 네트워크 연결 복구가 확인됨"
    }
  ],

  "recurrence": {
    "status": "UNKNOWN",
    "similar_incident_count": null
  },

  "analysis_context": {
    "log_source_count": 2,
    "devices_analyzed": [
      "2층 층간스위치",
      "백본스위치"
    ],
    "related_event_count": 17
  }
}
```

---

# 24. 1층 Validation 기대값

1층 Sample은 주로 위치 및 업무 Mapping 검증에 사용한다.

핵심 기대값:

```json id="xom48k"
{
  "incident": {
    "location": "1층 네트워크",
    "status": "RECOVERED"
  },

  "impact": {
    "affected_services": [
      {
        "name": "KICS(킥스)",
        "criticality": "HIGH"
      },
      {
        "name": "온나라",
        "criticality": "NORMAL"
      },
      {
        "name": "폴넷",
        "criticality": "NORMAL"
      }
    ],

    "overall_criticality": "HIGH",
    "recovery_priority": "P2"
  }
}
```

---

# 25. 3층 Validation 기대값

3층 Sample은 주로 위치 및 업무 Mapping 검증에 사용한다.

핵심 기대값:

```json id="7jczlu"
{
  "incident": {
    "location": "3층 네트워크",
    "status": "RECOVERED"
  },

  "impact": {
    "affected_services": [
      {
        "name": "TCS",
        "criticality": "HIGH"
      },
      {
        "name": "온나라",
        "criticality": "NORMAL"
      },
      {
        "name": "폴넷",
        "criticality": "NORMAL"
      }
    ],

    "overall_criticality": "HIGH",
    "recovery_priority": "P2"
  }
}
```

---

# 26. Interface 변경 절차

A/B Interface 변경이 필요한 경우 다음 순서를 따른다.

```text id="d0hdmb"
1. interface-spec.md 수정
2. data-spec.md와 정합성 확인
3. A/B 합의
4. Expected JSON 수정
5. A 구현 수정
6. B Mock 및 구현 수정
7. 테스트 재실행
```

A 또는 B가 단독으로 필드 의미를 변경하지 않는다.

---

# 27. Developer A Definition of Done

A 구현은 최소 다음 조건을 만족해야 한다.

```text id="v5d9xf"
□ 여러 장비 로그 Parsing

□ 관련 이벤트 선별

□ 무관 장비 이벤트 제외

□ 장애 위치 식별

□ 1층 Mapping 정상
□ 2층 Mapping 정상
□ 3층 Mapping 정상

□ impact_basis 생성

□ verification_status 생성

□ 업무 중요도 계산

□ 복구 우선순위 계산

□ detected_time 생성
□ start_time 생성
□ recovery_time 생성
□ end_time 생성

□ 관리자용 Timeline 생성

□ Fact timestamp 생성
□ Fact device 생성
□ Fact source_line 생성

□ 현재 상태 판단

□ recurrence 반환

□ analysis_context 생성

□ interface-spec 구조 준수

□ Golden Sample Expected 일치

□ Validation Samples 통과

□ pytest PASS
```

---

# 28. Developer B 사용 원칙

B는 A 구현이 완료되기 전에도 본 문서의 JSON을 Mock 데이터로 사용하여 개발할 수 있다.

B는 AI에게 가능한 한 전체 원본 로그를 직접 전달하기보다 다음 구조화 데이터를 우선 전달한다.

```text id="i8jk64"
incident
+
impact
+
timeline
+
facts
+
analysis_context
```

AI는 이를 이용하여 다음을 생성한다.

```text id="dxr84e"
원인 후보
근거
부족하거나 반대되는 근거
추가 확인사항
```

AI가 A의 Rule 기반 결과를 임의로 변경하지 않는다.

---

# 29. 최종 원칙

본 Interface의 핵심 구조는 다음과 같다.

```text id="y2py4x"
여러 장비 원본 로그
        ↓
A Core
        ↓
Incident 재구성
        ↓
위치 / 시간 / 영향 가능 업무
        ↓
업무 중요도 / 복구 우선순위
        ↓
Timeline / Fact / Evidence
        ↓
A/B JSON
        ↓
B AI 분석
        ↓
관리자 판단지원
```

본 PoC의 최종 목적은 장애원인을 자동 확정하는 것이 아니다.

> 여러 장비에서 발생한 기술 이벤트를 하나의 Incident로 재구성하고, 담당자가 장애 위치·업무영향·복구 우선순위·원인 후보를 신속하게 판단할 수 있는 구조화 정보로 변환한다.