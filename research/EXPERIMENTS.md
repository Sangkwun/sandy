# Sandy 실험 계획

> 핵심 기여 검증을 위한 실험 설계

---

## 실험 개요

| 실험 | 검증 대상 | RQ | 필수도 |
|------|----------|-----|--------|
| 실험 1 | 비용 절감 효과 | RQ1 | ⭐⭐⭐ |
| 실험 2 | Procedure 재사용률 | RQ5 | ⭐⭐ |
| 실험 3 | Selective Reasoning 빈도/비용 | RQ3 | ⭐⭐⭐ |
| 실험 4 | Selective Reasoning 복구 효과 | RQ4 | ⭐⭐ |
| 실험 5 | MCP Tool 유형별 적합성 | RQ2 | ⭐ |

**최소 실험 (Short Paper)**: 실험 1 + 실험 3

---

## 실험 환경

### MCP Servers

| Server | 유형 | 용도 |
|--------|------|------|
| `mcp__github` | API | 이슈/PR 생성 |
| `mcp__slack` | API | 메시지 전송 |
| `mcp__supabase` | API | DB 쿼리 |
| `mcp__chrome-devtools` | 브라우저 | 웹 자동화 |

### LLM

| 모델 | 용도 | 비용 기준 |
|------|------|----------|
| Claude 3.5 Sonnet | Record, Selective Reasoning | $3/1M input, $15/1M output |
| Claude 3 Haiku | 비용 비교용 (옵션) | $0.25/1M input, $1.25/1M output |

### 테스트 환경

| 환경 | 용도 |
|------|------|
| GitHub (실제) | API 호출 실험 |
| 자체 테스트 페이지 | 동적 요소 제어, 예외 상황 주입 |
| WebArena (옵션) | 벤치마크 비교 |

---

## 실험 1: 비용 절감 효과

### 목적

Sandy Procedure-level Replay가 얼마나 비용을 절감하는가?

### 가설

> Record 1회 비용을 N회 Play로 분산하면, N이 증가할수록 총 비용이 Pure LLM 대비 감소한다.

### 설정

```
Task: "GitHub 이슈 N개 생성"

비교 대상:
A) Pure LLM Agent - 매번 LLM이 판단하여 Tool 호출
B) Sandy Procedure - Record 1회 → Play N회
```

### 실험 변수

| 변수 | 값 |
|------|-----|
| N (반복 횟수) | 1, 5, 10, 20, 50 |
| Task 복잡도 | Simple (3 steps), Medium (5 steps), Complex (10 steps) |

### 측정 지표

| 지표 | 측정 방법 | 단위 |
|------|----------|------|
| Input 토큰 | API response `usage.input_tokens` | tokens |
| Output 토큰 | API response `usage.output_tokens` | tokens |
| 총 비용 | (input × $3 + output × $15) / 1M | $ |
| 실행 시간 | 시작~완료 timestamp 차이 | seconds |

### 데이터 수집

```python
@dataclass
class ExperimentResult:
    method: str          # "pure_llm" | "sandy"
    task: str            # "create_issue"
    n_iterations: int    # 1, 5, 10, 20, 50

    # 비용
    record_tokens: int   # Sandy만 (Record 시 토큰)
    play_tokens: int     # Sandy만 (Play 시 LLM Fallback 토큰, 보통 0)
    total_tokens: int    # Pure LLM: 전체, Sandy: record + play
    cost_usd: float

    # 시간
    total_time_sec: float
    avg_time_per_iteration: float

    # 성공률
    success_count: int
    failure_count: int
```

### 예상 결과

| N | Pure LLM 비용 | Sandy 비용 | 절감률 |
|---|--------------|-----------|--------|
| 1 | $0.05 | $0.05 (Record만) | 0% |
| 5 | $0.25 | $0.05 | 80% |
| 10 | $0.50 | $0.05 | 90% |
| 20 | $1.00 | $0.05 | 95% |
| 50 | $2.50 | $0.05 | 98% |

### 손익분기점 계산

```
Cost_Sandy = Cost_Record + Cost_LLM_Fallback × F
Cost_PureLLM = Cost_Per_Iteration × N

손익분기점: N = Cost_Record / Cost_Per_Iteration
예상: N ≈ 1~2 (Record 비용 ≈ 1~2회 실행 비용)
```

