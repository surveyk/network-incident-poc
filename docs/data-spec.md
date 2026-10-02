# Network Incident PoC — Data Specification

## 1. 목적

본 문서는 네트워크 장애분석 PoC에서 사용하는 기본 데이터 구조와 판단 기준을 정의한다.

A(Core Analysis)는 본 문서를 기준으로 다음 값을 생성한다.

- 장애 위치
- 영향 가능 업무
- 업무 중요도
- 복구 우선순위
- 현재 상태
- 반복 장애 여부
- 장애 Timeline
- 로그 기반 Fact
- 장애 발생 및 복구 관련 시각
- 분석에 사용된 장비 및 이벤트 정보

업무 중요도와 복구 우선순위는 사전에 정의된 기준정보를 사용한다.

AI가 임의로 업무 중요도나 복구 우선순위를 결정하거나 변경하지 않는다.

---

# 2. 기본 데이터 구성

PoC에서는 다음 데이터를 사용한다.

1. 장비정보
2. 업무정보
3. 업무 중요도
4. 복구 우선순위 기준
5. 장애이력
6. 장비 로그

입력되는 장비 로그는 장비정보 및 업무정보와 결합하여 장애 위치와 영향 가능 업무를 판단한다.

PoC의 핵심 원칙은 다음과 같다.

```text
장비 로그
+
장비 위치정보
+
업무 기준정보
=
장애 위치 및 영향 가능 업무 판단
```

장비 로그만으로 실제 업무서비스 장애 여부를 확정하지 않는다.

---

# 3. 장비정보

장비 식별자는 실제 로그에 나타나는 장비명을 사용한다.

사용자 또는 관리자에게 표시할 때는 기술적인 장비명보다 이해하기 쉬운 한글 표현을 사용한다.

## 기본 구조

```json
{
  "device_id": "SW-ACCESS-02",
  "display_name": "2층 층간스위치",
  "location": "2층",
  "floor": 2,
  "device_role": "ACCESS_SWITCH"
}
```

## PoC 장비 정의

| device_id | 표시명 | 위치 | floor | 역할 |
|---|---|---|---:|---|
| BACKBONE-SW | 백본스위치 | 중앙 | - | BACKBONE_SWITCH |
| SW-ACCESS-01 | 1층 층간스위치 | 1층 | 1 | ACCESS_SWITCH |
| SW-ACCESS-02 | 2층 층간스위치 | 2층 | 2 | ACCESS_SWITCH |
| SW-ACCESS-03 | 3층 층간스위치 | 3층 | 3 | ACCESS_SWITCH |
| SW-ACCESS-04 | 4층 층간스위치 | 4층 | 4 | ACCESS_SWITCH |
| SW-ACCESS-05 | 5층 층간스위치 | 5층 | 5 | ACCESS_SWITCH |
| SW-ACCESS-06 | 6층 층간스위치 | 6층 | 6 | ACCESS_SWITCH |
| SW-ACCESS-07 | 7층 층간스위치 | 7층 | 7 | ACCESS_SWITCH |
| SW-ACCESS-08 | 8층 층간스위치 | 8층 | 8 | ACCESS_SWITCH |
| SW-ACCESS-09 | 9층 층간스위치 | 9층 | 9 | ACCESS_SWITCH |
| SW-ACCESS-10 | 10층 층간스위치 | 10층 | 10 | ACCESS_SWITCH |

PoC에서는 1~3층을 실제 검증 대상으로 사용하고, 4~10층은 확장 가능 구조로 정의한다.

---

# 4. 장비 간 관계

PoC에서는 장애 발생 장비만 단독으로 분석하지 않고 가능한 경우 직접 연결된 상위 또는 인접 장비의 동일 시간대 이벤트를 함께 분석한다.

기본 관계는 다음과 같다.

```text
백본스위치
├─ 1층 층간스위치
├─ 2층 층간스위치
├─ 3층 층간스위치
├─ ...
└─ 10층 층간스위치
```

예를 들어 2층 장애 분석 시 다음 장비의 이벤트를 함께 사용할 수 있다.

```text
SW-ACCESS-02
+
BACKBONE-SW
```

이를 통해 단일 장비의 `LINK_DOWN` 이벤트만으로 판단하는 것보다 장애구간을 보다 신뢰성 있게 식별한다.

