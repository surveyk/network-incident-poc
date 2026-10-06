## 1인 D-Day 개발 운영원칙

본 PoC는 기존 2인 병렬개발 계획에서 **1인 D-Day 개발 방식**으로 변경한다.

기존 `JOB_261007_A.md`, `JOB_261007_B.md` 및 관련 설계문서는 Core Analysis, AI, Report, Web 구현을 위한 상세 참고자료로 유지한다.

실제 D-Day 개발은 별도의 `JOB_261007_SOLO.md`를 기준으로 진행한다.

개발은 하나의 작업 Branch에서 수행한다.

- D-Day 작업 Branch: `feature/solo-poc`

개발 우선순위는 다음과 같다.

```text
Core Analysis
↓
2층 Golden Sample 검증
↓
1층 / 3층 Validation
↓
관리자 Report / Web
↓
Mock AI
↓
Azure OpenAI
↓
전체 Test / Demo
```

하루 안에 End-to-End PoC를 완성하는 것을 최우선으로 하며, 모든 기존 설계 기능을 구현하는 것을 필수 목표로 하지 않는다.

특히 다음 핵심 흐름의 완성을 우선한다.

```text
Raw Log
↓
장애 사건 재구성
↓
영향 가능 업무 Mapping
↓
업무 중요도 / 복구 우선순위
↓
Timeline / Facts
↓
AI 원인 후보 및 추가확인
↓
관리자 장애 상황보고
```

Azure OpenAI 연결이나 부가기능 구현이 일정 내 완료되지 않더라도 Mock AI를 활용하여 전체 PoC 흐름과 관리자 보고서가 동작하도록 유지한다.

개발 중 새로운 기능 추가나 과도한 구조 변경은 지양하며, 기존 Specification과 Expected 데이터를 기준으로 최소 범위에서 구현한다.

상세 D-Day 실행절차는 `JOB_261007_SOLO.md`를 따른다.

기존 2인 개발 협업절차인 `docs/dev-workflow.md`는 설계 이력 및 참고자료로 유지한다.

## Git Branch 전략

기존 2인 개발에서 사용하던 다음 Branch는 D-Day 실제 개발에 사용하지 않는다.

```text
feature/core-analysis
feature/web-ai-report
```

1인 D-Day 개발은 다음 하나의 Branch에서 진행한다.

```text
feature/solo-poc
```

`main`에서는 직접 개발하지 않는다.

---

## D-Day 최초 시작

개발용 노트북에 Repository가 없는 경우:

```powershell
git clone https://github.com/surveyk/network-incident-poc.git

cd network-incident-poc

git checkout -b feature/solo-poc
```

확인:

```powershell
git status
git branch -vv
```

정상 상태 예:

```text
On branch feature/solo-poc
```

---

## 이미 Repository를 Clone한 경우

기존 Repository가 있는 경우 먼저 `main`을 최신 상태로 맞춘다.

```powershell
git checkout main
git pull origin main
```

그다음:

```powershell
git checkout -b feature/solo-poc
```

이미 Branch가 존재한다면:

```powershell
git checkout feature/solo-poc
```

---

## 개발 중 기본 Git 사용

기능 단위로 다음 순서를 반복한다.

```text
기능 구현
↓
Test
↓
PASS
↓
Commit
```

예:

```powershell
git status
git add .
git commit -m "feat: add core incident analysis"
```

필요할 때 원격에 Push:

```powershell
git push -u origin feature/solo-poc
```

최초 Push 이후에는:

```powershell
git push
```

만 사용해도 된다.

---

## D-Day 종료 시

전체 Test와 Demo 확인 후:

```powershell
git status
git add .
git commit -m "feat: complete solo network incident poc"
git push
```

그 후 `feature/solo-poc`를 `main`에 Merge한다.

---

## Git 운영 원칙

```text
main
= 준비 완료 / 안정본

feature/solo-poc
= D-Day 실제 개발

JOB_261007_A.md
JOB_261007_B.md
= 참고자료

JOB_261007_SOLO.md
= 실제 실행 기준
```