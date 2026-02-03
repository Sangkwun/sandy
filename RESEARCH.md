# Sandy 연구 계획

> Sandy: Accelerating LLM Agents via Deterministic Replay and Selective Reasoning

---

## 연구 개요

### 핵심 아이디어

MCP Tool 호출을 Record/Play하여 LLM Agent의 비용과 지연을 줄이는 프레임워크.

```
기존 LLM Agent:    매번 LLM 호출 → 비용 누적, 지연 발생
Sandy:             Record 1회 → Play N회 (LLM 없이, 비용 0원)
```

### 연구 질문

| RQ | 질문 |
|----|------|
| RQ1 | MCP Tool 호출의 Deterministic Replay가 얼마나 비용/시간을 절감하는가? |
| RQ2 | 어떤 유형의 작업이 Replay에 적합하고, 어떤 유형이 실패하는가? |
| RQ3 | Selective Reasoning(LLM Fallback)이 얼마나 자주 발생하고 비용은 얼마인가? |
| RQ4 | Selective Reasoning이 예측 불가능한 상황(사용자 입력 필요 등)을 얼마나 처리하는가? |
| RQ5 | Procedure-level Replay가 전체 워크플로우 대비 얼마나 유연성과 재사용성을 높이는가? |

---

## 관련 연구

### 1. Record & Replay for LLM Agents

#### AgentRR (arXiv:2505.17716, 2025.05)

> "Get Experience from Practice: LLM Agents with Record & Replay"

| 항목 | AgentRR | Sandy |
|------|---------|-------|
| 핵심 아이디어 | Record & Replay | Record & Play |
| MCP 통합 | 언급만 | **MCP 네이티브** |
| 구현 | 개념 증명 | **실용 도구** |
| 정량 평가 | **없음** | 계획 중 |
| 동적 요소 대응 | 한계 인정만 | **다중 선택자 전략** |
| 오픈소스 | 없음 | **공개 예정** |

**AgentRR의 한계 (논문에서 인정):**
- 요약 복잡성: 경험 수준 정의 불명확
- 상태 공간: 다양한 작업에서 상태 정의 어려움
- 기록 신뢰성: 동적 HTML 등으로 100% 재현 불가능
- **정량적 평가 없음**

---

### 2. LLM Agent Efficiency & Cost Reduction

