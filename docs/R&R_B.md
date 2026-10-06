
# Network Incident PoC
# Developer B — 역할 및 처리흐름
> ## 현재 운영기준 안내
>
> 본 문서는 최초 **2인 병렬개발 환경에서 Developer B의 역할과 책임범위(R&R)**를 정의하기 위해 작성된 참고자료이다.
>
> 현재 D-Day 개발방식은 **1인 개발**로 변경되었으며, 실제 개발 실행순서와 우선순위는 다음 문서를 기준으로 한다.
>
> ```text
> JOB_261007_SOLO.md
> ```
>
> 따라서 본 문서에서 사용하는 `Developer A`, `Developer B`, A/B 인수인계 등의 표현은 현재 개발 인원 구성을 의미하지 않는다.
>
> 다만 다음과 같은 **기술적 역할 경계는 계속 유효하다.**
>
> ```text
> Core Analysis
> = Fact / Rule
>
> AI Analysis
> = Inference
>
> Report Builder
> = Composition
>
> Web
> = Presentation
>
> Human
> = Final Decision
> ```
>
> 특히 AI / Report / Web 영역은 Core가 생성한 다음 정보를 임의로 변경하지 않는다.
>
> ```text
> 장애 위치
> 영향 가능 업무
> 업무 중요도
> 복구 우선순위
> 장애시간
> 현재 상태
> Facts
> Recurrence
> ```
>
> 본 문서는 AI / Report / Web 영역의 상세 설계 참고자료로 유지하며, 실제 D-Day 개발순서 및 완료기준은 `JOB_261007_SOLO.md`와 `.github/copilot-instructions.md`를 우선한다.
>
> ---

## 1. 목적

Developer B는 Developer A가 생성한 구조화된 Incident JSON을 입력으로 받아 다음 기능을 구현한다.

```text
A Core JSON
↓
AI 분석
↓
AI 결과 구조화
↓
Report Builder
↓
Web UI
↓
관리자 장애 상황보고
```

Developer B는 A의 Core Analysis 로직을 재구현하지 않는다.

---

# 2. B의 핵심 역할

B는 다음 질문에 답하는 영역을 담당한다.

```text
왜 이런 장애가 발생했을 가능성이 있는가?

그 판단의 근거는 무엇인가?

무엇이 아직 확인되지 않았는가?

추가로 무엇을 확인해야 하는가?

관리자가 빠르게 판단할 수 있도록
어떻게 보여줄 것인가?
```

---

# 3. B가 입력받는 데이터

B는 A가 생성한 다음 JSON을 입력으로 사용한다.

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

이 구조는 `docs/interface-spec.md`를 따른다.

B는 A 내부 Parser나 Analyzer의 구현방식에 의존하지 않는다.

---

# 4. B가 변경하지 않는 값

다음 값은 A의 Rule 기반 결과이므로 B가 임의로 변경하지 않는다.

```text
장애 위치
관련 장비
장애 발생시간
복구시간
현재 상태

영향 가능 업무
업무 중요도
복구 우선순위

Timeline의 사실관계
Fact
반복 장애 여부
```

예:

```text
A 결과:
overall_criticality = VERY_HIGH
recovery_priority = P1
```

AI가 다음과 같이 바꾸면 안 된다.

```text
AI 판단:
HIGH / P2
```

---

# 5. B 전체 처리흐름

B 처리흐름은 다음과 같이 고정한다.

```text
A Core JSON
      ↓
Input Validation
      ↓
AI Prompt Builder
      ↓
Azure OpenAI
      ↓
AI Response Validation
      ↓
Structured AI Result
      ↓
Report Builder
      ↓
View Model
      ↓
Web UI
```

Azure OpenAI 실패 시에는 다음 흐름을 사용한다.

```text
A Core JSON
      ↓
AI 호출 실패
      ↓
Fallback
      ↓
A Core 기반 보고서
      ↓
Web UI
```

즉:

```text
AI Failure
≠
Application Failure
```

---

# 6. B 내부 영역 구분

B는 크게 네 영역으로 나눈다.

## 영역 1 — AI Adapter

역할:

```text
A JSON
↓
AI 입력 Prompt
↓
Azure OpenAI 호출
↓
구조화된 AI 결과
```

담당 파일 예:

```text
src/llm/
├── azure_openai.py
└── prompt_builder.py
```

1일 PoC에서는 필요하면 한 파일로 단순화해도 된다.

---

## 영역 2 — AI Result

AI가 반환해야 하는 핵심 정보:

```text
summary
hypotheses
additional_checks
```

원인 후보에는 가능하면 다음 정보가 포함된다.

```text
cause
evidence
uncertainty
```

예:

```json
{
  "cause": "L2 Loop 가능성",
  "evidence": [
    "MAC 주소 반복 이동",
    "Broadcast 증가",
    "포트 차단 이후 복구"
  ],
  "uncertainty": [
    "실제 물리적 연결상태 미확인"
  ]
}
```

---

# 7. Report Builder

Report Builder는 A 결과와 AI 결과를 결합한다.

입력:

```text
A Core Result
+
AI Result
```

출력:

```text
관리자용 보고서 데이터
```

Report Builder는 새로운 장애 판단을 하지 않는다.

역할은 다음과 같다.

```text
데이터 조합
중복 제거
표현 정리
보고서 항목 배치
```

---

# 8. 관리자 보고서 구조

기존 `report-spec.md`를 기준으로 한다.

최종 보고서:

