# Sandy 개발 계획

> **A Sandevistan for your AI Agent.**

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **제품명** | Sandy |
| **학술 제목** | Sandy: Accelerating LLM Agents via Deterministic Replay and Selective Reasoning |
| **슬로건** | A Sandevistan for your AI Agent |
| **핵심 가치** | Speed, Record & Play, Hybrid |

### 핵심 아이디어

**MCP Tool 호출을 Record/Play**

- 현재 MCP 표준: Tool 호출 로깅 (감사/보안 목적)
- **Sandy가 추가**: Tool 호출 시퀀스 저장 → LLM 없이 재실행

```
MCP 표준:   Tool 정의 → Tool 호출 → 결과 반환
                 ↓
Sandy 레이어:  Tool 호출 → Record → JSON 저장
               JSON → Play → Tool 재호출 (LLM 없이, 비용 0원)
```

### 2가지 작동 모드

| 모드 | 역할 | 구현 방식 | AI 역할 |
|------|------|----------|--------|
| 🔴 **Record** | Tool 호출 시퀀스 기록 | 프롬프트 | 작업 수행 + 기록 |
| 🟢 **Play** | 시나리오/Procedure 재실행 | 스크립트 | 실행만 (LLM 불필요) |

**LLM + Sandy 조합 사용:**
- Sandy는 Record/Play만 제공
- LLM이 어떤 Procedure를 언제 쓸지 **판단**
- Sandy는 호출되면 **결정적으로 실행**

### 아키텍처 (Skill 기반)

```
sandy-skill/
├── SKILL.md              # 언제/어떻게 사용할지 지침
├── scripts/
│   └── play.py           # Play 로직 (Python)
├── prompts/
│   └── record.md         # Record Agent 지시사항
├── references/
│   └── schema.md         # JSON 스키마 문서
└── assets/
    └── examples/         # 예제 시나리오
```

### 언어 선택: Python

| 언어 | Claude Code | Gemini CLI | Codex | 선택 |
|------|-------------|------------|-------|------|
| Python | O | O | O (권장) | **채택** |
| Node/TS | O | O | 비권장 | - |
| Shell | O | O | O | 복잡한 로직 어려움 |

### 동작 방식

```
Record 모드 (Agent가 작업하면서 기록):
┌────────────────────────────────────────────────────┐
│  사용자: "GitHub 이슈 만드는 거 기록해줘"           │
│      │                                             │
│      ▼                                             │
│  AI가 prompts/record.md 읽음                       │
│      │                                             │
│      ▼                                             │
│  AI가 실제 작업 수행 (navigate, click, fill...)    │
│      │                                             │
│      ▼                                             │
│  Tool 호출들을 JSON 시나리오로 변환                │
│      │                                             │
│      ▼                                             │
│  scenario.json 저장                                │
└────────────────────────────────────────────────────┘

Play 모드 (MCP Server 연결/spawn):
┌────────────────────────────────────────────────────┐
│  사용자: "이 시나리오 실행해"                       │
│      │                                             │
│      ▼                                             │
│  AI가 scripts/play.py 실행 (Bash tool)             │
│      │                                             │
│      ▼                                             │
│  Config에서 서버 설정 읽기                         │
│      │                                             │
│      ├─→ endpoint 있음: SSE/WS로 기존 서버 연결    │
│      │                                             │
│      └─→ endpoint 없음: stdio로 직접 spawn         │
│      │                                             │
│      ▼                                             │
│  Tool 직접 호출 (LLM 완전 배제, 비용 0원)          │
│      │                                             │
│      ▼                                             │
│  결과 반환 (실패 시 AI가 판단)                     │
└────────────────────────────────────────────────────┘
```

### Play 아키텍처

```
방식 1: 기존 서버 연결 (SSE/WebSocket)
─────────────────────────────────────
┌─────────────────────────────────────────────────────────┐
│                       Host                               │
│                (Claude Code, Cursor 등)                  │
│         MCP Server들을 SSE/WS 모드로 실행                │
└─────────────────────────│────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│chrome-devtools│  │   supabase   │  │    slack     │
│  :9222 (ws)  │  │  :3101/sse   │  │  :3102/sse   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       └─────────────────┼─────────────────┘
                         │ 연결
                         ▼
              ┌─────────────────────┐
              │    Sandy Player     │
              │  (세션 공유, 즉시)   │
              └─────────────────────┘

방식 2: 직접 spawn (stdio)
─────────────────────────
┌─────────────────────────────────────────────────────────┐
│                    Sandy Player                          │
│                                                         │
│  Config 읽기 → command/args로 MCP Server spawn          │
│       │                                                 │
│       ▼                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   github     │  │   notion     │  │   postgres   │  │
│  │   (stdio)    │  │   (stdio)    │  │   (stdio)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  (독립 실행, CI/CD 적합)                                 │
└─────────────────────────────────────────────────────────┘
```