| 논문 | 핵심 내용 | Sandy 관련성 |
|------|----------|-------------|
| [AgentDiet](https://arxiv.org/abs/2509.23586) (2025.09) | Trajectory 압축으로 토큰 39.9%~59.7% 절감 | Sandy는 Replay로 토큰 100% 절감 |
| [Efficient Agents](https://arxiv.org/abs/2508.02694) (2025.08) | 비용 인식 Agent 평가 프레임워크 | Sandy 평가 지표 참고 |
| [Less is More](https://arxiv.org/abs/2411.15399) (2024.11) | Tool 수 축소로 성능/효율 개선 | Tool 선택 최적화 아이디어 |
| [CoRL](https://arxiv.org/abs/2511.02755) (2025.11) | RL로 성능-비용 트레이드오프 최적화 | Selective Reasoning 비용 제어 |
| [Natural Language Tools](https://arxiv.org/abs/2510.14453) (2025.10) | 구조화 출력이 정확도 20% 감소 | MCP Tool 호출 포맷 영향 |

---

### 3. MCP (Model Context Protocol) 관련

| 논문 | 주제 | 링크 |
|------|------|------|
| MCP Landscape & Security | MCP 아키텍처, 보안 분석 | [arXiv:2503.23278](https://arxiv.org/abs/2503.23278) |
| Breaking the Protocol | MCP 프로토콜 취약점 분석 | [arXiv:2601.17549](https://arxiv.org/abs/2601.17549) |
| MCP Security Bench | 2,000개 공격 시나리오 평가 | [arXiv:2510.15994](https://arxiv.org/abs/2510.15994) |
| MCP-Bench | Tool-Using Agent 벤치마크 | [arXiv:2508.20453](https://arxiv.org/abs/2508.20453) |
| MCP-Universe | 231 tasks, 11 MCP servers | [arXiv:2508.14704](https://arxiv.org/abs/2508.14704) |
| ScaleMCP | 동적 MCP Tool 동기화 | [arXiv:2505.06416](https://arxiv.org/abs/2505.06416) |
| MCP Performance | 토큰 사용량 증가 분석 | [arXiv:2511.07426](https://arxiv.org/abs/2511.07426) |

---

### 4. Web Automation & RPA with AI/ML

| 논문 | 핵심 내용 | Sandy 관련성 |
|------|----------|-------------|
| [SmartFlow](https://arxiv.org/abs/2405.12842) (2024.05) | LLM 기반 RPA, UI 변화 자동 적응 | 동적 요소 대응 참고 |
| [WebRobot](https://arxiv.org/abs/2203.09993) (2022.03) | PBD 기반 Web RPA 합성 | Record 방식 비교 |
| [PromptRPA](https://arxiv.org/abs/2404.02475) (2024.04) | 텍스트 프롬프트로 모바일 RPA 생성 | 프롬프트 기반 생성 참고 |
| [ML in RPA Taxonomy](https://arxiv.org/abs/2509.15730) (2025.09) | 지능형 RPA에서 ML 역할 분류 | 학술적 포지셔닝 |
| [RPA + Process Mining](https://arxiv.org/abs/2204.00751) (2022.04) | 이벤트 기록 및 루틴 발견 | Record 메커니즘 비교 |
| [LLM vs RPA](https://arxiv.org/abs/2509.04198) (2025.09) | 기업 워크플로우 비교 | 하이브리드 접근 근거 |

---

### 5. Web Element Localization & Self-Healing

| 논문 | 핵심 내용 | Sandy 관련성 |
|------|----------|-------------|
| [Web Element Relocalization](https://arxiv.org/abs/2505.16424) (2025.05) | VON Similo로 96~99% 복구율 | 규칙 기반 비교 대상 |
| [Similo (TOSEM)](https://dl.acm.org/doi/10.1145/3571855) (2023) | 원본 Similo 알고리즘, 89% 성공률 | 규칙 기반 비교 대상 |
| [Healenium](https://github.com/healenium/healenium-web) | LCS + ML 기반 self-healing | 오픈소스 참고 |

**Sandy의 차별화된 접근:**

| 항목 | Similo (규칙 기반) | Sandy (LLM Fallback) |
|------|-------------------|---------------------|
| 구현 복잡도 | 높음 | **낮음** |
| 대응 범위 | 요소 찾기만 | **무제한** |
| 사용자 상호작용 | ❌ | **⭕** |
| 새로운 상황 대응 | ❌ | **⭕** |
| 비용 | 0 | 토큰 소모 (필요시만) |

→ Sandy는 규칙 기반 복잡성 대신 **LLM을 범용 Fallback으로 활용**하여 구현 단순화 + 대응 범위 확대

---

### 6. Semantic Caching for LLMs

| 논문 | 핵심 내용 | Sandy 관련성 |
|------|----------|-------------|
| [Semantic Cache Eviction](https://arxiv.org/abs/2508.07675) (2025.08) | 시맨틱 캐시 eviction 최적화 | 시나리오 캐싱 아이디어 |
| [GPT Semantic Cache](https://arxiv.org/abs/2411.05276) (2024.11) | API 호출 68.8% 감소, 97% 정확도 | 유사 쿼리 재사용 참고 |
| [MeanCache](https://arxiv.org/abs/2403.02694) (2024.03) | 반복 쿼리 31%, F-score 17% 개선 | 사용자 측 캐시 참고 |
| [ToolCaching](https://arxiv.org/abs/2601.15335) (2025.01) | Tool calling 요청 캐싱 | **직접 관련 논문** |

**ToolCaching과 Sandy 비교:**
- ToolCaching: 의미적 유사성 기반 캐싱 (동적)
- Sandy: 동일 시나리오 완전 재현 (결정적)

---

### 7. Browser Automation Agents & Benchmarks

| 논문 | 핵심 내용 | Sandy 관련성 |
|------|----------|-------------|
| [WebArena](https://arxiv.org/abs/2307.13854) (2023.07) | 812 tasks, 4개 도메인 벤치마크 | 웹 자동화 벤치마크 표준 |
| [VisualWebArena](https://arxiv.org/abs/2401.13649) (2024.01) | 910 시각 기반 tasks | Visual matching 참고 |
| [WebVoyager](https://arxiv.org/abs/2401.13919) (2024.01) | 멀티모달 웹 에이전트, 59.1% 성공률 | Agent 성능 비교 기준 |
| [SeeAct](https://osu-nlp-group.github.io/SeeAct/) (EMNLP 2024) | 비전 기반 웹 에이전트 | 스크린샷 기반 매칭 참고 |
| [WALT](https://arxiv.org/abs/2510.01524) (2025.10) | Tool 학습 웹 에이전트, 52.9% SOTA | 최신 성능 비교 |
| [GUI Agents Survey](https://arxiv.org/abs/2411.18279) (2024.11) | LLM 기반 GUI Agent 서베이 | 전체 분야 이해 |
| [WebArXiv](https://arxiv.org/abs/2507.00938) (2025.07) | 시간 불변 arXiv 작업 평가 | 결정적 환경 참고 |

---

### 8. Experience Replay & Memory for LLM Agents

| 논문 | 핵심 내용 | Sandy 관련성 |
|------|----------|-------------|
| [CER](https://arxiv.org/abs/2506.06698) (2025.06) | Contextual Experience Replay, 동적 메모리 버퍼 | 경험 재사용 |
| [RLEP](https://arxiv.org/abs/2507.07451) (2025.07) | RL + Experience Replay, trajectory 재사용 | Replay 학습 |
| [Memento](https://arxiv.org/abs/2508.16153) (2025.08) | Case Bank에 trajectory 저장, 에피소드 메모리 | **유사 접근** |
| [WebATLAS](https://arxiv.org/abs/2510.22732) (2025.10) | Experience-Driven Memory, 시뮬레이션 | 메모리 기반 |
| [DreamGym](https://arxiv.org/abs/2511.03773) (2025.11) | Experience Replay Buffer, 합성 경험 | 경험 합성 |
| [P2 Experience Replay](https://arxiv.org/abs/2410.12236) (2024.10) | 우선순위 기반 경험 재사용 | 코드 생성 |

**Sandy vs Experience Replay 접근:**
- Experience Replay: 과거 경험을 **학습**에 활용
- Sandy: 과거 경험을 **그대로 재실행** (결정적)

**Sandy Procedures vs Memento:**

| 항목 | Memento | Sandy Procedures |
|------|---------|------------------|
| 저장 단위 | 전체 trajectory | **Procedure (중간 단위)** |
| 매칭 방식 | 유사 케이스 검색 | **정확한 procedure 호출** |
| LLM 역할 | 항상 실행에 참여 | **조합/계획만 담당** |
| 실행 방식 | LLM이 참고하며 실행 | **결정적 replay** |
| 재사용성 | 유사 task | **동일 procedure 호출 시 100%** |

---

### 9. Workflow Generation & Automation

| 논문 | 핵심 내용 | Sandy 관련성 |
|------|----------|-------------|
| [WorkflowLLM](https://arxiv.org/abs/2411.05451) (2024.11) | 106K 샘플, 1,503 APIs | 워크플로우 벤치마크 |
| [AutoFlow](https://arxiv.org/abs/2407.12821) (2024.07) | RL로 워크플로우 자동 생성 | 워크플로우 합성 |
| [FlowMind](https://arxiv.org/abs/2404.13050) (2024.04) | LLM으로 RPA 워크플로우 생성 | RPA 연계 |
| [Blueprint First](https://arxiv.org/abs/2508.02721) (2025.08) | 결정적 워크플로우 실행 | **결정성 강조** |
| [AutoDroid](https://arxiv.org/abs/2308.15272) (2023.08) | Android 작업 자동화 | 모바일 자동화 |
| [MobileGPT](https://arxiv.org/abs/2312.03003) (2023.12) | 앱 메모리 기반 모바일 자동화 | 메모리 활용 |

**Blueprint First 핵심 인사이트:**
> "LLM의 CoT는 비결정적. 외부 액션 시퀀스가 예측 가능하고 보장되어야 하는
> 응용에는 **결정적 실행 워크플로우**가 필요하다."

→ Sandy의 Play 모드가 정확히 이 문제를 해결

---

### 10. API Call Sequence & Tool Use

| 논문 | 핵심 내용 | Sandy 관련성 |
|------|----------|-------------|
| [NESTful](https://arxiv.org/abs/2409.03797) (2024.09) | 중첩 API 호출 벤치마크, 1800+ 시퀀스 | API 시퀀스 평가 |
| [StateGen](https://arxiv.org/abs/2507.09481) (2025.07) | 순차 API 호출 테스트 생성 | API 상호작용 |
| [ToolACE](https://arxiv.org/abs/2409.00920) (ICLR 2025) | Tool 자기진화 합성 | Tool 다양성 |
| [T-Eval](https://arxiv.org/abs/2507.21504) (2025.07) | Agent 벤치마크 서베이 | 평가 프레임워크 |

---

### 11. 기타 관련 연구

| 논문 | 주제 | 링크 |
|------|------|------|
| Cost-of-Pass | 경제적 LLM 평가 프레임워크 | [arXiv:2504.13359](https://arxiv.org/abs/2504.13359) |
| TinyAgent | 엣지 디바이스 Function calling | [arXiv:2409.00608](https://arxiv.org/abs/2409.00608) |
| Agent.xpu | SoC에서 Agent 스케줄링 | [arXiv:2506.24045](https://arxiv.org/abs/2506.24045) |
| Privacy in Action | MCP Agent 프라이버시 | [arXiv:2509.17488](https://arxiv.org/abs/2509.17488) |
| In-Context Learning Agents | 데모 선택으로 성능 향상 | [arXiv:2506.13109](https://arxiv.org/abs/2506.13109) |

---

## Sandy의 기여점

### 핵심 연구 질문

> **LLM Agent에서 결정적 실행과 LLM 추론의 최적 균형점은 어디인가?**

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  100% 결정적          Sandy           100% LLM     │
│  (비용 0, 유연성 0)    (균형)      (비용 높음, 유연)  │
│       │                 │                │          │
│       ▼                 ▼                ▼          │
│  ════════════════════════════════════════════       │
│                         ▲                           │
│                    최적 지점                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### 1. Procedure-level Replay (핵심 기여 ⭐)

재사용 단위 스펙트럼에서 **최적 균형점**을 제시.

**기존 접근법의 한계:**

| 접근법 | 재사용 단위 | 한계 |
|--------|------------|------|
| AgentRR | 전체 워크플로우 | 유연성 부족, 조합 불가 |
| ToolCaching | 개별 API 호출 | 컨텍스트 손실, 시퀀스 무시 |
| Memento | 유사 케이스 참조 | LLM 항상 필요 |

**Sandy Procedure Library:**

```
┌─────────────────────────────────────────────────────────┐
│              Procedure-level Replay                     │
│                                                         │
│   Workflow (전체)  ←─────── 기존 AgentRR               │
│        │                                                │
│        ├── Procedure (중간) ←─── Sandy Procedures      │
│        │      ├── login_github                         │
│        │      ├── create_issue                         │
│        │      └── upload_file                          │
│        │                                                │
│        └── API Call (개별) ←─── ToolCaching            │
│                                                         │
│   LLM이 Procedure를 Tool처럼 선택/조합                 │
└─────────────────────────────────────────────────────────┘
```

**핵심 차별점:**
- 워크플로우보다 **유연** (LLM이 선택/조합)
- API 호출보다 **효율적** (시퀀스 단위 재사용)
- 비용과 유연성의 **최적 균형점**

**역할 분리:**
- **LLM**: Procedure 선택, 조합, 계획 (비용 발생)
- **Sandy**: Procedure 실행 (비용 0)

### 종합 비교표

| 항목 | AgentRR | Memento | ToolCaching | **Sandy** |
|------|---------|---------|-------------|-----------|
| **재사용 단위** | 전체 workflow | 유사 케이스 | 개별 API | **Procedure** |
| **매칭 방식** | 동일 task | 유사도 검색 | 의미적 유사성 | **명시적 호출** |
| **LLM 역할** | replay 안내 | 항상 참여 | 캐시 미스 시 | **조합만** |
| **실행 결정성** | 비결정적 | 비결정적 | 비결정적 | **결정적** |
| **유연성** | 낮음 | 높음 | 높음 | **중간** |
| **비용 절감** | 중간 | 낮음 | 중간 | **높음** |
| **동적 요소 대응** | 한계 인정 | LLM 의존 | N/A | **Fallback 전략** |
| **MCP 네이티브** | ❌ | ❌ | ❌ | **✅** |
| **정량 평가** | ❌ | ✅ | ✅ | **✅ (계획)** |

### 2. Selective Reasoning (핵심 기여 ⭐)

**실패 시 LLM이 개입하는 범용적 Fallback 전략.**

기존 접근법(Similo 등 규칙 기반)의 한계:
- 요소 재탐색만 가능
- 새로운 상황 대응 불가
- 사용자 상호작용 불가

**LLM Fallback의 장점:**

| Similo (규칙 기반) | LLM Fallback |
|-------------------|--------------|
| 요소 찾기만 | **무제한** |
| 새로운 상황 ❌ | 새로운 상황 ⭕ |
| 사용자 질문 ❌ | 사용자 질문 ⭕ |
| 비용 0 | 토큰 소모 |

**LLM Fallback이 처리 가능한 상황:**

```
├── 동적 요소 재탐색 (uid 변경)
├── 사용자에게 질문 ("어떤 옵션을 선택할까요?")
├── 예상치 못한 팝업/CAPTCHA 처리
├── 로그인 세션 만료 대응
├── A/B 테스트로 UI가 다른 경우
├── 에러 메시지 해석 및 복구
└── 기타 예측 불가능한 상황
```

**간소화된 Fallback 전략:**

```
Level 1: 정확 매칭 (uid, 비용 0)
    ↓ 실패
Level 2: 간단한 휴리스틱 (text, aria-label, 비용 0)
    ↓ 실패
Level 3: LLM Fallback (범용, 비용 발생)
         ├── 요소 찾기
         ├── 사용자 질문
         ├── 상황 판단
         └── 복구 시도
```

**핵심 인사이트:**

> Similo 같은 규칙 기반 접근 대신, **LLM을 범용 Fallback으로 활용**하면
> 구현 복잡도는 낮추면서 대응 범위는 무한대로 확장 가능.

**측정 가능한 지표:**

| 지표 | 설명 |
|------|------|
| LLM 개입률 | 전체 step 중 LLM이 필요한 비율 |
| 개입당 비용 | LLM fallback 1회당 토큰 소모 |
| 복구 성공률 | LLM 개입으로 복구된 실패 비율 |
| 총 비용 | Play 비용 + LLM Fallback 비용 |

### 3. MCP 네이티브 구현

AgentRR은 MCP를 "언급"만, Sandy는 MCP 기반으로 설계.

```
Sandy 차별점:
- MCP Tool 이름 파싱 (mcp__server__tool)
- Transport 자동 선택 (SSE/WebSocket/stdio)
- 기존 MCP Server 재사용 (세션 공유)
- Config 자동 감지 (Claude Desktop, Cursor 등)
```

### 4. 정량적 평가 (AgentRR이 안 한 것)

| 실험 | 측정 항목 |
|------|----------|
| 비용 비교 | Record 1회 비용 vs Agent N회 비용, 손익분기점 |
| 속도 비교 | LLM Agent vs Sandy Play 실행 시간 |
| 성공률 | 작업 유형별 Play 성공률 |
| LLM 개입 | Selective Reasoning 빈도 및 비용 |

**비용 모델 공식화:**

```
Cost_Total = Cost_Record + Cost_Play × N + Cost_LLM_Fallback × F

여기서:
- Cost_Record: 1회 녹화 비용 (LLM 토큰)
- Cost_Play: 재생 비용 (0원)
- N: 재생 횟수
- Cost_LLM_Fallback: LLM 개입 1회 비용
- F: LLM 개입 횟수

손익분기점: N > Cost_Record / (Cost_Agent - Cost_LLM_Fallback × (F/N))
```

### 5. 오픈소스 + 벤치마크 데이터셋

재현 가능한 연구를 위한 도구와 데이터 공개.

---

## Procedure Library 설계

### 개념

```
User: "GitHub에 로그인해서 버그 이슈 만들고 Slack에 알려줘"

┌──────────────────────────────────────────────────────┐
│ LLM (계획/선택):                                      │
│   "github_login, create_issue, slack_notify 쓰자"    │
│                                                      │
│ 실행:                                                │
│   1. sandy.play("github_login")  ← Sandy (비용 0)   │
│   2. sandy.play("create_issue")  ← Sandy (비용 0)   │
│   3. sandy.play("slack_notify")  ← Sandy (비용 0)   │
│                                                      │
│ LLM (종합):                                          │
│   4. 결과 종합 보고               ← LLM (비용 발생)  │
└──────────────────────────────────────────────────────┘

총 비용: LLM 계획 + 종합만 (Procedure 실행은 0원)
```

### Procedure 포맷

```json
{
  "version": "2.2",
  "type": "procedure",
  "name": "github_login",
  "description": "GitHub 계정으로 로그인 수행",
  "tags": ["auth", "github", "web"],

  "inputs": {
    "USERNAME": { "type": "string", "required": true },
    "PASSWORD": { "type": "string", "required": true, "sensitive": true }
  },

  "outputs": {
    "logged_in": { "type": "boolean" },
    "user_profile": { "type": "string", "extract": "$.username" }
  },

  "preconditions": [
    { "check": "url_contains", "value": "github.com" },
    { "check": "element_not_exists", "selector": ".user-avatar" }
  ],

  "postconditions": [
    { "check": "element_exists", "selector": ".user-avatar" }
  ],

  "steps": [
    {
      "step": 1,
      "tool": "mcp__chrome-devtools__navigate_page",
      "params": { "url": "https://github.com/login" }
    },
    {
      "step": 2,
      "tool": "mcp__chrome-devtools__fill",
      "params": { "uid": "login_field", "value": "{{USERNAME}}" },
      "selectors": { ... }
    },
    {
      "step": 3,
      "tool": "mcp__chrome-devtools__fill",
      "params": { "uid": "password", "value": "{{PASSWORD}}" },
      "selectors": { ... }
    },
    {
      "step": 4,
      "tool": "mcp__chrome-devtools__click",
      "params": { "uid": "sign_in_button" },
      "selectors": { ... }
    }
  ]
}
```

### Procedure Library 구조

```
procedures/
├── auth/
│   ├── github_login.json
│   ├── google_oauth.json
│   └── slack_login.json
├── github/
│   ├── create_issue.json
│   ├── create_pr.json
│   └── merge_pr.json
├── slack/
│   ├── send_message.json
│   └── upload_file.json
└── common/
    ├── file_upload.json
    └── form_submit.json
```

### LLM 통합 인터페이스

```python
class ProcedureLibrary:
    """LLM이 Tool처럼 사용할 수 있는 Procedure 라이브러리"""

    def __init__(self, procedures_dir: str):
        self.procedures = self._load_procedures(procedures_dir)

    def list_procedures(self) -> list[ProcedureInfo]:
        """LLM에게 사용 가능한 procedure 목록 제공"""
        return [
            {
                "name": p.name,
                "description": p.description,
                "inputs": p.inputs,
                "outputs": p.outputs,
                "tags": p.tags
            }
            for p in self.procedures.values()
        ]

    def get_procedure_schema(self, name: str) -> dict:
        """MCP Tool 형식으로 procedure 스키마 반환"""
        p = self.procedures[name]
        return {
            "name": f"sandy_procedure_{name}",
            "description": p.description,
            "inputSchema": {
                "type": "object",
                "properties": p.inputs,
                "required": [k for k, v in p.inputs.items() if v.get("required")]
            }
        }

    async def play(self, name: str, variables: dict) -> PlayResult:
        """특정 procedure 실행"""
        procedure = self.procedures[name]

        # Precondition 검사
        if not await self._check_preconditions(procedure):
            return PlayResult(success=False, error="Preconditions not met")

        # 실행
        result = await self.executor.play(procedure, variables)

        # Postcondition 검사
        if result.success and not await self._check_postconditions(procedure):
            return PlayResult(success=False, error="Postconditions not met")

        return result

    def search_procedures(self, query: str) -> list[ProcedureInfo]:
        """자연어로 procedure 검색 (LLM 지원용)"""
        # 태그, 설명, 이름 기반 검색
        ...
```

### LLM Prompt에 Procedure 노출

```python
def generate_system_prompt(library: ProcedureLibrary) -> str:
    """LLM 시스템 프롬프트에 Procedure 목록 포함"""
    procedures = library.list_procedures()

    return f"""
You have access to the following pre-recorded procedures that can be executed
without LLM cost. Use these whenever possible instead of performing actions step-by-step.

## Available Procedures

{format_procedures_as_tools(procedures)}

## Usage

To execute a procedure, call:
- sandy.play("procedure_name", {{"INPUT_VAR": "value"}})

The procedure will execute deterministically and return the result.
Only use LLM reasoning when:
1. No matching procedure exists
2. A procedure fails and needs recovery
3. Combining multiple procedure results
"""
```

### Sandy Play API

```python
# 기본 실행 (전체)
sandy.play("github_login", variables={"USERNAME": "...", "PASSWORD": "..."})

# 시작/종료 지점 지정
sandy.play("github_login", start=3)           # step 3부터 끝까지
sandy.play("github_login", end=2)             # step 1~2만
sandy.play("github_login", start=2, end=4)    # step 2~4만

# 실패 후 재시작
sandy.play("github_login", start=3)           # 실패 지점부터 재개
```

### 반환값

```python
@dataclass
class StepResult:
    step: int
    tool: str                      # "mcp__github__create_issue"
    params: dict                   # 실제 호출한 파라미터
    success: bool
    result: Any | None = None      # MCP 원본 결과 (옵션)
    error: str | None = None

@dataclass
class PlayResult:
    success: bool
    completed_steps: list[int]     # 완료된 step 번호
    failed_step: int | None        # 실패한 step (없으면 None)
    error: str | None              # 에러 메시지
    outputs: dict                  # JSONPath로 추출된 값 (항상 포함)
    step_results: list[StepResult] # 각 step 정보
    context: dict | None           # 디버깅 정보
```

### include_results 옵션

```python
# 기본 (토큰 절약): outputs만 포함, MCP 결과 없음
result = play("scenario.json")
result.outputs          # {"issue_number": 123} ← 항상 있음
result.step_results[0].result  # None ← 생략됨

# 전체 포함: MCP 원본 결과 포함
result = play("scenario.json", include_results=True)
result.step_results[0].result  # {...전체 GitHub API 응답...}

# 실패 시만 포함: 디버깅용
result = play("scenario.json", include_results="on_failure")
# 성공 시: result = None
# 실패 시: result + context 포함
```

### 사용 예시

```python
# 일반 사용 (토큰 절약)
result = play("create_issue.json")
print(result.outputs["issue_number"])  # 123

# 상세 정보 필요 시
result = play("create_issue.json", include_results=True)
full_response = result.step_results[0].result
print(full_response["created_at"])  # "2026-02-03T..."

# 디버깅 시
result = play("create_issue.json", include_results="on_failure")
if not result.success:
    print(result.context)  # 페이지 상태 등
```
```

### LLM 연동 흐름

```
┌─────────────────────────────────────────────────────────┐
│  LLM (Claude Code 등)이 직접 sandy.play() 호출          │
│                                                         │
│  1. sandy.play("github_login")                          │
│     └─→ 실패: step 3에서 "Element not found"            │
│                                                         │
│  2. LLM 판단: "selector 문제네, 내가 직접 해볼게"       │
│     └─→ mcp__chrome-devtools__fill(...) 직접 호출      │
│                                                         │
│  3. sandy.play("github_login", start=4)                 │
│     └─→ 성공: step 4 완료                               │
│                                                         │
│  4. sandy.play("create_issue", variables={...})         │
│     └─→ 성공                                            │
└─────────────────────────────────────────────────────────┘
```

### 부분 실행 활용 예시

```
Procedure: github_login (steps 1-4)
  step 1: navigate to github.com/login
  step 2: fill username
  step 3: fill password
  step 4: click submit

활용:
┌────────────────────────────────────────────────────────┐
│ Case 1: 이미 로그인 페이지에 있음                       │
│   → sandy.play("github_login", start=2)                │
│                                                        │
│ Case 2: 비밀번호만 다시 입력                            │
│   → sandy.play("github_login", start=3, end=3)         │
│                                                        │
│ Case 3: step 3 실패 후 LLM이 직접 처리하고 계속         │
│   → sandy.play("github_login", start=4)                │
│                                                        │
│ Case 4: 네비게이션만 재사용                             │
│   → sandy.play("github_login", end=1)                  │
└────────────────────────────────────────────────────────┘
```

**핵심:**
- LLM이 **호출자** (별도 orchestration 불필요)
- Sandy는 **시작/종료 지점** 받아서 실행
- 실패 시 **상세 정보 반환** → LLM이 판단

### 비용 분석

```
시나리오: "GitHub 이슈 10개 생성하고 Slack에 알림"

순수 LLM Agent:
  - 이슈당 ~5 API 호출 × 10 = 50회 LLM 판단
  - 비용: $$$

Sandy (전체 워크플로우):
  - Record 1회 → Play 불가 (이슈 내용이 다름)
  - 비용: $$$ (매번 새로 실행)

Sandy Procedures:
  - create_issue procedure × 10 (비용 0)
  - LLM: 계획 1회 + 종합 1회
  - 비용: $ (95% 이상 절감)
```

---

## Selective Reasoning 전략

### 문제 정의

```
Record 시점:                    Play 시점:
┌─────────────────────┐        ┌─────────────────────┐
│ <button uid="abc123">│   →    │ <button uid="xyz789">│
│   로그인             │        │   로그인             │
│ </button>           │        │ </button>           │
└─────────────────────┘        └─────────────────────┘

uid가 달라짐 → 기존 방식은 실패
```

### 기존 접근법의 한계

**규칙 기반 (Similo 등):**

| 한계 | 설명 |
|------|------|
| 요소 찾기만 가능 | 그 외 상황 대응 불가 |
| 복잡한 구현 | 다중 선택자, 유사도 계산 등 |
| 새로운 상황 대응 불가 | 미리 정의된 규칙만 |
| 사용자 상호작용 불가 | 질문/확인 불가 |

### Sandy의 접근: LLM을 범용 Fallback으로

**핵심 인사이트:**

> 복잡한 규칙 기반 시스템 대신, **LLM을 범용 Fallback으로 활용**하면
> 구현 복잡도는 낮추면서 대응 범위는 무한대로 확장 가능.

### 간소화된 3-Level Fallback

```
┌─────────────────────────────────────────────────────────┐
│              Selective Reasoning Pipeline                │
│                                                         │
│  Level 1: Exact Match (비용 0)                          │
│     └─ uid 정확히 일치                                  │
│         대부분의 API 호출은 여기서 성공                  │
│                                                         │
│  Level 2: Simple Heuristic (비용 0)                     │
│     └─ text, aria-label 기반                           │
│         간단한 규칙으로 빠르게 시도                      │
│                                                         │
│  Level 3: LLM Reasoning (비용 발생)                     │
│     └─ 범용 문제 해결                                   │
│         ├── 동적 요소 찾기                              │
│         ├── 사용자에게 질문                             │
│         ├── 예상치 못한 상황 대응                       │
│         ├── 에러 분석 및 복구                           │
│         └── 기타 모든 상황                              │
└─────────────────────────────────────────────────────────┘
```

### LLM Fallback이 처리 가능한 상황

```
동적 요소 (기존 접근도 가능):
├── uid 변경
├── DOM 구조 변경
└── A/B 테스트로 UI 다름

새로운 상황 (LLM만 가능):
├── 사용자에게 질문 ("어떤 옵션을 선택할까요?")
├── 예상치 못한 팝업/다이얼로그 처리
├── CAPTCHA 감지 및 사용자 알림
├── 로그인 세션 만료 대응
├── 에러 메시지 해석 및 복구 전략 결정
├── 새로운 필수 필드 발견 시 사용자 입력 요청
└── 기타 예측 불가능한 상황
```

### 시나리오 포맷 (간소화)

```json
{
  "step": 2,
  "tool": "mcp__chrome-devtools__click",
  "params": { "uid": "abc123" },
  "fallback": {
    "text": "로그인",
    "aria-label": "로그인 버튼"
  },
  "llm_hint": "로그인 폼에서 제출 버튼을 찾아 클릭",
  "allow_user_input": true
}
```

**필드 설명:**

| 필드 | 설명 |
|------|------|
| `fallback` | Level 2에서 사용할 간단한 휴리스틱 |
| `llm_hint` | Level 3에서 LLM에게 제공할 힌트 |
| `allow_user_input` | LLM이 사용자에게 질문해도 되는지 |

### Play 시 Resolution 로직

```python
class SelectiveReasoning:
    """간소화된 3-Level Fallback"""

    async def resolve(self, step: dict, context: PlayContext) -> ResolveResult:
        # Level 1: Exact Match
        if result := self.try_exact_match(step["params"]):
            return ResolveResult(success=True, method="exact", cost=0)

        # Level 2: Simple Heuristic
        if fallback := step.get("fallback"):
            if result := self.try_heuristic(fallback, context.snapshot):
                return ResolveResult(success=True, method="heuristic", cost=0)

        # Level 3: LLM Reasoning
        return await self.llm_fallback(step, context)

    async def llm_fallback(self, step: dict, context: PlayContext) -> ResolveResult:
        """LLM에게 문제 해결 위임"""

        prompt = f"""
현재 상황에서 다음 작업을 수행해야 합니다:

목표: {step.get("llm_hint", step.get("description"))}

페이지 정보:
- URL: {context.page_url}
- 스냅샷: {context.snapshot[:2000]}...

가능한 행동:
1. 요소 찾기: {{"action": "find", "uid": "..."}}
2. 사용자에게 질문: {{"action": "ask_user", "question": "..."}}
3. 에러 보고: {{"action": "error", "message": "..."}}

JSON으로 응답해주세요.
"""

        response = await self.llm.complete(prompt)
        action = parse_llm_response(response)

        if action["action"] == "find":
            return ResolveResult(success=True, uid=action["uid"], method="llm", cost=response.tokens)
        elif action["action"] == "ask_user":
            user_input = await self.ask_user(action["question"])
            return await self.continue_with_input(step, context, user_input)
        else:
            return ResolveResult(success=False, error=action["message"], method="llm", cost=response.tokens)
```

### 사용자 상호작용 예시

```
시나리오: 폼 제출 중 새로운 필수 필드 발견

┌────────────────────────────────────────────────────┐
│  Step 3: fill "company" field                       │
│                                                    │
│  Level 1: ❌ uid 없음 (Record 당시 없던 필드)       │
│  Level 2: ❌ fallback 없음                          │
│  Level 3: LLM 개입                                  │
│           │                                        │
│           └─→ "회사명 필드가 추가되었습니다.        │
│                회사명을 입력해주세요:"              │
│                                                    │
│           사용자 입력: "Anthropic"                  │
│           │                                        │
│           └─→ 필드 채우고 계속 진행                │
└────────────────────────────────────────────────────┘
```

### 비용-효과 분석

```
┌─────────────────────────────────────────────────────────┐
│                    비용 vs 대응력                        │
│                                                         │
│  대응력                                                 │
│    │                              ┌─────┐              │
│ 100├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤ LLM │              │
│    │                              └──┬──┘              │
│  80├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─     │
│    │                    ┌─────┐     │                  │
│  60├─ ─ ─ ─ ─ ─ ─ ─ ─ ┤Similo├─ ─ ─│─ ─ ─ ─ ─ ─     │
│    │                    └──┬──┘     │                  │
│  40├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │─ ─ ─ ─ │─ ─ ─ ─ ─ ─     │
│    │        ┌─────┐       │         │                  │
│  20├─ ─ ─ ─┤Exact ├─ ─ ─ ─│─ ─ ─ ─ │─ ─ ─ ─ ─ ─     │
│    │        └──┬──┘       │         │                  │
│   0├───────────┴──────────┴─────────┴─────────────►   │
│    0          낮음       중간       높음     비용      │
│                                                         │
│  Sandy 전략: Exact → (Similo 생략) → LLM               │
│  → 복잡도 낮추고, 대응력 최대화                         │
└─────────────────────────────────────────────────────────┘
```

---

## 실험 설계

### 실험 1: 비용 절감 효과 (RQ1)

**목적:** Sandy가 얼마나 비용/시간을 절감하는가?

| 방식 | 측정 항목 |
|------|----------|
| Pure LLM Agent | 토큰 수, 비용($), 실행 시간 |
| Sandy Play | 실행 시간 (토큰 0) |
| Sandy + LLM Fallback | 토큰 수, 비용, 실행 시간 |

**손익분기점 계산:**
```
Cost_Total = Cost_Record + Cost_Play × N + Cost_LLM_Fallback × F

손익분기점: N > Cost_Record / (Cost_Agent - Cost_LLM_Fallback × (F/N))
```

**실험 시나리오 (API 호출 위주):**
- GitHub 이슈 생성/조회
- Slack 메시지 전송
- Supabase 쿼리 실행

→ API 호출은 동적 요소 문제가 없어 순수 비용 절감 효과 측정 가능

### 실험 2: MCP Tool 유형별 적합성 (RQ2)

**목적:** 어떤 MCP Server/Tool이 Replay에 적합한가?

| 분류 | 특성 | 예시 | 예상 성공률 |
|------|------|------|------------|
| 높은 적합성 | 상태 없음, 결정적 | API 호출, DB 쿼리 | 95%+ |
| 중간 적합성 | 약간의 상태 | 파일 시스템 | 80-95% |
| 낮은 적합성 | 동적 상태, UI | 브라우저 자동화 | 60-80% |

### 실험 3: Selective Reasoning 효과 (RQ3, RQ4)

**목적:** LLM Fallback이 얼마나 효과적인가?

| 측정 항목 | 설명 |
|----------|------|
| LLM 개입률 | 전체 step 중 LLM Fallback 발생 비율 |
| 복구 성공률 | LLM 개입으로 복구된 실패 비율 |
| 개입당 비용 | LLM Fallback 1회당 평균 토큰 |
| 사용자 질문률 | LLM이 사용자에게 질문한 비율 |
| 복구 불가 유형 | LLM도 해결 못하는 패턴 분석 |

**실험 시나리오:**
```
1. API 호출 시나리오 (예상: LLM 개입 거의 없음)
2. 브라우저 자동화 - 정적 사이트 (예상: 낮은 LLM 개입)
3. 브라우저 자동화 - 동적 사이트 (예상: 중간 LLM 개입)
4. 예외 상황 포함 시나리오 (예상: 높은 LLM 개입)
   - 로그인 세션 만료
   - 예상치 못한 팝업
   - 새로운 필수 필드
```

### 실험 4: Procedure-level Replay 효과 (RQ5)

**목적:** Procedure 단위 재사용이 얼마나 효과적인가?

| 비교 대상 | 설명 |
|----------|------|
| Pure LLM Agent | 모든 단계를 LLM이 수행 |
| Full Workflow Replay | 전체 워크플로우 단위 replay (AgentRR 방식) |
| Procedure Replay | Procedure 단위 replay + LLM 조합 (Sandy 방식) |
| ToolCaching | 개별 API 호출 캐싱 |

**측정 항목:**

| 메트릭 | 설명 |
|--------|------|
| 비용 절감률 | LLM 토큰 사용량 감소 비율 |
| 유연성 점수 | 변형 task 수행 가능 비율 |
| 재사용률 | 기존 procedure 활용 비율 |
| 조합 성공률 | 여러 procedure 조합 시 성공률 |

**실험 시나리오:**

```
기본 Task: "GitHub에 로그인해서 이슈 생성"
변형 Tasks:
  - "GitHub에 로그인해서 PR 생성" (일부 procedure 재사용)
  - "GitHub에 로그인해서 이슈 10개 생성" (반복)
  - "GitHub에 로그인해서 이슈 생성 후 Slack 알림" (조합)
  - "GitLab에 로그인해서 이슈 생성" (유사 도메인)
```

**예상 결과:**

| 방식 | 기본 Task | 변형 Task | 비용 |
|------|----------|----------|------|
| Pure LLM | ✅ | ✅ | $$$ |
| Full Workflow | ✅ | ❌ (새로 record 필요) | $ |
| **Procedure** | ✅ | ✅ (조합) | $ |
| ToolCaching | ✅ | △ (일부 캐시) | $$ |

---

## 벤치마크 데이터셋

### 구성 계획

```
sandy-benchmark/
├── procedures/                     # Procedure Library
│   ├── auth/
│   │   ├── github_login.json
│   │   ├── google_oauth.json
│   │   └── slack_login.json
│   ├── github/
│   │   ├── create_issue.json
│   │   ├── create_pr.json
│   │   ├── merge_pr.json
│   │   └── add_comment.json
│   ├── slack/
│   │   ├── send_message.json
│   │   ├── send_dm.json
│   │   └── upload_file.json
│   └── common/
│       ├── file_upload.json
│       ├── form_submit.json
│       └── captcha_solve.json
│
├── scenarios/                      # Full Workflow (비교용)
│   ├── web/
│   │   ├── form-simple.json
│   │   ├── form-dynamic.json
│   │   ├── login-standard.json
│   │   ├── login-oauth.json
│   │   └── navigation-multi.json
│   ├── api/
│   │   ├── github-issue.json
│   │   ├── slack-message.json
│   │   └── notion-page.json
│   └── mixed/
│       └── web-api-combo.json
│
├── tasks/                          # 실험용 Task 세트
│   ├── base/                       # 기본 task
│   │   └── github_issue_create.json
│   ├── variations/                 # 변형 task (RQ5용)
│   │   ├── github_pr_create.json      # 일부 procedure 재사용
│   │   ├── github_issue_bulk.json     # 반복 실행
│   │   ├── github_issue_slack.json    # procedure 조합
│   │   └── gitlab_issue_create.json   # 유사 도메인
│   └── compositions/               # 복합 task
│       ├── daily_standup.json         # 여러 procedure 조합
│       └── release_workflow.json      # 복잡한 워크플로우
│
├── snapshots/
│   └── {scenario}/
│       ├── t0/
│       ├── t1d/
│       ├── t7d/
│       └── t30d/
│
└── results/
    └── {experiment}/
        └── {strategy}/
            └── results.json
```

### Procedure 카탈로그

| 카테고리 | Procedure | 설명 | 난이도 |
|----------|-----------|------|--------|
| **Auth** | github_login | GitHub 로그인 | Easy |
| | google_oauth | Google OAuth 로그인 | Medium |
| | slack_login | Slack 로그인 | Easy |
| **GitHub** | create_issue | 이슈 생성 | Easy |
| | create_pr | PR 생성 | Medium |
| | merge_pr | PR 머지 | Medium |
| | add_comment | 코멘트 추가 | Easy |
| **Slack** | send_message | 채널 메시지 | Easy |
| | send_dm | DM 전송 | Easy |
| | upload_file | 파일 업로드 | Medium |
| **Common** | file_upload | 일반 파일 업로드 | Medium |
| | form_submit | 폼 제출 | Easy |

### 시나리오 난이도 분류

| 난이도 | 특성 | 시나리오 수 |
|--------|------|------------|
| Easy | 정적 요소, 단순 흐름 | 10 |
| Medium | 일부 동적, 조건 분기 | 10 |
| Hard | 동적 uid, 상태 의존 | 10 |

### Procedure 조합 테스트 케이스 (RQ5용)

| 테스트 | 사용 Procedure | 기대 결과 |
|--------|---------------|----------|
| T1: 단일 | github_login | 100% 재사용 |
| T2: 순차 | github_login → create_issue | 100% 재사용 |
| T3: 반복 | create_issue × 10 | 100% 재사용 |
| T4: 조합 | github_login → create_issue → slack_notify | 100% 재사용 |
| T5: 부분 | github_login → (새 작업) | 50% 재사용 |
| T6: 유사 | github_login → gitlab_issue (없음) | 50% 재사용 (login만) |

---

## 논문 구조 (Draft)

```
1. Introduction
   - LLM Agent의 비용/지연 문제
   - 핵심 질문: 결정적 실행과 LLM 추론의 최적 균형점
   - 기여점 요약

2. Background & Related Work
   - MCP (Model Context Protocol)
   - 재사용 단위 스펙트럼: API ↔ Procedure ↔ Workflow
   - AgentRR, Memento, ToolCaching 비교

3. Sandy Framework
   - 아키텍처 개요
   - Procedure 포맷
   - MCP 네이티브 설계

4. Procedure-level Replay (핵심 기여 1)
   - 문제: 전체 워크플로우 vs 개별 API의 딜레마
   - 해결: Procedure-level Abstraction
   - LLM이 Procedure를 선택/조합
   - 비용 모델

5. Selective Reasoning (핵심 기여 2)
   - 문제: 예측 불가능한 상황에서의 실패
   - 해결: LLM을 범용 Fallback으로 활용
   - 간소화된 3-Level 전략
   - 사용자 상호작용 지원

6. Evaluation
   - 실험 설정
   - RQ1: 비용 절감 효과
   - RQ2: MCP Tool 유형별 적합성
   - RQ3: Selective Reasoning 빈도 및 비용
   - RQ4: Selective Reasoning 복구 효과
   - RQ5: Procedure-level Replay 유연성

7. Discussion
   - 적용 범위와 한계
   - Procedure 설계 가이드라인
   - Threats to Validity

8. Conclusion
   - 요약
   - Future Work
```

### 핵심 Figure 구상

```
Figure 1: 재사용 단위 스펙트럼
┌────────────────────────────────────────────────────────┐
│                                                        │
│  개별 API        Procedure         전체 Workflow      │
│     │               │                   │              │
│     ▼               ▼                   ▼              │
│  ┌─────┐       ┌─────────┐        ┌──────────┐        │
│  │Tool │       │ login   │        │ Full     │        │
│  │Cache│       │ upload  │        │ Scenario │        │
│  └─────┘       │ notify  │        └──────────┘        │
│                └─────────┘                             │
│                                                        │
│  유연성: 높음 ◄──────────────────────► 낮음           │
│  효율성: 낮음 ◄──────────────────────► 높음           │
│                     ▲                                  │
│                     │                                  │
│              Sandy Procedures                          │
│              (최적 균형점)                              │
└────────────────────────────────────────────────────────┘

Figure 2: Selective Reasoning 전략 (핵심 기여 2)
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Step 실행                                              │
│    │                                                    │
│    ├─→ Level 1: Exact Match (비용 0)                   │
│    │      └─→ 성공 → 다음 Step                         │
│    │                                                    │
│    ├─→ Level 2: Simple Heuristic (비용 0)              │
│    │      └─→ 성공 → 다음 Step                         │
│    │                                                    │
│    └─→ Level 3: LLM Fallback (비용 발생)               │
│           │                                             │
│           ├─→ 요소 찾기 → 성공 → 다음 Step            │
│           ├─→ 사용자 질문 → 입력 받고 계속             │
│           ├─→ 에러 분석 → 복구 시도                    │
│           └─→ 복구 불가 → 실패 보고                    │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  결정적 실행 (비용 0)  │  LLM 추론 (필요시만, 범용)    │
└─────────────────────────────────────────────────────────┘

Figure 3: LLM이 Sandy를 호출하는 흐름
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  LLM (Claude Code 등)                                   │
│    │                                                    │
│    ├─→ sandy.play("login")                              │
│    │      ├─→ 성공 → 다음 단계                          │
│    │      └─→ 실패 (step 3) → LLM 판단                 │
│    │                │                                   │
│    │                ├─→ 직접 처리 후 sandy.play(start=4)│
│    │                ├─→ 재시도: sandy.play(start=3)     │
│    │                └─→ 건너뛰기: 다음 procedure        │
│    │                                                    │
│    ├─→ sandy.play("create_issue")                       │
│    │      └─→ 성공                                      │
│    │                                                    │
│    └─→ 결과 종합 보고                                   │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  LLM: 호출, 판단, 종합  │  Sandy: 실행 (start/end 지정) │
└─────────────────────────────────────────────────────────┘

Figure 4: 비용 비교 (예상)
┌─────────────────────────────────────────────────────────┐
│  비용 ($)                                               │
│    │                                                    │
│ 100├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ Pure LLM Agent        │
│    │                          ／                        │
│  80├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ／─ ─ ─ ─ ─ ─ ─ ─ ─ ─      │
│    │                    ／                              │
│  60├─ ─ ─ ─ ─ ─ ─ ─ ／─ ─ ─ ─ ─ ToolCaching          │
│    │              ／        ／                          │
│  40├─ ─ ─ ─ ─ ／─ ─ ─ ─ ／─ ─ ─ ─ ─ ─ ─ ─ ─ ─        │
│    │        ／        ／                                │
│  20├─ ─ ／─ ─ ─ ─ ／─ ─ ─ ─ Sandy Procedures          │
│    │  ／        ／                                      │
│   0├─────────────────────────────────────────────►     │
│    0    5    10    15    20    25    반복 횟수         │
└─────────────────────────────────────────────────────────┘
```

---

## 학회 제출 계획

### 제출 대상 (2026년 2월 기준)

| 학회 | 트랙 | 마감 | 페이지 | 출판 | 장소 |
|------|------|------|--------|------|------|
| **ICLR 2026 AIWILD** | Workshop | **2월 6일** | 3-5p | Non-archival | Rio de Janeiro |
| **ACM AIware 2026** | Main | **2월 13일** | 4p (short) | ACM DL | Montreal |

### 제출 전략

```
2/3-6   ICLR AIWILD (3페이지 Short paper)
   ↓ 확장
2/7-13  AIware (4페이지 Short paper)
```

- **AIWILD**: Non-archival → 피드백 수집 + ICLR 커뮤니티 노출
- **AIware**: ACM 정식 출판 → CV 가치, FSE 공동 개최

### ICLR AIWILD 정보

| 항목 | 내용 |
|------|------|
| 워크샵명 | Agents in the Wild: Safety, Security, and Beyond |
| 웹사이트 | https://agentwild-workshop.github.io/ |
| 제출 | https://openreview.net/group?id=ICLR.cc/2026/Workshop/AIWILD |
| 리뷰 | Double-blind |
| Dual submission | ✅ 허용 (non-archival) |

### AIware 2026 정보

| 항목 | 내용 |
|------|------|
| 학회명 | 3rd ACM International Conference on AI-powered Software |
| 웹사이트 | https://2026.aiwareconf.org/ |
| 제출 | https://openreview.net/group?id=ACM.org/AIWare/2026/Conference |
| 리뷰 | Double-blind, OpenReview |
| 공동 개최 | FSE 2026 (Montreal) |

### 논문 폴더 구조

```
research/
├── papers/
│   ├── aiwild-2026/     # ICLR Workshop
│   │   ├── main.tex
│   │   └── figures/
│   └── aiware-2026/     # AIware
│       ├── main.tex
│       └── figures/
├── slides/
└── notes/
```

### 후속 제출 계획 (Accept 여부에 따라)

| 시기 | 학회 | 조건 |
|------|------|------|
| 2026.04 | ICML 2026 Workshop | AIWILD/AIware 피드백 반영 |
| 2026.05 | ICSME 2026 Tool Demo | 구현 완료 시 |
| 2026.05 | NeurIPS 2026 Main | 실험 완료 시 |

---

## 타임라인

### 단기 (2026년 2월)

| 날짜 | 할 일 |
|------|------|
| 2/3-4 | AIWILD 논문 초안 (Introduction + Approach) |
| 2/5 | AIWILD 논문 완성 (Related Work + Conclusion) |
| 2/6 | **AIWILD 제출** |
| 2/7-12 | AIware 논문 확장 |
| 2/13 | **AIware 제출** |

### 중기 (2026년 상반기)

| 단계 | 내용 | 목표 |
|------|------|------|
| Phase 1 | Play 구현 + 기본 실험 | v0.2.0 |
| Phase 2 | 동적 요소 대응 구현 | v0.3.0 |
| Phase 3 | 전체 실험 수행 | - |
| Phase 4 | 풀페이퍼 작성 | NeurIPS/ICSME |

---

## 스폰서십/Travel Grant

### 비용 예상

| 학회 | 등록비 | 항공 | 숙박 | 합계 |
|------|--------|------|------|------|
| ICLR (Brazil) | ~$800 | ~$1,500 | ~$600 | ~$2,900 |
| AIware (Montreal) | ~$800 | ~$1,200 | ~$600 | ~$2,600 |

### 지원 옵션

1. **ICLR Financial Assistance** - https://iclr.cc/Conferences/2026/FinancialAssistance
2. **Citadel Travel Grant** - 마감 3월 13일
3. **기업 스폰서십** - Anthropic (MCP 관련)
4. **Virtual 발표 요청** - Accept 후 협의

### Anthropic 연락

- Fellows Program: fellows@anthropic.com
- LinkedIn: Anthropic MCP Developer Relations
- 제안: MCP 기반 연구 스폰서십 요청

---

## 참고 자료

### 핵심 논문 (Sandy와 가장 유사)
- [AgentRR: Record & Replay for LLM Agents](https://arxiv.org/abs/2505.17716) - 가장 유사한 연구
- [Blueprint First, Model Second](https://arxiv.org/abs/2508.02721) - 결정적 워크플로우 실행
- [Memento: Case-based LLM Agents](https://arxiv.org/abs/2508.16153) - Trajectory 저장/재사용
- [ToolCaching](https://arxiv.org/abs/2601.15335) - Tool calling 캐싱

### 동적 요소 대응 (참고용, Sandy는 LLM Fallback 사용)
- [Web Element Relocalization](https://arxiv.org/abs/2505.16424) - VON Similo, 96-99% 복구율 (규칙 기반)
- [Similo (TOSEM 2023)](https://dl.acm.org/doi/10.1145/3571855) - 규칙 기반 알고리즘
- Sandy 접근: 규칙 기반 대신 **LLM을 범용 Fallback으로 활용** → 구현 단순화 + 대응 범위 확대

### MCP 관련
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Landscape & Security](https://arxiv.org/abs/2503.23278)
- [MCP-Universe Benchmark](https://arxiv.org/abs/2508.14704)
- [MCP-Bench](https://arxiv.org/abs/2508.20453)

### 웹 에이전트 벤치마크
- [WebArena](https://arxiv.org/abs/2307.13854) - 표준 벤치마크
- [VisualWebArena](https://arxiv.org/abs/2401.13649) - 비주얼 벤치마크
- [WebVoyager](https://arxiv.org/abs/2401.13919) - 멀티모달 에이전트

### 비용 최적화
- [AgentDiet](https://arxiv.org/abs/2509.23586) - Trajectory 압축
- [GPT Semantic Cache](https://arxiv.org/abs/2411.05276) - 시맨틱 캐싱
- [Efficient Agents](https://arxiv.org/abs/2508.02694) - 비용 인식 평가

### 도구 & 구현
- [Healenium](https://github.com/healenium/healenium-web) - Self-healing 오픈소스
- [Awesome Web Agents](https://github.com/steel-dev/awesome-web-agents) - 리소스 모음

---

*Last updated: 2026-02-03 (Selective Reasoning 중심으로 재구성, Similo 제거)*
