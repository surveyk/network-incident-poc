## 2인 개발 운영원칙

Developer A와 Developer B는 동일 Repository의 별도 Branch에서 병렬 개발한다.

- Developer A: `feature/core-analysis`
- Developer B: `feature/web-ai-report`

Developer B는 A 구현 완료 전까지 Mock Core 데이터를 이용해 AI / Report / Web 영역을 독립적으로 개발한다.

Developer A가 1F·2F·3F Sample 및 전체 Test를 통과하면 B가 A/B Interface를 Review한다. Interface 확인 후 A Branch를 `main`에 Merge한다.

이후 Developer B는 최신 `main`을 반영하고 Mock Core를 실제 A Core Result로 교체하여 최종 통합한다.

실제 A/B Integration에서는 `interface-spec.md`의 구조를 만족하는 Python `dict` 또는 Pydantic Object를 직접 전달하는 방식을 우선하며, 중간 JSON 파일 저장은 필수로 하지 않는다.

상세 협업절차는 `docs/dev-workflow.md`를 따른다.