### Transport 방식

| Transport | 공유 가능 | Sandy 지원 | 동작 |
|-----------|----------|-----------|------|
| **SSE/HTTP** | O | **O** | 기존 서버에 연결 |
| **WebSocket** | O | **O** | 기존 서버에 연결 |
| **stdio** | X (1:1) | **O** | 직접 spawn |

### Transport 자동 선택

```
┌─────────────────────────────────────────────────────────┐
│                  Sandy Transport 선택                    │
│                                                         │
│  1. SSE/WebSocket endpoint 설정 있음?                   │
│     ├─→ Yes: 기존 서버에 연결 (세션 공유)               │
│     │        - Host가 띄운 서버 재사용                  │
│     │        - 브라우저 상태 등 유지                    │
│     │                                                   │
│     └─→ No: stdio로 직접 spawn (독립 세션)              │
│              - Config에서 command/args 읽기             │
│              - 새 프로세스 생성                         │
│              - CI/CD, 독립 실행에 적합                  │
└─────────────────────────────────────────────────────────┘
```

| 상황 | Transport | 장점 | 단점 |
|------|-----------|------|------|
| Host가 SSE/WS로 띄움 | 연결 | 세션 공유, 즉시 실행 | Host 의존 |
| 독립 실행 (CI/CD 등) | spawn | 완전 독립 | 새 세션, 초기화 필요 |

### Config 설정

```json
// ~/.sandy/config.json (또는 환경별 자동 감지)
{
  "servers": {
    "chrome-devtools": {
      // SSE/WebSocket: 기존 서버에 연결
      "endpoint": "ws://localhost:9222"
    },
    "supabase": {
      // SSE: 기존 서버에 연결
      "endpoint": "http://localhost:3101/sse"
    },
    "github": {
      // stdio: 직접 spawn (endpoint 없으면 자동)
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

| 설정 | Transport | 동작 |
|------|-----------|------|
| `endpoint` 있음 (ws://) | WebSocket | 기존 서버 연결 |
| `endpoint` 있음 (http://) | SSE | 기존 서버 연결 |
| `endpoint` 없음, `command` 있음 | stdio | 직접 spawn |

| 환경 | Config 감지 방법 |
|------|-----------------|
| Claude Desktop | `claude_desktop_config.json` 읽기 |
| Cursor | Cursor MCP 설정 읽기 |
| Standalone | `~/.sandy/config.json` |

### Config 자동 감지 로직

```python
def detect_config() -> dict:
    """환경별 MCP Config 자동 감지 (우선순위 순)"""

    # 1. 환경변수로 직접 지정 (최우선)
    if os.getenv("SANDY_CONFIG"):
        return load_config(os.getenv("SANDY_CONFIG"))

    # 2. 프로젝트 로컬 config
    local_config = Path.cwd() / ".sandy/config.json"
    if local_config.exists():
        return load_config(local_config)

    # 3. Claude Desktop config
    claude_config = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if claude_config.exists():
        return parse_claude_config(claude_config)

    # 4. Cursor config
    cursor_config = Path.home() / ".cursor/mcp.json"
    if cursor_config.exists():
        return parse_cursor_config(cursor_config)

    # 5. Sandy 글로벌 config
    sandy_config = Path.home() / ".sandy/config.json"
    if sandy_config.exists():
        return load_config(sandy_config)

    raise ConfigNotFoundError("No MCP config found")