### 실험 절차

```
1. Pure LLM Agent로 Task 수행 (N=1, 5, 10, 20, 50)
   - 각 N에 대해 3회 반복 (평균 계산)
   - 토큰 수, 비용, 시간 기록

2. Sandy로 동일 Task 수행
   - Record 1회 수행, 토큰 기록
   - Play N회 수행 (N=1, 5, 10, 20, 50)
   - LLM Fallback 발생 시 토큰 기록

3. 결과 비교 및 그래프 생성
```

---

## 실험 2: Procedure 재사용률

### 목적

Procedure가 변형 Task에서 얼마나 재사용되는가?

### 가설

> Procedure-level 추상화는 Full Workflow 대비 높은 재사용률을 보인다.

### 설정

```
Base Procedures (미리 Record):
- github_login: GitHub 로그인
- create_issue: 이슈 생성
- create_pr: PR 생성
- slack_notify: Slack 알림
- supabase_query: DB 쿼리

Test Tasks:
T1: "GitHub 이슈 1개 생성"
T2: "GitHub 이슈 10개 생성"
T3: "GitHub 이슈 생성 후 Slack 알림"
T4: "GitHub PR 생성"
T5: "GitHub 이슈 생성 후 DB에 기록"
T6: "GitLab 이슈 생성" (유사 도메인, 새 Procedure 필요)
```

### 측정 지표

| 지표 | 정의 |
|------|------|
| 재사용률 | 기존 Procedure 사용 수 / 총 Procedure 수 |
| 신규 Record 필요 | 새로 Record해야 하는 Procedure 수 |
| LLM 조합 비용 | Procedure 선택/조합에 소모된 토큰 |

### 데이터 수집

```python
@dataclass
class ReuseResult:
    task: str
    procedures_used: list[str]      # 사용된 기존 Procedure
    procedures_new: list[str]       # 새로 Record 필요
    reuse_rate: float               # 재사용률
    llm_planning_tokens: int        # LLM이 조합에 사용한 토큰
```

### 예상 결과

| Task | 기존 Procedure | 신규 필요 | 재사용률 |
|------|---------------|----------|---------|
| T1 | github_login, create_issue | 0 | 100% |
| T2 | github_login, create_issue | 0 | 100% |
| T3 | github_login, create_issue, slack_notify | 0 | 100% |
| T4 | github_login, create_pr | 0 | 100% |
| T5 | github_login, create_issue, supabase_query | 0 | 100% |
| T6 | (없음) | gitlab_login, gitlab_create_issue | 0% |

### 비교: Full Workflow vs Procedure

| 방식 | T1 | T2 | T3 | T4 | T5 | T6 |
|------|-----|-----|-----|-----|-----|-----|
| Full Workflow | ✅ | ❌ 새로 필요 | ❌ 새로 필요 | ❌ 새로 필요 | ❌ 새로 필요 | ❌ 새로 필요 |
| Procedure | ✅ | ✅ 조합 | ✅ 조합 | ✅ 조합 | ✅ 조합 | ❌ 새로 필요 |

---

## 실험 3: Selective Reasoning 빈도/비용

### 목적

LLM Fallback이 얼마나 자주 발생하고, 비용은 얼마인가?

### 가설

> API 호출 시나리오에서는 LLM Fallback이 거의 발생하지 않고,
> 브라우저 자동화에서도 대부분 Level 1-2에서 해결된다.

### 설정

```
시나리오 유형:
A) API 호출만 - GitHub 이슈 생성 (10 steps)
B) 브라우저 정적 - 단순 폼 제출 (10 steps)
C) 브라우저 동적 - React SPA 조작 (10 steps)
D) 예외 상황 포함 - 의도적 실패 주입 (10 steps)
```

### 예외 상황 (D 시나리오)

| 상황 | 주입 방법 |
|------|----------|
| uid 변경 | 세션 재시작 후 Play |
| 새 필드 | 테스트 페이지에 필드 추가 |
| 팝업 | JavaScript alert 주입 |
| 세션 만료 | 쿠키 삭제 |

### 측정 지표

| 지표 | 정의 |
|------|------|
| Level 1 성공률 | Exact Match로 해결된 비율 |
| Level 2 성공률 | Simple Heuristic으로 해결된 비율 |
| Level 3 발생률 | LLM Fallback이 필요한 비율 |
| 평균 Fallback 토큰 | LLM Fallback 1회당 평균 토큰 |
| 총 Fallback 비용 | 시나리오당 LLM Fallback 총 비용 |