```text
1. 장애 요약
2. 장애경과
3. 조치내용
4. 추정원인 및 추가확인
```

첫 화면에서 우선 보여줄 정보:

```text
발생일시
장애구간
영향 가능 업무
업무 중요도
복구 우선순위
현재상태
반복 장애 여부
```

AI 정보는 다음 영역에 사용한다.

```text
추정원인
추정근거
불확실성
추가확인사항
```

---

# 9. Web UI 역할

Web UI는 화려한 Dashboard보다 **장애 상황보고서** 형태를 우선한다.

화면 기본 구조:

```text
[Network Incident PoC]

장애 상황보고

┌ 장애 요약 ┐

┌ 장애경과 ┐

┌ 조치내용 ┐

┌ 추정원인 / 추가확인 ┐

[기술 상세정보]
```

관리자가 첫 화면에서 기술 로그 전체를 볼 필요는 없다.

---

# 10. 기술 상세정보

필요 시 별도 영역에서 다음 정보를 보여준다.

```text
Timeline 상세
Facts
Fact 발생장비
Fact timestamp
source_line
analysis_context
```

원본 로그 전체를 관리자용 본문에 반복하지 않는다.

---

# 11. A/B 경계

A의 최종 책임:

```text
Fact
```

B의 시작점:

```text
Inference
```

이를 다음과 같이 유지한다.

```text
A
로그에서 실제 확인된 사실
        ↓
B
사실들 사이의 관계 해석
        ↓
담당자
최종 판단
```

---

# 12. AI 역할

AI는 다음을 수행한다.

```text
원인 후보 생성
근거 연결
부족한 근거 표시
추가 확인 제안
간결한 설명 생성
```

AI는 다음을 수행하지 않는다.

```text
업무 중요도 결정
복구 우선순위 결정
실제 서비스 장애 확정
최종 장애원인 확정
책임자 판단
```

---

# 13. B 권장 파일구조

B는 다음 구조를 기본으로 한다.

```text
src/
├── llm/
│   ├── __init__.py
│   └── azure_openai.py
│
├── report/
│   ├── __init__.py
│   └── report_builder.py
│
└── app.py

templates/
└── index.html

tests/
├── test_ai.py
├── test_report.py
└── test_app.py
```

필요하면 AI Prompt Builder를 별도 파일로 분리할 수 있다.

```text
src/llm/prompt_builder.py
```

하지만 1일 PoC에서는 과도하게 파일을 늘리지 않는다.

---

# 14. B가 수정하지 않는 A 파일

가능한 한 다음 파일은 B가 직접 수정하지 않는다.

```text
src/parser.py
src/analyzer.py
src/impact.py
src/timeline.py
src/core.py
```

실제 A 구현 파일명이 달라져도 원칙은 동일하다.

B는 A의 Core 내부 구현이 아니라 최종 JSON Interface에 의존한다.

---

# 15. Mock 기반 병렬 개발

A 구현이 완료되지 않아도 B는 개발을 시작한다.

입력은 `interface-spec.md`에 정의된 Golden Sample JSON을 사용한다.

예:

```text
Mock A JSON
↓
AI
↓
Report
↓
Web
```

A가 Merge된 후:

```text
Mock
↓
실제 Core Result
```

로 교체한다.

---

# 16. B의 테스트 기준

B는 최소 다음 상황을 테스트한다.

```text
1. 정상 A JSON 입력

2. 2층 Loop
   → AI 원인 후보 생성

3. 1층 단순 Link 장애
   → 과도한 원인추정 방지

4. 3층 단순 Link 장애
   → 과도한 원인추정 방지

5. Azure OpenAI 실패

6. 잘못된 AI Response

7. AI 없이도 관리자 보고서 생성
```

---

# 17. Azure OpenAI 실패 원칙

AI 장애가 발생하더라도 다음 정보는 보여야 한다.

```text
장애 위치
영향 가능 업무
업무 중요도
복구 우선순위
현재 상태
Timeline
Facts
```

AI 영역만:

```text
AI 분석 사용 불가
```

로 표시한다.

---

# 18. B 성공 기준

B는 다음이 가능하면 완료한다.

```text
A JSON 입력
↓
Azure OpenAI 분석
↓
구조화 AI 결과
↓
관리자 보고서 생성
↓
Web 출력
```

그리고:

```text
Azure OpenAI 장애
↓
Fallback 보고서 정상 출력
```

도 가능해야 한다.

---

# 19. B Definition of Done

```text
□ A/B JSON 입력 가능

□ Azure OpenAI 연결

□ AI Prompt 생성

□ 구조화 AI 응답 생성

□ summary
□ hypotheses
□ evidence
□ uncertainty
□ additional_checks

□ AI Failure 처리

□ Report Builder

□ 관리자 1페이지 보고서

□ 기술 상세정보

□ Web UI

□ 1층 Sample 확인
□ 2층 Golden Sample 확인
□ 3층 Sample 확인

□ A 실제 JSON 연동

□ Integration Test PASS
```

---

# 20. 최종 역할분리

전체 프로젝트 역할은 다음과 같이 확정한다.

```text
Developer A
====================
What happened?

어디서?
언제?
무슨 일이?
어떤 업무 영향?
복구 우선순위?
로그 Fact?


Developer B
====================
Why might it have happened?

가능한 원인?
근거?
불확실성?
추가확인?
어떻게 보고할 것인가?


Human
====================
What is the final decision?

최종 장애원인
실제 업무영향
후속조치
```