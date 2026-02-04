# Sandy Design Direction

Sandy의 설계 방향성을 정리한 문서입니다.

## 핵심 철학

> **Sandy는 Agent가 자율적으로 사용하는 도구다.**
> 사람이 명령어를 입력하는 게 아니라, Agent가 판단해서 시나리오를 생성하고 재사용한다.

## 사용자 정의

| 구분 | 설명 |
|------|------|
| **1차 사용자** | Agent (LLM) |
| **2차 사용자** | Agent를 사용하는 개발자 |
| **사용 맥락** | MCP 도구를 연결해서 사용하는 모든 상황 |

## Agent의 Sandy 사용 흐름

### 1. 시나리오 생성 (자동)

```
작업 수행 중 "이건 반복될 수 있겠다" 판단
→ MCP 호출 기록
→ 변수화 판단 (LLM이 결정)
→ 시나리오 저장 (.sandy/scenarios/)
→ 이름/설명 자동 생성
```

### 2. 시나리오 재사용

```
새 작업 요청 받음
→ 기존 시나리오 탐색 (.sandy/scenarios/)
→ 이름/description으로 매칭
→ 전체 또는 일부(--start/--end) 재사용
```

### 3. 에러 처리

```
시나리오 실행 실패
→ 에러 정보 분석 (MCP 도구 정보 + 시나리오 단계)
→ Agent가 판단: 직접 복구 또는 사용자에게 보고
```

## 시나리오 저장 판단 기준

Agent가 스스로 판단하되, 다음 상황에서 저장을 고려:

- 같은 MCP 도구 조합을 2번 이상 사용
- 사용자가 "반복", "매일", "자동화" 등의 키워드 사용
- 명확한 워크플로우가 형성된 경우

## 시나리오 부분 재사용

시나리오의 일부만 사용 가능:

```bash
# 스텝 1~3만 실행 (예: HN 접근까지만)
python play.py scenario.json --start 1 --end 3
```

Agent는 시나리오 파일을 읽고 필요한 범위를 판단.

## 시나리오 탐색

- 위치: `.sandy/scenarios/`
- 매칭 기준: `metadata.name`, `metadata.description`
- Agent가 Glob/Read로 직접 탐색

## Skill MD 구조 방향

### 포함할 내용

| 섹션 | 내용 |
|------|------|
| **Why Sandy** | 언제/왜 시나리오를 만들어야 하는지 |
| **저장 판단 기준** | 반복 가능성 판단 가이드라인 |
| **탐색 방법** | `.sandy/scenarios/` 구조, 매칭 기준 |
| **생성 방법** | 스키마 요약 + 상세는 `schema.md` 참조 |
| **실행 방법** | CLI 호출 방식 (옵션 포함) |
| **에러 처리** | 실패 시 대응 방법 |

### 제거할 내용

- `/sandy play`, `/sandy new`, `/sandy list` 명령어 구조
- 사람용 튜토리얼 (Agent는 스키마만 있으면 됨)
- 중복 내용 (schema.md와 examples/README.md 간)

### 문서 분리 전략

```
skills/sandy/sandy.md     ← 핵심: 언제/왜 사용, 판단 기준, 기본 사용법
references/schema.md      ← 상세: JSON 스키마 (필요시 Read)
assets/examples/          ← 예제: 시나리오 파일들 (필요시 Read)
```

토큰 효율을 위해 Skill MD는 핵심만, 상세는 필요시 참조.

## 핵심 사용 시나리오

### 예시 1: 웹 스크래핑 자동화

```
사용자: "HN 탑 뉴스를 스크래핑해서 DB에 저장해줘"

Agent 동작:
1. 기존 시나리오 탐색 → 없음
2. 워크플로우 실행 (chrome-devtools → supabase)
3. "반복 가능성 있음" 판단
4. 시나리오 저장: hn-scrape-to-db.json
5. 다음 요청 시 시나리오 재사용
```

### 예시 2: 부분 재사용

```
사용자: "HN에서 다른 기사 찾아줘"

Agent 동작:
1. 기존 시나리오 탐색 → hn-scrape-to-db.json 발견
2. 시나리오 분석: step 1-2가 "HN 접근"
3. --end 2로 부분 실행
4. 이후 작업은 직접 수행
```

### 예시 3: 시나리오 실행 실패

```
시나리오 실행 중 step 3에서 실패

Agent 동작:
1. 에러 정보 분석 (MCP 응답 + 시나리오 단계)
2. 원인 파악: 요소를 찾지 못함
3. 판단: 페이지 구조 변경됨
4. 대응: 직접 해결 시도 또는 사용자에게 보고
```

## 다음 단계

1. [ ] `skills/sandy/sandy.md` 재작성 (Agent 중심)
2. [ ] `references/schema.md` 정리 (중복 제거)
3. [ ] `assets/examples/README.md` 정리 (한국어→영어, 중복 제거)
4. [ ] 명령어 구조 제거 또는 단순화