### 데이터 수집

```python
@dataclass
class StepResolution:
    step: int
    level: int              # 1, 2, or 3
    method: str             # "exact", "heuristic", "llm"
    tokens_used: int        # Level 3만
    time_ms: int

@dataclass
class ScenarioResult:
    scenario_type: str      # "api", "static", "dynamic", "exception"
    total_steps: int
    level1_count: int
    level2_count: int
    level3_count: int
    total_fallback_tokens: int
    total_fallback_cost: float
    step_resolutions: list[StepResolution]
```

### 예상 결과

| 시나리오 | 총 Step | L1 | L2 | L3 | L3 비율 | Fallback 비용 |
|----------|---------|-----|-----|-----|---------|--------------|
| A (API) | 10 | 10 | 0 | 0 | 0% | $0 |
| B (정적) | 10 | 8 | 1 | 1 | 10% | $0.01 |
| C (동적) | 10 | 5 | 2 | 3 | 30% | $0.03 |
| D (예외) | 10 | 3 | 2 | 5 | 50% | $0.05 |

### 핵심 인사이트

> API 호출 위주 시나리오에서 Selective Reasoning 비용은 거의 0에 가깝다.
> → Procedure-level Replay의 비용 절감 효과가 그대로 유지됨.

---

## 실험 4: Selective Reasoning 복구 효과

### 목적

LLM Fallback이 실패를 얼마나 복구하는가? 특히 사용자 상호작용이 필요한 경우는?

### 가설

> LLM Fallback은 대부분의 동적 요소 문제를 자동 복구하고,
> 사용자 입력이 필요한 경우에도 적절히 질문하여 해결한다.

### 설정

```
의도적 실패 상황 주입 (각 10회):

F1: uid 변경 - 세션 재시작으로 uid 변경
F2: DOM 구조 변경 - 테스트 페이지 구조 수정
F3: 새 필수 필드 - 폼에 새 필드 추가
F4: 예상치 못한 팝업 - alert/confirm 주입
F5: 로그인 세션 만료 - 쿠키 삭제
F6: 네트워크 에러 - 일시적 연결 실패
```

### 측정 지표

| 지표 | 정의 |
|------|------|
| 자동 복구율 | LLM이 혼자 해결한 비율 |
| 사용자 협력 복구율 | 사용자 입력으로 해결한 비율 |
| 총 복구율 | 자동 + 사용자 협력 |
| 복구 불가율 | 해결 못한 비율 |
| 평균 복구 토큰 | 복구 1건당 평균 토큰 |

### 데이터 수집

```python
@dataclass
class RecoveryResult:
    failure_type: str       # "uid_change", "new_field", etc.
    total_count: int
    auto_recovered: int     # LLM이 혼자 해결
    user_assisted: int      # 사용자 입력으로 해결
    unrecoverable: int      # 해결 못함
    avg_tokens: float
    avg_time_sec: float

    @property
    def auto_rate(self) -> float:
        return self.auto_recovered / self.total_count

    @property
    def total_recovery_rate(self) -> float:
        return (self.auto_recovered + self.user_assisted) / self.total_count
```

### 예상 결과

| 실패 유형 | 발생 | 자동 복구 | 사용자 협력 | 복구 불가 | 총 복구율 |
|----------|------|----------|-----------|----------|----------|
| F1: uid 변경 | 10 | 9 | 0 | 1 | 90% |
| F2: DOM 변경 | 10 | 7 | 2 | 1 | 90% |
| F3: 새 필드 | 10 | 0 | 10 | 0 | 100% |
| F4: 팝업 | 10 | 8 | 2 | 0 | 100% |
| F5: 세션 만료 | 10 | 0 | 10 | 0 | 100% |
| F6: 네트워크 에러 | 10 | 10 | 0 | 0 | 100% |
| **평균** | - | 57% | 40% | 3% | **97%** |

### 사용자 질문 유형 분석

| 상황 | LLM이 하는 질문 예시 |
|------|---------------------|
| 새 필드 | "회사명을 입력해주세요" |
| 세션 만료 | "다시 로그인이 필요합니다. 비밀번호를 입력해주세요" |
| 선택 필요 | "다음 중 어떤 옵션을 선택할까요? 1) A 2) B" |
| 확인 필요 | "이 작업을 계속 진행할까요?" |