```

| 우선순위 | Config 위치 | 용도 |
|---------|------------|------|
| 1 | `$SANDY_CONFIG` | 명시적 지정 |
| 2 | `./.sandy/config.json` | 프로젝트별 설정 |
| 3 | Claude Desktop config | Claude Code 연동 |
| 4 | Cursor config | Cursor 연동 |
| 5 | `~/.sandy/config.json` | 글로벌 기본값 |

### 방식별 비교

| 항목 | stdio (spawn) | SSE/WebSocket (연결) |
|------|--------------|---------------------|
| 리소스 | 새로 할당 | **공유** |
| 세션 | 새로 생성 | **기존 유지** |
| 브라우저 상태 | 초기화 | **유지** |
| 초기화 시간 | 필요 | **즉시** |
| Host 의존 | **없음** | 있음 |
| CI/CD | **적합** | 어려움 |

### 에러 복구 전략

```
Play 실행 중 Step 3에서 실패:
┌────────────────────────────────────────────────────┐
│  Step 1: ✅ 성공                                   │
│  Step 2: ✅ 성공                                   │
│  Step 3: ❌ 실패 (요소를 찾을 수 없음)             │
│  Step 4: ⏸️ 미실행                                │
│  Step 5: ⏸️ 미실행                                │
└────────────────────────────────────────────────────┘
```

**반환값:**

```python
PlayResult(
    success=False,
    completed_steps=[1, 2],
    failed_step=3,
    error="Element not found: #submit_button",
    outputs={"issue_title": "버그 수정"},
    step_results=[
        StepResult(step=1, tool="mcp__chrome__navigate", success=True,
                   result={"url": "https://github.com/..."}),
        StepResult(step=2, tool="mcp__chrome__fill", success=True,
                   result={"filled": True}),
        StepResult(step=3, tool="mcp__chrome__click", success=False,
                   error="Element not found: #submit_button")
    ],
    context={"page_url": "https://github.com/...", "snapshot": "..."}
)
```

**LLM이 결과 활용:**

```python
# 실패 원인 파악
result.step_results[-1].error  # "Element not found: #submit_button"
result.step_results[-1].tool   # "mcp__chrome__click"

# 이전 step 결과 확인
result.step_results[0].result  # 첫 번째 step의 MCP 응답
```

**LLM이 판단 후 복구:**

```python
# Case 1: 실패 지점부터 재시작
play("scenario.json", start=3)

# Case 2: 실패 step 건너뛰고 계속
play("scenario.json", start=4)

# Case 3: 실패 step만 재시도
play("scenario.json", start=3, end=3)

# Case 4: LLM이 직접 처리 후 계속
llm.call_tool("mcp__chrome-devtools__click", {...})  # 직접 처리
play("scenario.json", start=4)                        # 나머지 실행
```

**LLM 연동 흐름:**

```
Sandy 실패 반환
    │
    ▼
LLM 판단:
  ├─→ "일시적 오류" → play(start=3) 재시도
  ├─→ "selector 문제" → LLM이 직접 처리 → play(start=4)
  ├─→ "이 step 불필요" → play(start=4) 건너뛰기
  └─→ "환경 문제" → 사용자에게 안내
```

### 역할 분리

```
Agent (LLM)                         Sandy (Skill)                    MCP Servers
    │                                   │                                │
    ├─→ /sandy:record ─────────────────→│                                │
    │   (Agent가 작업하면서 기록)        │                                │
    │   Agent가 직접 MCP Tool 호출 ─────────────────────────────────────→│
    │   Tool 호출 기록 → JSON 생성      │                                │
    │                                   │                                │
    ├─→ /sandy:play ───────────────────→│                                │
    │   (스크립트 실행만)               │──→ MCP Client 직접 연결 ───────→│
    │                                   │    (LLM 완전 배제)              │
    │                                   │                                │
    │◀── 실패 시 결과 반환 ◀────────────│                                │
    │                                   │                                │
    └─→ Agent가 판단 (Selective Reasoning)
            │
            └─→ 수정 후 다시 호출
```

- **Sandy의 책임**: Record 프롬프트 + Play 스크립트 (MCP 직접 연결)
- **Agent의 책임**: Record 시 작업 수행, Play 실패 시 판단 및 수정

### Skill 방식의 장점

| 항목 | 설명 |
|------|------|
| **배포 단순화** | npm 패키지 없이 skill 폴더만 공유 |
| **교차 호환** | Claude Code, Gemini CLI, Codex 모두 지원 |
| **버전 관리** | 프로젝트 `.claude/skills/`에 두면 레포와 함께 이동 |
| **설치 불필요** | 폴더 복사만으로 사용 가능 |

---

## Tool 이름 규칙

MCP Tool 이름은 `mcp__<server>__<tool>` 형식을 따릅니다.

```
mcp__chrome-devtools__click
 │        │            │
 │        │            └─ Tool 이름
 │        └─ MCP Server 이름
 └─ MCP 접두사