인접 장비 이벤트가 존재하지 않는 경우 해당 사실 자체를 분석조건으로 사용하며, 근거가 부족한 원인 판단은 수행하지 않는다.

PoC에서는 복잡한 Topology 자동탐색은 구현하지 않는다.

---

# 5. 층별 업무정보

전 층 공통업무와 층별 주요업무를 구분한다.

## 공통업무

| 업무분류 | 시스템 | 적용범위 |
|---|---|---|
| 행정 | 온나라 | 1~10층 |
| 행정 | 폴넷 | 1~10층 |

## 층별 주요업무

| 위치 | 업무분류 | 주요 시스템 |
|---|---|---|
| 1층 | 수사 | KICS(킥스) |
| 2층 | 112 | 112시스템 |
| 3층 | 교통 | TCS |
| 4~10층 | 기타 | PoC 범위 외 |

---

# 6. 영향 가능 업무 정의

본 PoC에서 장애 위치와 업무 Mapping을 통해 생성되는 업무목록은 실제 업무서비스 중단을 의미하지 않는다.

`affected_services`는 다음 의미로 사용한다.

> 장애 위치와 사전에 정의된 업무정보를 기반으로 식별한 **영향 가능 업무**

예를 들어 2층 네트워크 장애가 확인된 경우:

```text
영향 가능 업무
- 112시스템
- 온나라
- 폴넷
```

으로 표시한다.

이는 다음 의미가 아니다.

```text
112시스템 실제 장애 확정
온나라 실제 장애 확정
폴넷 실제 장애 확정
```

실제 업무서비스 장애 여부는 서비스 상태 또는 사용자 확인 등 별도의 근거가 필요하다.

PoC에서는 기본적으로 다음 상태를 사용한다.

```text
impact_basis = LOCATION_MAPPING
verification_status = UNVERIFIED
```

의미:

```text
LOCATION_MAPPING
= 장애 위치와 업무 Mapping에 따른 영향 가능 업무

UNVERIFIED
= 실제 서비스 장애 여부는 아직 확인되지 않음
```

---

# 7. 업무 중요도

업무 중요도는 사전에 정의된 값을 사용한다.

AI 또는 로그분석 결과가 업무 중요도를 임의로 변경하지 않는다.

| 업무분류 | 시스템 | 중요도 |
|---|---|---|
| 112 | 112시스템 | VERY_HIGH |
| 수사 | KICS(킥스) | HIGH |
| 교통 | TCS | HIGH |
| 행정 | 온나라 | NORMAL |
| 행정 | 폴넷 | NORMAL |

## 화면 표시값

| 내부값 | 화면 표시 |
|---|---|
| VERY_HIGH | 매우 높음 |
| HIGH | 높음 |
| NORMAL | 보통 |

---

# 8. 복구 우선순위

복구 우선순위는 장애구간에서 영향을 받을 가능성이 있는 업무 중 가장 높은 업무 중요도를 기준으로 결정한다.

| 최고 업무 중요도 | 복구 우선순위 | 화면 표시 |
|---|---|---|
| VERY_HIGH | P1 | 최우선 |
| HIGH | P2 | 신속 복구 |
| NORMAL | P3 | 일반 복구 |

## 예시

2층 장애:

```text
112시스템 = VERY_HIGH
온나라 = NORMAL
폴넷 = NORMAL

최고 중요도 = VERY_HIGH

→ 복구 우선순위 = P1
→ 화면 표시 = 최우선
```

AI가 복구 우선순위를 변경하지 않는다.

---

# 9. 장애 위치와 업무 영향 Mapping

장애 위치가 식별되면 해당 위치의 고유업무와 공통업무를 결합한다.

## 1층 장애

```text
KICS(킥스)
+ 온나라
+ 폴넷

→ overall_criticality = HIGH
→ recovery_priority = P2
```

## 2층 장애

```text
112시스템
+ 온나라
+ 폴넷

→ overall_criticality = VERY_HIGH
→ recovery_priority = P1
```

## 3층 장애

```text
TCS
+ 온나라
+ 폴넷

→ overall_criticality = HIGH
→ recovery_priority = P2
```