---

## 실험 5: MCP Tool 유형별 적합성

### 목적

어떤 MCP Tool 유형이 Replay에 가장 적합한가?

### 설정

```
Tool 유형:
- API: GitHub, Slack, Notion
- Database: Supabase, PostgreSQL
- File System: 파일 읽기/쓰기
- Browser: chrome-devtools
```

### 측정 지표

| 지표 | 정의 |
|------|------|
| 재생 성공률 | Play 성공 비율 |
| LLM 개입 필요율 | Selective Reasoning 발생 비율 |
| 평균 실행 시간 | Step당 평균 시간 |

### 예상 결과

| Tool 유형 | 재생 성공률 | LLM 개입 필요 | 적합성 |
|----------|-----------|--------------|--------|
| API | 99% | 1% | ⭐⭐⭐ 높음 |
| Database | 98% | 2% | ⭐⭐⭐ 높음 |
| File System | 95% | 5% | ⭐⭐ 중간 |
| Browser | 80% | 20% | ⭐ 낮음 |

---

## 실험 일정

### AIWILD 제출용 (최소)

| 일정 | 실험 | 산출물 |
|------|------|--------|
| Day 1 | 실험 1 (비용 절감) | 비용 비교 그래프 |
| Day 2 | 실험 3 (LLM 개입 빈도) | 시나리오별 개입률 테이블 |
| Day 3 | 결과 정리 | 논문 Evaluation 섹션 |

### AIware 제출용 (확장)

| 일정 | 실험 | 산출물 |
|------|------|--------|
| Week 1 | 실험 1, 3 | 핵심 결과 |
| Week 2 | 실험 2, 4 | 재사용률, 복구율 |
| Week 3 | 실험 5 | Tool 유형별 분석 |
| Week 4 | 결과 정리 | 논문 완성 |

---

## 결과 시각화

### Figure 1: 비용 비교 (실험 1)

```
비용 ($)
    │
 2.5├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ Pure LLM ─────●
    │                                      ／
 2.0├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─／─ ─ ─
    │                              ／
 1.5├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─／─ ─ ─ ─ ─ ─ ─
    │                      ／
 1.0├─ ─ ─ ─ ─ ─ ─ ─ ─ ／─ ─ ─ ─ ─ ─ ─ ─ ─ ─
    │              ／
 0.5├─ ─ ─ ─ ─ ／─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
    │      ／
 0.05├─●══════════════════════════════════════ Sandy
    │
   0├─────┬─────┬─────┬─────┬─────────────►
         5    10    20    30    50   반복 횟수
```

### Figure 2: Selective Reasoning 발생률 (실험 3)

```
LLM 개입률 (%)
    │
 50├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ■ 예외상황
    │
 40├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
    │
 30├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ■ 동적 브라우저
    │
 20├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
    │
 10├─ ─ ─ ─ ─ ■ 정적 브라우저
    │
  0├─■─────────────────────────────────────►
    API    정적     동적     예외    시나리오 유형
```

### Table 1: Selective Reasoning 복구율 (실험 4)

| 실패 유형 | 자동 복구 | 사용자 협력 | 복구 불가 |
|----------|:---------:|:----------:|:---------:|
| uid 변경 | 90% | 0% | 10% |
| 새 필드 | 0% | 100% | 0% |
| 팝업 | 80% | 20% | 0% |
| 세션 만료 | 0% | 100% | 0% |
| **평균** | **57%** | **40%** | **3%** |

---

## 재현성

### 코드 공개

```
sandy-benchmark/
├── experiments/
│   ├── exp1_cost/
│   │   ├── run.py
│   │   └── results/
│   ├── exp2_reuse/
│   ├── exp3_frequency/
│   └── exp4_recovery/
├── procedures/
│   └── *.json
├── scenarios/
│   └── *.json
└── README.md
```

### 환경 재현

```bash
# 환경 설정
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export GITHUB_TOKEN=...

# 실험 실행
python experiments/exp1_cost/run.py --iterations 1,5,10,20,50
python experiments/exp3_frequency/run.py --scenarios api,static,dynamic,exception
```

---

*Last updated: 2026-02-03*