```

| 예시 | Server | Tool |
|------|--------|------|
| `mcp__chrome-devtools__click` | chrome-devtools | click |
| `mcp__chrome-devtools__fill` | chrome-devtools | fill |
| `mcp__supabase__query` | supabase | query |
| `mcp__github__create_issue` | github | create_issue |

Sandy는 이 규칙으로 Tool 이름을 파싱하여 해당 MCP Server에 연결합니다.

---

## Procedure Library (v2.2 신규)

### 개념

**Procedure**: 재사용 가능한 Tool 호출 시퀀스 (로그인, 이슈 생성 등)

```
┌─────────────────────────────────────────────────────────┐
│              재사용 단위 스펙트럼                        │
│                                                         │
│  개별 API        Procedure         전체 Workflow        │
│  (ToolCaching)   (Sandy)           (AgentRR)            │
│     │               │                   │               │
│     ▼               ▼                   ▼               │
│  유연성: 높음 ◄─────────────────────► 낮음              │
│  효율성: 낮음 ◄─────────────────────► 높음              │
│                     ▲                                   │
│              Sandy Procedures                           │
│              (최적 균형점)                               │
└─────────────────────────────────────────────────────────┘
```

### 왜 Procedure인가?

| 접근법 | 재사용 단위 | 한계 |
|--------|------------|------|
| 전체 Workflow | 처음부터 끝까지 | 조금만 달라도 새로 Record |
| 개별 API 캐싱 | 단일 호출 | 컨텍스트/시퀀스 손실 |
| **Procedure** | 의미 있는 단위 | **LLM이 조합 가능** |

### LLM이 Procedure 선택/조합

```
User: "GitHub에 로그인해서 이슈 10개 만들고 Slack에 알려줘"

┌─────────────────────────────────────────────────────────┐
│  LLM 판단:                                              │
│  "github_login, create_issue, slack_notify 있네"        │
│  "이걸 조합해서 쓰면 되겠다"                             │
│                                                         │
│  LLM이 sandy.play() 호출:                               │
│  ├─→ sandy.play("github_login")     ← Sandy 실행 (0원) │
│  ├─→ for i in range(10):                               │
│  │      sandy.play("create_issue")  ← Sandy 실행 (0원) │
│  ├─→ sandy.play("slack_notify")     ← Sandy 실행 (0원) │
│  └─→ 결과 종합 보고                  ← LLM (비용 발생)  │
└─────────────────────────────────────────────────────────┘

총 비용: LLM 판단 + 종합만 (Procedure 실행은 0원)
```

**역할 분리:**
- **LLM**: 어떤 Procedure를 언제 쓸지 결정
- **Sandy**: 호출된 Procedure를 결정적으로 실행

### Procedure 포맷 (v2.2)

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
    "username": { "type": "string", "extract": "$.profile.login" }
  },

  "preconditions": [
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
      "selectors": { "primary": {...}, "fallback": [...] }
    },
    {
      "step": 3,
      "tool": "mcp__chrome-devtools__fill",
      "params": { "uid": "password", "value": "{{PASSWORD}}" }
    },
    {
      "step": 4,
      "tool": "mcp__chrome-devtools__click",
      "params": { "uid": "sign_in_button" }
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

### LLM 통합

```python
class ProcedureLibrary:
    def list_procedures(self) -> list[ProcedureInfo]:
        """LLM에게 사용 가능한 procedure 목록 제공"""
        return [
            {"name": "github_login", "description": "GitHub 로그인", "inputs": [...]},
            {"name": "create_issue", "description": "이슈 생성", "inputs": [...]},
            ...
        ]

    async def play(self, name: str, variables: dict) -> PlayResult:
        """Procedure 실행 (LLM 비용 0)"""
        ...
```

### System Prompt에 Procedure 노출

```
You have access to pre-recorded procedures that execute without LLM cost:

## Available Procedures
- github_login(USERNAME, PASSWORD): GitHub 로그인
- create_issue(REPO, TITLE, BODY): GitHub 이슈 생성
- slack_notify(CHANNEL, MESSAGE): Slack 알림

## Usage
sandy.play("procedure_name", {"VAR": "value"})