PoC에서는 장애구간을 식별한 후 이 Mapping을 이용하여 영향 가능 업무를 자동 생성한다.

1·2·3층은 각각 독립된 Sample을 이용하여 Mapping이 특정 층에 하드코딩되지 않았음을 검증한다.

---

# 10. 정규화 이벤트 구조

원본 장비 로그는 다음 구조로 변환한다.

```json
{
  "timestamp": "2026-09-30T10:21:02",
  "device_id": "SW-ACCESS-02",
  "device_name": "2층 층간스위치",
  "location": "2층",
  "event_type": "MAC_FLAPPING",
  "severity": "WARNING",
  "interface": "Gi1/0/18",
  "message": "MAC address flapping detected",
  "source_line": 4,
  "raw": "원본 로그 전체"
}
```

## 필수 필드

- timestamp
- device_id
- location
- event_type
- raw

가능한 경우 다음 정보도 보존한다.

- device_name
- interface
- severity
- message
- source_line

추출할 수 없는 필드는 `null`을 허용한다.

`source_line`은 최종 Fact에서 원본 로그 근거를 추적할 수 있도록 사용한다.

---

# 11. PoC 이벤트 유형

1일 PoC에서는 다음 이벤트를 우선 지원한다.

| event_type | 의미 |
|---|---|
| MAC_FLAPPING | MAC 주소 반복 이동 |
| LOOP_DETECTED | Loop 관련 이벤트 |
| BROADCAST_HIGH | Broadcast 증가 |
| CPU_HIGH | CPU 사용률 상승 |
| LINK_DOWN | 링크 단절 |
| LINK_UP | 링크 복구 |
| PORT_DISABLED | 포트 차단 |
| WARNING | 기타 경고 |
| UNKNOWN | 분류 불가 |

분류할 수 없는 로그는 삭제하지 않고 `UNKNOWN`으로 보존한다.

단, `UNKNOWN` 또는 정상 이벤트가 존재한다는 이유만으로 장애 Timeline에 포함하지 않는다.

---

# 12. 관련 이벤트 선별

입력 로그에는 장애와 관계없는 장비의 이벤트가 포함될 수 있다.

예:

```text
2층 장애 발생 중
1층 정상 Link 이벤트
3층 Configuration 이벤트
4층 정상 Interface 이벤트
```

A는 전체 로그를 Parsing한 후 Incident와 관련된 이벤트를 선별한다.

선별 기준은 다음과 같다.

```text
장애 위치와 관련된 장비
+
직접 연결된 상위 또는 인접 장비
+
동일 Incident 시간대 이벤트
```

무관 장비 이벤트는 원본에서는 보존하되 최종 Incident Timeline과 Fact에서는 제외한다.

---

# 13. 다중장비 상관분석

Incident 분석은 가능한 경우 단일 장비 이벤트만으로 판단하지 않는다.

기본 분석 관점은 다음과 같다.

```text
① 장애 발생 장비
무슨 이벤트가 발생했는가?

+

② 상위 또는 인접 장비
동일 시간대에 관련 이벤트가 발생했는가?

+

③ 조치 및 복구
어떤 변화 이후 정상화되었는가?
```

예:

```text
2층 층간스위치
MAC Flapping
        ↓
2층 층간스위치
Broadcast / CPU 증가
        ↓
백본스위치
2층 방향 Broadcast 증가
        ↓
백본 + 2층 장비
Link Down
        ↓
2층 장비
의심 포트 차단
        ↓
백본 + 2층 장비
Link Up / 정상화
```

A는 이 관계를 이용하여 장애 사건을 하나의 Incident Timeline으로 재구성한다.

A는 이러한 이벤트 관계를 이용해 장애 위치와 상태를 판단하지만, 최종 장애 원인을 확정하지 않는다.

---

# 14. 장애 관련 시간 정의

Incident에는 다음 네 가지 시각을 사용할 수 있다.

| 필드 | 의미 |
|---|---|
| detected_time | Incident와 관련된 최초 이상징후 시각 |
| start_time | 실제 네트워크 장애 발생 시각 |
| recovery_time | 네트워크 연결이 복구된 시각 |
| end_time | 관련 이상징후까지 최종 정상화된 시각 |

## 2층 Loop 예시

