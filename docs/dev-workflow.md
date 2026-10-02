# Developer A / B Collaboration Workflow

## 1. 기본 원칙

Developer A와 Developer B는 동일 Repository에서 서로 다른 Branch를 사용하여 병렬 개발한다.

```text
Developer A
feature/core-analysis

Developer B
feature/web-ai-report
```

`main`에서 직접 개발하지 않는다.

---

## 2. 병렬 개발

Developer A:

```text
Raw Log
→ Core Analysis
→ A/B Interface Result
```

Developer B:

```text
Mock Core
→ AI
→ Report Builder
→ Web
```

B는 A 구현 완료를 기다리지 않고 Mock 데이터를 이용하여 독립적으로 개발한다.

---

## 3. A 완료 및 인수인계

Developer A:

```text
Core 구현
↓
1F Validation PASS
↓
2F Golden Sample PASS
↓
3F Validation PASS
↓
pytest PASS
↓
Pull Request
```

A PR 생성 후 Developer B가 A/B Interface를 Review한다.

검토 대상:

```text
incident
impact
timeline
facts
recurrence
analysis_context
```

---

## 4. A Merge

B의 Interface Review가 완료된 후 A PR을 `main`에 Merge한다.

순서:

```text
A 개발 완료
↓
A Test PASS
↓
A PR
↓
B Interface Review
↓
A PR main Merge
```

---

## 5. B 실제 통합

A Merge 이후 Developer B는 최신 `main`을 자신의 Branch에 반영한다.

```bash
git checkout feature/web-ai-report
git merge main
```

이후 Mock Core를 실제 A Core Result로 교체한다.

실제 실행흐름:

```text
Raw Log
↓
A Core
↓
Python dict / Pydantic Object
↓
B AI Adapter
↓
Report Builder
↓
Web
```

`interface-spec.md`의 JSON은 데이터 구조 계약을 의미한다.

실제 프로그램에서 중간 JSON 파일을 반드시 생성할 필요는 없다.

---

## 6. 최종 Integration

```text
A Core
↓
B AI
↓
Report Builder
↓
Web
↓
Integration Test
```

다음이 모두 PASS해야 한다.

```text
1F
2F
3F
Mock Integration
A/B Integration
pytest
```

---

## 7. B 완료

```text
B Integration PASS
↓
B PR
↓
A Review
↓
B PR main Merge
```

---

## 8. 최종 협업 흐름

```text
A                         B
────────────────────────────────

Core 개발                 Mock 기반 개발
↓                         ↓
3 Sample PASS             AI / Report / Web
↓                         ↓
pytest PASS               Mock Integration PASS
↓
A PR
          ─────────────→  Interface Review
↓
main Merge
          ─────────────→  최신 main 반영
                          ↓
                          실제 A Core 연결
                          ↓
                          A/B Integration
                          ↓
                          pytest PASS
                          ↓
                          B PR
A Review  ←───────────────
↓
B Merge
```