Use procedures when possible instead of step-by-step actions.
```

### 비용 비교

| 시나리오 | Pure LLM | Full Workflow | **Procedures** |
|----------|----------|---------------|----------------|
| 이슈 1개 생성 | $$$ | $ | $ |
| 이슈 10개 생성 | $$$$$$$$$$ | 불가 (내용 다름) | **$** |
| 이슈 + Slack | $$$$$ | 불가 (조합) | **$** |
| 약간 다른 작업 | $$$ | 새로 Record | **일부 재사용** |

---

## 일반화된 시나리오 포맷 (v2.1)

### 기존 (Web 특화)

```json
{
  "version": "1.1",
  "steps": [
    { "action": "navigate", "params": { "url": "..." } },
    { "action": "click", "params": { "ref": "..." } }
  ]
}
```

### 새로운 (MCP Tool 범용 + 런타임 결과 참조)

```json
{
  "version": "2.1",
  "metadata": {
    "name": "GitHub Issue 생성 + Slack 알림",
    "created_at": "2025-02-03T12:00:00Z"
  },
  "variables": {
    "ISSUE_TITLE": "버그 수정 필요",
    "CHANNEL": "#dev"
  },
  "steps": [
    {
      "step": 1,
      "id": "create_issue",
      "tool": "mcp__github__create_issue",
      "params": {
        "repo": "owner/repo",
        "title": "{{ISSUE_TITLE}}"
      },
      "output": {
        "issue_number": "$.number",
        "issue_url": "$.html_url"
      },
      "description": "GitHub 이슈 생성"
    },
    {
      "step": 2,
      "tool": "mcp__slack__post_message",
      "params": {
        "channel": "{{CHANNEL}}",
        "text": "이슈 #{{create_issue.issue_number}} 생성됨: {{create_issue.issue_url}}"
      },
      "on_error": "skip",
      "description": "Slack 알림"
    },
    {
      "step": 3,
      "tool": "mcp__chrome-devtools__navigate_page",
      "params": {
        "url": "{{create_issue.issue_url}}"
      },
      "wait_for": { "timeout": 5000 },
      "description": "이슈 페이지로 이동"
    }
  ]
}
```

### Step 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `step` | number | O | 실행 순서 |
| `id` | string | - | 결과 참조용 식별자 |
| `tool` | string | O | MCP Tool 이름 |
| `params` | object | O | Tool 파라미터 |
| `output` | object | - | 결과에서 추출할 값 (JSONPath) |
| `wait_for` | object | - | 실행 전 대기 조건 |
| `on_error` | string | - | 에러 시 동작: `"retry"`, `"skip"`, `"fail"` |
| `retry` | object | - | 재시도 설정: `{ "count": 3, "delay": 1000 }` |
| `condition` | string | - | 조건부 실행 |
| `description` | string | - | 설명 |

### Output (결과 추출)

`output` 필드로 Tool 결과에서 필요한 값을 JSONPath로 추출합니다.

```json
"output": {
  "id": "$.id",
  "name": "$.data.name",
  "first_item": "$.items[0]",
  "full_response": "$"
}
```

| JSONPath | 설명 |
|----------|------|
| `$.field` | 최상위 필드 |
| `$.data.name` | 중첩 필드 |
| `$.items[0]` | 배열 첫 번째 요소 |
| `$` | 전체 결과 |

### 변수 참조 문법

| 타입 | 문법 | 예시 |
|------|------|------|
| 정적 변수 | `{{VAR_NAME}}` | `{{ISSUE_TITLE}}` |
| Step 결과 필드 | `{{step_id.field}}` | `{{create_issue.issue_number}}` |
| Step 전체 결과 | `{{step_id}}` | `{{create_issue}}` |
| 환경 변수 | `${ENV_VAR}` | `${GITHUB_TOKEN}` |

**.env 파일 지원:**
```
# .sandy.env 또는 .env
GITHUB_TOKEN=ghp_xxx
SLACK_WEBHOOK=https://hooks.slack.com/xxx
```

### 적용 범위

| 도메인 | MCP Server | 예시 Tool |
|--------|------------|-----------|
| **Web** | chrome-devtools, claude-in-chrome | navigate, click, fill |
| **File** | filesystem | read_file, write_file |
| **DB** | postgres, supabase | query |
| **API** | slack, github, notion | post_message, create_issue |
| **Desktop** | (추가 예정) | mouse_click, keyboard_type |
| **Mobile** | (추가 예정) | tap, swipe |

---

## Phase 0: 프로젝트 설정

### 0.1 디렉토리 구조

- [ ] `sandy-skill/` 폴더 생성
- [ ] 기본 파일 구조 설정

### 0.2 문서 정비

- [ ] `README.md` 작성 (슬로건, 설치, 사용법)
- [ ] JSON Schema 문서화 (`references/schema.md`)

---

## Phase 1: Skill 구조 구현

### 1.1 시나리오 포맷 v2.1

- [ ] v1.1 (Web 특화) → v2.1 (MCP Tool 범용 + 런타임 결과 참조) 포맷 정의
- [ ] `action` → `tool` 필드 변경
- [ ] `id`, `output` 필드 추가 (런타임 결과 참조)
- [ ] 기존 Web 액션을 MCP Tool 호출로 매핑
  ```
  navigate → mcp__chrome-devtools__navigate_page
  click    → mcp__chrome-devtools__click
  fill     → mcp__chrome-devtools__fill
  ```

### 1.2 Skill 폴더 구조

```
sandy-skill/
├── SKILL.md              # Skill 사용 지침
│                         # - /sandy:record 설명
│                         # - /sandy:play 설명
│                         # - 예제 사용법
│
├── scripts/
│   ├── play.py           # Play 실행 스크립트
│   └── requirements.txt  # 의존성
│                         # - mcp (MCP Python SDK)
│                         # - httpx-sse (SSE 클라이언트)
│                         # - websockets (WebSocket 클라이언트)
│                         # - jsonpath-ng (결과 추출)
│
├── prompts/
│   └── record.md         # Record Agent 프롬프트
│                         # - 작업하면서 Tool 호출 기록
│                         # - JSON 시나리오 생성 규칙
│                         # - 변수 추출 가이드
│
├── references/
│   └── schema.md         # v2.1 JSON 스키마 문서
│
└── assets/
    └── examples/
        ├── github-issue.json
        ├── slack-notify.json
        └── web-form.json