```text
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

일부 단순 장애에서는 모든 시각을 구분할 수 없을 수 있다.

예를 들어 최초 확인 이벤트가 바로 `LINK_DOWN`인 경우:

```text
detected_time = start_time
```

으로 처리할 수 있다.

정확한 값을 판단할 수 없는 필드는 임의로 생성하지 않는다.

---

# 15. Timeline 단계

관리자용 Timeline은 모든 로그를 보여주지 않는다.

이벤트는 다음 단계 중 하나로 분류한다.

| 단계 | 의미 |
|---|---|
| PRECURSOR | 장애 전 이상징후 |
| INCIDENT | 실제 장애 발생 |
| ACTION | 운영자 조치 |
| RECOVERY | 연결 또는 기능 복구 |
| NORMALIZED | 관련 상태 최종 정상화 |

## 2층 Loop 예시

```text
10:21:02 MAC_FLAPPING → PRECURSOR
10:21:22 BROADCAST_HIGH → PRECURSOR
10:21:24 LINK_DOWN → INCIDENT
10:22:05 PORT_DISABLED → ACTION
10:22:13 LINK_UP → RECOVERY
10:22:19 CPU 정상화 → NORMALIZED
```

관리자 보고서에는 이 중 핵심 4~6개 이벤트만 사용한다.

전체 원본 로그와 관리자 Timeline을 동일하게 취급하지 않는다.

---

# 16. 현재 상태 판단

장애 상태는 다음 값을 사용한다.

| 내부값 | 의미 | 화면 표시 |
|---|---|---|
| ACTIVE | 장애 지속 중 | 장애 지속 |
| RECOVERING | 일부 복구 | 복구 중 |
| RECOVERED | 네트워크 정상화 | 복구 완료 |
| UNKNOWN | 판단 불가 | 확인 필요 |

PoC에서는 일반적으로 다음 조건을 이용한다.

```text
LINK_DOWN 확인
+
이후 LINK_UP 확인
+
주요 관련 이상징후 정상화
=
RECOVERED
```

단순 Link 장애 Sample의 경우 양단 Link Up이 확인되면 `RECOVERED`로 판단할 수 있다.

실제 업무서비스 정상 여부와 네트워크 복구상태는 동일한 개념으로 취급하지 않는다.

---

# 17. 반복 장애 여부

반복 여부는 과거 장애이력이 존재할 경우 판단한다.

| 내부값 | 의미 | 화면 표시 |
|---|---|---|
| REPEATED | 동일·유사 장애 반복 확인 | 반복 장애 |
| NOT_REPEATED | 동일 장애 없음 | 반복 없음 |
| UNKNOWN | 과거 이력 없음 또는 미확인 | 확인 필요 |

1일 PoC에서는 과거 장애 DB를 구현하지 않는다.

따라서 기본값은:

```text
UNKNOWN
→ 화면 표시: 확인 필요
```

로 처리한다.

`NOT_REPEATED`를 임의로 반환하지 않는다.

향후 장애이력이 축적되면 다음 정보를 기준으로 확장할 수 있다.

```text
동일 위치
+
유사 이벤트 패턴
+
일정 기간 내 발생이력
```

---

# 18. 로그 기반 Fact

Fact는 원본 로그에서 직접 확인 가능한 내용만 생성한다.

Fact는 가능하면 원본 근거를 추적할 수 있도록 다음 정보를 포함한다.

```json
{
  "type": "MAC_FLAPPING",
  "timestamp": "2026-09-30T10:21:02",
  "device": "2층 층간스위치",
  "source_line": 4,
  "text": "MAC 주소 반복 이동이 확인됨"
}
```

## Fact 예시

```text
- 2층 층간스위치에서 MAC Flapping 발생
- Broadcast 증가 이벤트 확인
- 백본스위치에서 2층 연결 Down 확인
- 장애 의심 포트 차단 확인
- 이후 2층 연결 Up 확인
```

다음과 같은 내용은 Fact에 포함하지 않는다.

```text
- Loop가 최종 장애 원인이다.
- 케이블 연결이 잘못되었다.
- 112시스템이 실제로 중단되었다.
```

위 내용은 로그만으로 직접 확인할 수 없기 때문이다.

장애 원인 후보와 추가 확인사항은 B의 AI 분석영역에서 처리한다.

---

# 19. 분석 Context

A는 필요 시 분석에 사용된 로그 범위를 다음과 같이 요약할 수 있다.

예:

```json
{
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

의미:

- `log_source_count`: Incident 분석에 사용된 장비 수
- `devices_analyzed`: 관련 이벤트가 사용된 장비
- `related_event_count`: Incident 분석에 사용된 관련 이벤트 수

`analysis_context`는 관리자용 보고서에 반드시 표시할 필요는 없으며, 기술 상세정보 및 AI 분석 Context로 사용할 수 있다.

---

# 20. L3 장비 장애정보 확장 방향

PoC에서는 Syslog 형태의 이벤트를 사용한다.

실제 운영환경에서는 L3 장비에서 단순 `LINK_DOWN`, `LINK_UP` 외 다음 정보를 함께 활용하면 장애 판단 신뢰성을 높일 수 있다.

## Interface 상태

```text
LINK_DOWN
LINK_UP
LINE_PROTOCOL_DOWN
LINE_PROTOCOL_UP
```

## Routing Neighbor

```text
OSPF Neighbor Down / Full
BGP Session Down / Established
VRRP 또는 HSRP 상태 변경
```

## Interface 품질

```text
CRC Error
Input Error
Output Error
Packet Drop
Traffic 증가
Broadcast / Multicast 증가
```

## 장비 상태

```text
CPU
Memory
Temperature
Power
Fan
Reboot
Configuration Change
```

향후 운영환경에서는 다음과 같이 확장할 수 있다.

```text
Syslog
+
SNMP Trap
+
Interface Counter
+
Routing Neighbor Event
+
장비 Resource Event
```

단, 본 1일 PoC에서는 해당 기능을 구현하지 않는다.

---

# 21. Golden Sample 및 Validation Sample

PoC에서는 다음 3개의 Sample을 사용한다.

## 1층 Validation Sample

목적:

- 1층 위치 식별
- KICS Mapping
- HIGH / P2 판단
- 백본 + 1층 장비 이벤트 결합

기대값:

```text
장애 위치 = 1층 네트워크

영향 가능 업무
KICS(킥스)
온나라
폴넷

업무 중요도 = HIGH
복구 우선순위 = P2
현재상태 = RECOVERED
```

---

## 2층 Golden Sample

목적:

- 복합 장애 이벤트 분석
- 다중장비 Timeline
- 112 업무 Mapping
- VERY_HIGH / P1 판단
- Fact 및 근거 생성
- AI 분석 입력 제공

기대 핵심값:

```json
{
  "location": "2층 네트워크",
  "affected_services": [
    "112시스템",
    "온나라",
    "폴넷"
  ],
  "criticality": "VERY_HIGH",
  "recovery_priority": "P1",
  "status": "RECOVERED",
  "recurrence": "UNKNOWN"
}
```

시간 기대값:

```text
detected_time = 10:21:02
start_time = 10:21:24
recovery_time = 10:22:13
end_time = 10:22:19
```

---

## 3층 Validation Sample

목적:

- 3층 위치 식별
- TCS Mapping
- HIGH / P2 판단
- 백본 + 3층 장비 이벤트 결합

기대값:

```text
장애 위치 = 3층 네트워크

영향 가능 업무
TCS
온나라
폴넷

업무 중요도 = HIGH
복구 우선순위 = P2
현재상태 = RECOVERED
```

1·2·3층 Sample이 모두 통과해야 위치 또는 업무 Mapping을 특정 Sample에 하드코딩하지 않은 것으로 판단한다.

---

# 22. Sample 파일 구성

PoC Sample은 다음 구조를 사용한다.

```text
data/
├── sample_logs/
│   ├── link_1f.log
│   ├── loop_2f.log
│   └── link_3f.log
│
└── expected/
    ├── link_1f_expected.json
    ├── loop_2f_expected.json
    └── link_3f_expected.json
```

`loop_2f.log`는 전체 기능을 검증하는 Golden Sample이다.

`link_1f.log`와 `link_3f.log`는 위치 및 업무 Mapping이 2층에 하드코딩되지 않았음을 검증하기 위한 Validation Sample이다.

---

# 23. A 개발 범위

A는 다음 기능까지 담당한다.

```text
여러 장비 원본 로그
→ Parsing
→ Normalization
→ Event Classification
→ 관련 이벤트 선별
→ 장비 간 시간 상관관계 확인
→ Timeline 생성
→ 장애 위치 식별
→ 영향 가능 업무 Mapping
→ 업무 중요도 조회
→ 복구 우선순위 판단
→ 장애시간 식별
→ 현재 상태 판단
→ 반복 여부 반환
→ Fact 및 근거 생성
→ A/B Interface JSON
```

A는 AI 기반 원인추정을 구현하지 않는다.

AI 추정, Web 화면 및 최종 자연어 보고서 생성은 B 영역에서 처리한다.

---

# 24. A 판단 원칙

A의 목적은 장애 원인을 최종 확정하는 것이 아니다.

A는 다음 질문에 답할 수 있어야 한다.

```text
어디서 발생했는가?
언제 이상징후가 시작됐는가?
언제 실제 장애가 발생했는가?
어떤 장비에서 관련 이벤트가 발생했는가?
어떤 순서로 상태가 변했는가?
어떤 업무에 영향 가능성이 있는가?
복구 우선순위는 무엇인가?
현재 네트워크 상태는 어떠한가?
로그로 직접 확인 가능한 사실은 무엇인가?
```

다음 질문은 B 및 담당자 판단영역이다.

```text
왜 장애가 발생했는가?
가장 가능성 높은 원인은 무엇인가?
추가로 무엇을 확인해야 하는가?
최종 장애원인은 무엇인가?
```

---

# 25. A 검증 기준

A 구현 완료 전 다음 항목을 검증한다.

## Parser / Normalizer

```text
□ 전체 로그 Parsing
□ 장비정보 Mapping
□ 원본 로그 보존
□ source_line 보존
□ 분류 불가 로그 UNKNOWN 처리
```

## Event Classification

```text
□ MAC_FLAPPING
□ LOOP_DETECTED
□ BROADCAST_HIGH
□ CPU_HIGH
□ LINK_DOWN
□ LINK_UP
□ PORT_DISABLED
□ WARNING
□ UNKNOWN
```

## Multi-device Analysis

```text
□ 장애 층 장비와 백본 이벤트 결합
□ 무관 층 이벤트 제외
□ 여러 장비 이벤트를 시간순으로 정렬
```

## Location / Impact

```text
□ 1층 위치 자동 식별
□ 2층 위치 자동 식별
□ 3층 위치 자동 식별

□ 1층 → KICS + 온나라 + 폴넷
□ 2층 → 112 + 온나라 + 폴넷
□ 3층 → TCS + 온나라 + 폴넷
```

## Criticality / Priority

```text
□ 1층 = HIGH / P2
□ 2층 = VERY_HIGH / P1
□ 3층 = HIGH / P2
```

## Incident Time

```text
□ detected_time
□ start_time
□ recovery_time
□ end_time
```

## Incident Status

```text
□ ACTIVE
□ RECOVERING
□ RECOVERED
□ UNKNOWN
```

Golden Sample에서는:

```text
RECOVERED
```

를 반환해야 한다.

## Fact / Evidence

```text
□ timestamp
□ device
□ source_line
□ 로그에서 직접 확인 가능한 내용만 포함
```

## Final Output

```text
□ interface-spec 준수
□ Golden Sample Expected 결과 일치
□ 1층 Validation Sample 통과
□ 3층 Validation Sample 통과
□ pytest PASS
```

---

# 26. PoC 범위 제한

다음 기능은 1일 PoC 범위에서 제외한다.

- 실시간 NMS 연동
- SNMP 실시간 수집
- 실제 업무서비스 상태 모니터링
- 장애이력 Database
- 자동 장애복구
- Topology 자동탐색
- 다중 제조사 완전 지원
- 반복장애 자동학습
- 장애 예방 예측
- AI 기반 복구우선순위 결정

본 PoC의 목표는 모든 장애를 자동 판정하는 것이 아니다.

최종 목표는 다음과 같다.

> 여러 네트워크 장비의 장애 이벤트를 하나의 Incident로 재구성하고, 장애 위치와 영향 가능 업무 및 복구 우선순위를 담당자가 신속하게 판단할 수 있는 정보로 변환한다.