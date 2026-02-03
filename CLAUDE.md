# Sandy - MCP Scenario Player

## Project Overview

Sandy는 MCP(Model Context Protocol) 도구 호출 시퀀스를 기록하고 재생하는 **결정론적 워크플로우 자동화 도구**입니다. LLM 추론 없이 정확한 도구 호출을 재생하여 토큰 비용과 지연 시간을 대폭 절감합니다.

**핵심 가치:**
- LLM 없이 MCP 도구 호출을 결정론적으로 재생
- 반복 작업의 토큰 비용 절감
- CI/CD 파이프라인 및 회귀 테스트에 적합

## Tech Stack

- **Language**: Python 3.14
- **Core Dependencies**:
  - `mcp>=1.0.0` - MCP Python SDK
  - `websockets>=12.0` - WebSocket 지원
  - `jsonpath-ng>=1.6.0` - JSONPath 출력 추출
  - `python-dotenv>=1.0.0` - 환경 변수 로드

## Project Structure

```
sandy/
├── sandy-skill/                    # 메인 플러그인/CLI 구현
│   ├── .claude-plugin/
│   │   └── plugin.json            # Claude Code 플러그인 매니페스트
│   ├── .sandy/
│   │   └── config.json            # MCP 서버 설정
│   ├── skills/sandy/
│   │   └── sandy.md               # Skill 명세 (Claude Code용)
│   ├── scripts/                   # 핵심 Python 구현
│   │   ├── play.py               # CLI 진입점
│   │   ├── player.py             # 시나리오 실행기
│   │   ├── scenario.py           # 시나리오 파서 & 검증기
│   │   ├── config.py             # 설정 자동 감지
│   │   ├── reporter.py           # 결과 포매팅
│   │   └── clients/              # MCP 전송 구현체
│   │       ├── base.py           # 추상 베이스 클래스
│   │       ├── stdio_client.py   # stdio 전송
│   │       ├── sse_client.py     # SSE 전송
│   │       ├── websocket_client.py
│   │       └── socket_client.py  # Unix 소켓
│   ├── assets/examples/          # 예제 시나리오
│   ├── references/schema.md      # JSON 스키마 문서
│   └── tests/                    # 유닛 테스트
└── README.md
```

## Key Components

| 컴포넌트 | 파일 | 책임 |
|---------|------|------|
| CLI Entry | `play.py` | 인자 파싱, 설정/시나리오 로드, 실행 조율 |
| Scenario Executor | `player.py` | 단계 실행, 변수 치환, 출력 추출, 에러 처리 |
| Scenario Parser | `scenario.py` | JSON 파싱, 검증, v1.1→v2.1 변환 |
| Config Manager | `config.py` | 여러 소스에서 MCP 설정 자동 감지 |
| Reporter | `reporter.py` | 결과 포매팅 (콘솔, JSON) |
| MCP Clients | `clients/` | 전송별 구현 (stdio, SSE, WebSocket, socket) |

## Architecture & Patterns

### 실행 흐름

```
CLI Input → parse arguments → load scenario → detect config
    → create player → execute steps → format result → report
```

### 시나리오 JSON 포맷 (v2.1)

```json
{
  "version": "2.1",
  "metadata": { "name": "...", "description": "..." },
  "variables": { "VAR_NAME": "default" },
  "steps": [
    {
      "step": 1,
      "id": "unique_id",
      "tool": "mcp__server__tool_name",
      "params": { ... },
      "output": { "field": "$.json.path" },
      "on_error": "stop|skip|retry"
    }
  ]
}
```

### 변수 치환 시스템

| 패턴 | 설명 | 예시 |
|------|------|------|
| `{{VAR}}` | 정적 변수 | `"title": "{{TITLE}}"` |
| `{{step_id.field}}` | 이전 단계 출력 참조 | `"text": "Issue #{{create.number}}"` |
| JSONPath | 출력 추출 | `"items": "$[*].id"` |

### MCP 도구 네이밍

형식: `mcp__<server>__<tool_name>`
- `mcp__github__create_issue`
- `mcp__chrome-devtools__click`
- `mcp__supabase__query`

### Sandy 내장 도구

`sandy__` 접두사로 MCP 서버 없이 사용:
- `sandy__wait` - 대기
- `sandy__log` - 로그 출력
- `sandy__append_file` - JSONL/CSV/JSON 저장
- `sandy__wait_for_element` - CSS 선택자 대기
- `sandy__wait_until` - JavaScript 표현식 대기

### 에러 처리 전략

단계별 에러 모드:
- `"stop"` - 실행 중단 (기본값)
- `"skip"` - 다음 단계로 진행
- `"retry"` - 지수 백오프로 재시도

### 전송 추상화 패턴

`MCPClient` 추상 클래스와 구현체:
1. **StdioClient** - 서브프로세스 stdin/stdout
2. **SSEClient** - HTTP SSE
3. **WebSocketClient** - WebSocket
4. **SocketClient** - Unix 도메인 소켓

팩토리 패턴으로 설정에 따라 자동 선택.

## Development Guidelines

### 테스트 실행

```bash
cd sandy-skill
pytest tests/
```

### 설정 자동 감지 우선순위

1. `$SANDY_CONFIG` 환경 변수
2. `.sandy/config.json` (프로젝트 로컬)
3. Claude Desktop 설정
4. Cursor 설정 (`~/.cursor/mcp.json`)
5. `~/.sandy/config.json` (글로벌 사용자 설정)

### 하위 호환성

v1.1 시나리오(`action` 필드 사용)는 v2.1로 자동 변환됨.

## Code Conventions

- **Type Safety**: dataclass로 타입 정의 (`Step`, `Scenario`, `StepResult`, `PlayResult` 등)
- **변수명**: snake_case 사용
- **파일당 하나의 책임**: 각 모듈은 단일 책임 원칙 준수
- **JSONPath 사용**: `jsonpath-ng` 라이브러리로 결과 파싱

## Important Notes

- 새 MCP 도구 추가 시 `clients/` 디렉토리의 전송 구현체 확인
- 시나리오 스키마 변경 시 `references/schema.md` 업데이트 필요
- 플러그인 버전 변경 시 `plugin.json` 업데이트
- 예제 시나리오는 `assets/examples/`에 위치