```

### 1.3 Record 프롬프트 작성

- [ ] `prompts/record.md` 작성
  - 작업 수행하면서 모든 Tool 호출 기록
  - 반복 가능한 부분 변수화 (`{{VAR}}`)
  - `id`, `output` 필드로 결과 참조 설정
  - v2.1 포맷으로 JSON 생성
  - 저장 위치 결정

### 1.4 Play 스크립트 구현

- [ ] `scripts/play.py` 구현
  - JSON 시나리오 파싱
  - 변수 치환 (`{{VAR}}`, `{{step_id.field}}`)
  - Output 추출 (JSONPath)
  - Transport 자동 선택 (SSE/WS 연결 또는 stdio spawn)
  - MCP Client로 Tool 직접 호출
  - 실패 시 상세 결과 반환

```python
@dataclass
class StepResult:
    step: int
    tool: str                      # "mcp__github__create_issue"
    params: dict                   # 실제 호출한 파라미터 (변수 치환 후)
    success: bool
    result: Any | None = None      # MCP 원본 결과 (include_results 옵션에 따라)
    error: str | None = None

@dataclass
class PlayResult:
    success: bool
    completed_steps: list[int]     # 완료된 step 번호 목록
    failed_step: int | None        # 실패한 step 번호
    error: str | None              # 에러 메시지
    outputs: dict                  # JSONPath로 추출한 값 (항상 포함)
    step_results: list[StepResult] # 각 step 정보
    context: dict | None = None    # 디버깅 정보

# include_results 옵션에 따른 동작:
# - False (기본): step_results[i].result = None (토큰 절약)
# - True: step_results[i].result = MCP 원본 결과
# - "on_failure": 실패한 step만 result 포함

class ScenarioPlayer:
    def __init__(self, scenario: dict):
        self.scenario = scenario
        self.variables = dict(scenario.get("variables", {}))
        self.step_outputs = {}  # id -> extracted output

    def execute(
        self,
        start: int = 1,
        end: int | None = None,
        include_results: bool | str = False  # False, True, "on_failure"
    ) -> PlayResult:
        """시나리오 실행 (시작/종료 지점 지정 가능)"""
        steps = self.scenario["steps"]
        end = end or len(steps)

        completed = []
        step_results = []

        for step in steps:
            step_num = step["step"]

            # 범위 체크
            if step_num < start:
                continue
            if step_num > end:
                break

            # 1. 변수 치환 ({{VAR}}, {{step_id.field}})
            params = self.substitute_variables(step["params"])

            try:
                # 2. Tool 호출
                mcp_result = self.call_tool(step["tool"], params)

                # 3. Output 추출 (JSONPath) - 항상 수행
                if "id" in step and "output" in step:
                    self.extract_output(step["id"], step["output"], mcp_result)

                # 4. StepResult 저장 (include_results에 따라 result 포함 여부 결정)
                step_results.append(StepResult(
                    step=step_num,
                    tool=step["tool"],
                    params=params,
                    success=True,
                    result=mcp_result if include_results == True else None
                ))
                completed.append(step_num)

            except Exception as e:
                # 실패 시: include_results가 "on_failure"면 context 포함
                include_on_fail = include_results in [True, "on_failure"]
                step_results.append(StepResult(
                    step=step_num,
                    tool=step["tool"],
                    params=params,
                    success=False,
                    result=None,
                    error=str(e)
                ))
                return PlayResult(
                    success=False,
                    completed_steps=completed,
                    failed_step=step_num,
                    error=str(e),
                    outputs=self.step_outputs,
                    step_results=step_results,
                    context=self.get_current_context() if include_on_fail else None
                )

        return PlayResult(
            success=True,
            completed_steps=completed,
            failed_step=None,
            error=None,
            outputs=self.step_outputs,
            step_results=step_results
        )

    def extract_output(self, step_id: str, output_spec: dict, result: dict):
        """JSONPath로 결과에서 값 추출"""
        from jsonpath_ng import parse as jsonpath_parse

        extracted = {}
        for name, path in output_spec.items():
            if path == "$":
                extracted[name] = result
            else:
                expr = jsonpath_parse(path)
                matches = expr.find(result)
                extracted[name] = matches[0].value if matches else None

        self.step_outputs[step_id] = extracted
```

**CLI 인터페이스:**

```bash
# 기본 실행 (전체)
python play.py scenario.json

# 시작/종료 지점 지정
python play.py scenario.json --start 3              # step 3부터 끝까지
python play.py scenario.json --end 2                # step 1~2만
python play.py scenario.json --start 2 --end 4      # step 2~4만

# 변수 전달
python play.py scenario.json --var TITLE="버그 수정" --var CHANNEL="#dev"

# 환경변수 파일 지정
python play.py scenario.json --env .sandy.env

# Config 직접 지정
python play.py scenario.json --config ~/.sandy/config.json

# 디버그 모드 (상세 로그)
python play.py scenario.json --debug

# Dry run (실제 호출 없이 검증만)
python play.py scenario.json --dry-run
```

**CLI 옵션:**

| 옵션 | 설명 |
|------|------|
| `--start N` | N번 step부터 시작 (기본: 1) |
| `--end N` | N번 step까지 실행 (기본: 마지막) |
| `--var KEY=VALUE` | 변수 전달 (여러 개 가능) |
| `--env FILE` | 환경변수 파일 경로 |
| `--config FILE` | Config 파일 경로 |
| `--include-results` | MCP 원본 결과 포함 |
| `--include-results-on-failure` | 실패 시만 MCP 결과 포함 |
| `--debug` | 상세 로그 출력 |
| `--dry-run` | 실제 호출 없이 검증 |
| `--output FILE` | 결과 JSON 저장 경로 |

**Python API:**

```python
from sandy import play

# 전체 실행
result = play("scenario.json", variables={"TITLE": "버그"})

# 부분 실행
result = play("scenario.json", start=3)           # step 3부터
result = play("scenario.json", end=2)             # step 1~2만
result = play("scenario.json", start=2, end=4)    # step 2~4만

# 실패 후 재시작
if not result.success:
    result = play("scenario.json", start=result.failed_step)

# MCP 결과 포함 옵션
result = play("scenario.json")                           # 기본: outputs만
result = play("scenario.json", include_results=True)     # 전체 MCP 결과 포함
result = play("scenario.json", include_results="on_failure")  # 실패 시만 포함
```

### 1.5 SKILL.md 작성

- [ ] `/sandy:record` 사용법
- [ ] `/sandy:play` 사용법
- [ ] 예제 시나리오 설명
- [ ] 트러블슈팅 가이드

---

## Phase 2: 플랫폼 지원 확장

### 2.1 Claude Code (기본)

- [ ] `.claude/skills/sandy/`에 배치
- [ ] `/sandy:record`, `/sandy:play` 동작 확인

### 2.2 Gemini CLI

- [ ] Gemini CLI의 Skill 구조 확인
- [ ] 호환성 테스트
- [ ] 필요시 어댑터 작성

### 2.3 Codex CLI

- [ ] Codex CLI의 Skill 구조 확인
- [ ] 호환성 테스트
- [ ] 필요시 어댑터 작성

### 2.4 호환성 매트릭스

| 플랫폼 | Skill 지원 | MCP 지원 | 상태 |
|--------|-----------|---------|------|
| Claude Code | O | O | Phase 2 |
| Gemini CLI | ? | ? | 조사 필요 |
| Codex CLI | ? | ? | 조사 필요 |

---

## Phase 3: 확장

### 3.1 Desktop Automation

- [ ] 키보드/마우스 제어 MCP Server 연동
- [ ] 화면 캡처 + OCR
- [ ] Desktop용 Tool 지원

### 3.2 Mobile Automation

- [ ] ADB 연동 (Android) MCP Server
- [ ] Mobile용 Tool 지원

### 3.3 CI/CD 연동

- [ ] GitHub Actions 예제
- [ ] Docker 이미지
- [ ] 환경변수 주입

---

## Phase 4: 학술 & 공개

> 상세 연구 계획은 [RESEARCH.md](./RESEARCH.md) 참조

### 4.1 핵심 기여점

| 기여 | 설명 |
|------|------|
| **MCP 네이티브 구현** | AgentRR은 언급만, Sandy는 실제 구현 |
| **동적 요소 대응 전략** | 다중 선택자 + 계층적 Fallback |
| **정량적 평가** | AgentRR이 안 한 비용/속도/성공률 측정 |
| **Selective Reasoning 효과** | LLM Fallback의 실제 복구율 |

### 4.2 실험 계획

| 실험 | 목적 |
|------|------|
| 선택자 전략별 성공률 | 어떤 fallback 조합이 가장 robust? |
| 시간 경과에 따른 성공률 | Record 후 얼마나 유효한가? |
| 비용/속도 비교 | 손익분기점 계산 |
| Selective Reasoning 효과 | LLM fallback 복구율 |

### 4.3 논문 작성

- [ ] 관련 연구 조사 (AgentRR, RPA, MCP)
- [ ] 동적 요소 대응 전략 구현 및 평가
- [ ] ArXiv 초안 업로드
- [ ] Workshop/Conference 투고

### 4.4 오픈소스 공개

- [ ] 라이선스: **AGPL v3.0**
- [ ] GitHub Public 전환
- [ ] Skill 배포 (폴더 공유)
- [ ] 벤치마크 데이터셋 공개

---

## 우선순위 매트릭스

| Phase | 핵심 목표 | 난이도 | 의존성 |
|-------|----------|--------|--------|
| **0** | 프로젝트 설정 | 낮음 | 없음 |
| **1** | Skill 구조 + Python 구현 | 중간 | Phase 0 |
| **2** | 플랫폼 지원 확장 | 낮음 | Phase 1 |
| **3** | Desktop/Mobile 확장 | 높음 | Phase 2 |
| **4** | 논문 + 공개 | 중간 | Phase 2 |

## 권장 구현 순서

```
┌─────────────────────────────────────────────────────────┐
│  1단계: Play 먼저 (PoC)                                 │
│  ─────────────────────                                  │
│  - Phase 0 + Phase 1.1~1.4                              │
│  - 수동 JSON 작성 + Play 실행                           │
│  - Record 없이 핵심 기능 검증                           │
│                                                         │
│  2단계: Play 안정화                                     │
│  ─────────────────────                                  │
│  - Transport 자동 선택 (SSE/WS/stdio)                   │
│  - 에러 복구 (resume, retry)                            │
│  - 변수 시스템 ({{step_id.field}} 등)                   │
│                                                         │
│  3단계: Record 추가                                     │
│  ─────────────────────                                  │
│  - Play가 안정화된 후 Record 프롬프트 작성              │
│  - Agent가 생성한 JSON이 Play에서 동작하는지 검증       │
│                                                         │
│  4단계: 플랫폼 확장                                     │
│  ─────────────────────                                  │
│  - Claude Code 외 다른 플랫폼 테스트                    │
│  - Config 감지 로직 검증                                │
└─────────────────────────────────────────────────────────┘
```

**핵심 원칙: Play가 먼저, Record는 나중에**

Record가 생성한 JSON이 Play에서 동작해야 의미가 있으므로,
Play의 안정성이 확보된 후 Record를 구현합니다.

---

## 마일스톤

| 마일스톤 | Phase | 완료 조건 |
|----------|-------|----------|
| **v0.1.0** | 0 | 프로젝트 설정, 문서 |
| **v0.2.0** | 1 | Skill 구조 완성, 시나리오 v2.1, play.py |
| **v0.3.0** | 2 | Claude Code에서 동작 |
| **v1.0.0** | 2 | 안정화, 문서화 완료 |
| **v1.1.0** | 3 | Desktop 지원 |
| **v1.2.0** | 3 | Mobile 지원 |
| **v2.0.0** | 4 | 오픈소스 공개, 논문 발표 |

---

## 현재 상태

### 기존 LuftPlay (TypeScript) - 참고용

- [x] Play Engine (`Executor` class) - Web 특화
- [x] JSON Scenario 파싱 및 검증 (v1.1)
- [x] Variable 치환 (`{{VAR}}`)
- [x] MCP 자동 감지 (claude-in-chrome, chrome-devtools)
- [x] Retry 로직 (`on_error: retry`)
- [x] `ref_hint` 기본 fallback

### Sandy (Python) - 새로 구현

- [ ] Python으로 Play 스크립트 재작성
- [ ] 시나리오 v2.1 (MCP Tool 범용 + 런타임 결과 참조)
- [ ] Output 추출 (JSONPath)
- [ ] Transport 자동 선택 (SSE/WS/stdio)
- [ ] Skill 구조 구현
- [ ] Record 프롬프트
- [ ] 에러 복구 (resume, retry, skip)
- [ ] 플랫폼 확장 (Claude Code, Gemini CLI, Codex)
- [ ] Desktop/Mobile 지원
- [ ] 성능 벤치마크
- [ ] 논문

---

## 참고 자료

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP GitHub](https://github.com/modelcontextprotocol)
- [Anthropic MCP Blog](https://www.anthropic.com/engineering/code-execution-with-mcp)

---

*Last updated: 2026-02-03*
