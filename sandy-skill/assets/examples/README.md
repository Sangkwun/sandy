# Sandy Scenario Examples

Sandy 시나리오 예시 모음. 단일 MCP 및 멀티 MCP 조합 패턴을 다룹니다.

## 목차

- [단일 MCP 예시](#단일-mcp-예시)
- [멀티 MCP 예시](#멀티-mcp-예시)
- [실행 방법](#실행-방법)
- [변수 사용법](#변수-사용법)

---

## 단일 MCP 예시

### Chrome DevTools

**파일**: `chrome-test.json`

브라우저 페이지 조회 및 스냅샷 캡처.

```json
{
  "steps": [
    { "tool": "mcp__chrome-devtools__list_pages" },
    { "tool": "mcp__chrome-devtools__navigate_page", "params": { "url": "https://example.com" } },
    { "tool": "mcp__chrome-devtools__take_snapshot" }
  ]
}
```

---

### Supabase Query

**파일**: `supabase-query.json`

데이터베이스 쿼리 및 결과 추출.

```json
{
  "variables": { "LIMIT": "10" },
  "steps": [
    {
      "id": "user_query",
      "tool": "mcp__supabase__query",
      "params": { "sql": "SELECT * FROM users LIMIT {{LIMIT}}" },
      "output": { "users": "$", "first_id": "$[0].id" }
    }
  ]
}
```

---

### Filesystem

**파일**: `filesystem-test.json`

파일 시스템 읽기/쓰기.

---

### Memory

**파일**: `memory-test.json`

지식 그래프 기반 메모리 저장/조회.

---

## 멀티 MCP 예시

### 1. GitHub Issue → Slack 알림

**파일**: `multi-mcp-github-slack.json`

**MCP 조합**: `github` → `slack`

**용도**: GitHub에 이슈 생성 후 Slack 채널에 알림

```json
{
  "version": "2.1",
  "metadata": { "name": "GitHub Issue to Slack" },
  "variables": {
    "REPO": "owner/repo",
    "ISSUE_TITLE": "",
    "ISSUE_BODY": "",
    "SLACK_CHANNEL": "#dev"
  },
  "steps": [
    {
      "step": 1,
      "id": "create_issue",
      "tool": "mcp__github__create_issue",
      "params": {
        "repo": "{{REPO}}",
        "title": "{{ISSUE_TITLE}}",
        "body": "{{ISSUE_BODY}}"
      },
      "output": {
        "number": "$.number",
        "url": "$.html_url"
      },
      "on_error": "stop"
    },
    {
      "step": 2,
      "tool": "mcp__slack__post_message",
      "params": {
        "channel": "{{SLACK_CHANNEL}}",
        "text": ":github: Issue #{{create_issue.number}} created\n{{create_issue.url}}"
      },
      "on_error": "skip"
    }
  ]
}
```

**실행**:
```bash
sandy play multi-mcp-github-slack.json \
  --var ISSUE_TITLE="Bug: Login fails" \
  --var ISSUE_BODY="Cannot login with valid credentials"
```

---

### 2. 웹 스크래핑 → DB 저장

**파일**: `multi-mcp-web-to-db.json`

**MCP 조합**: `chrome-devtools` → `supabase`

**용도**: 웹 페이지 스크래핑 후 결과를 데이터베이스에 저장

```json
{
  "version": "2.1",
  "metadata": { "name": "Web Scrape to Database" },
  "variables": {
    "TARGET_URL": "https://news.ycombinator.com"
  },
  "steps": [
    {
      "step": 1,
      "tool": "mcp__chrome-devtools__navigate_page",
      "params": { "url": "{{TARGET_URL}}" },
      "wait_after": 2.0
    },
    {
      "step": 2,
      "id": "snapshot",
      "tool": "mcp__chrome-devtools__take_snapshot",
      "output": { "content": "$" }
    },
    {
      "step": 3,
      "id": "screenshot",
      "tool": "mcp__chrome-devtools__take_screenshot",
      "params": { "filePath": "/tmp/scrape_screenshot.png" },
      "output": { "path": "$" }
    },
    {
      "step": 4,
      "tool": "mcp__supabase__query",
      "params": {
        "sql": "INSERT INTO scrape_logs (url, scraped_at) VALUES ('{{TARGET_URL}}', NOW())"
      }
    }
  ]
}
```

---

### 3. DB 리포트 → Slack

**파일**: `multi-mcp-db-report-slack.json`

**MCP 조합**: `supabase` → `slack`

**용도**: 데이터베이스 통계 조회 후 Slack에 일일 리포트 전송

```json
{
  "version": "2.1",
  "metadata": { "name": "Daily Database Report to Slack" },
  "variables": {
    "SLACK_CHANNEL": "#reports"
  },
  "steps": [
    {
      "step": 1,
      "id": "user_stats",
      "tool": "mcp__supabase__query",
      "params": {
        "sql": "SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as new_today FROM auth.users"
      },
      "output": {
        "total_users": "$[0].total",
        "new_users": "$[0].new_today"
      }
    },
    {
      "step": 2,
      "id": "order_stats",
      "tool": "mcp__supabase__query",
      "params": {
        "sql": "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as revenue FROM orders WHERE created_at > NOW() - INTERVAL '24 hours'"
      },
      "output": {
        "order_count": "$[0].count",
        "revenue": "$[0].revenue"
      }
    },
    {
      "step": 3,
      "tool": "mcp__slack__post_message",
      "params": {
        "channel": "{{SLACK_CHANNEL}}",
        "text": ":chart_with_upwards_trend: *Daily Report*\n\nUsers: {{user_stats.total_users}} ({{user_stats.new_users}} new)\nOrders: {{order_stats.order_count}}\nRevenue: ${{order_stats.revenue}}"
      }
    }
  ]
}
```

---

### 4. PR 리뷰 워크플로우

**파일**: `multi-mcp-pr-review-notify.json`

**MCP 조합**: `github` → `slack`

**용도**: PR 정보 조회, 리뷰 코멘트 추가, Slack 알림

```json
{
  "version": "2.1",
  "metadata": { "name": "PR Review Workflow" },
  "variables": {
    "REPO": "",
    "PR_NUMBER": "",
    "SLACK_CHANNEL": "#code-review"
  },
  "steps": [
    {
      "step": 1,
      "id": "pr_info",
      "tool": "mcp__github__get_pull_request",
      "params": {
        "repo": "{{REPO}}",
        "pull_number": "{{PR_NUMBER}}"
      },
      "output": {
        "title": "$.title",
        "author": "$.user.login",
        "url": "$.html_url",
        "additions": "$.additions",
        "deletions": "$.deletions"
      }
    },
    {
      "step": 2,
      "tool": "mcp__github__create_pull_request_review",
      "params": {
        "repo": "{{REPO}}",
        "pull_number": "{{PR_NUMBER}}",
        "event": "COMMENT",
        "body": "Stats: +{{pr_info.additions}}/-{{pr_info.deletions}}"
      },
      "on_error": "skip"
    },
    {
      "step": 3,
      "tool": "mcp__slack__post_message",
      "params": {
        "channel": "{{SLACK_CHANNEL}}",
        "text": ":eyes: *{{pr_info.title}}* by {{pr_info.author}}\n+{{pr_info.additions}}/-{{pr_info.deletions}}\n{{pr_info.url}}"
      }
    }
  ]
}
```

**실행**:
```bash
sandy play multi-mcp-pr-review-notify.json \
  --var REPO="myorg/myrepo" \
  --var PR_NUMBER="123"
```

---

### 5. 폼 제출 → DB 로깅

**파일**: `multi-mcp-form-submit-log.json`

**MCP 조합**: `chrome-devtools` → `supabase`

**용도**: 웹 폼 자동 입력/제출 후 데이터베이스에 기록

```json
{
  "version": "2.1",
  "metadata": { "name": "Form Submission with Logging" },
  "variables": {
    "FORM_URL": "",
    "USER_EMAIL": "",
    "USER_NAME": ""
  },
  "steps": [
    {
      "step": 1,
      "tool": "mcp__chrome-devtools__navigate_page",
      "params": { "url": "{{FORM_URL}}" },
      "wait_after": 1.5
    },
    {
      "step": 2,
      "tool": "mcp__chrome-devtools__take_snapshot",
      "output": { "snapshot": "$" }
    },
    {
      "step": 3,
      "tool": "mcp__chrome-devtools__fill_form",
      "params": {
        "elements": [
          { "uid": "email-input", "value": "{{USER_EMAIL}}" },
          { "uid": "name-input", "value": "{{USER_NAME}}" }
        ]
      }
    },
    {
      "step": 4,
      "tool": "mcp__chrome-devtools__click",
      "params": { "uid": "submit-button" },
      "wait_after": 2.0
    },
    {
      "step": 5,
      "tool": "mcp__chrome-devtools__take_screenshot",
      "params": { "filePath": "/tmp/form_result.png" }
    },
    {
      "step": 6,
      "tool": "mcp__supabase__query",
      "params": {
        "sql": "INSERT INTO form_submissions (email, name, submitted_at) VALUES ('{{USER_EMAIL}}', '{{USER_NAME}}', NOW())"
      }
    }
  ]
}
```

---

## 실행 방법

### 기본 실행

```bash
sandy play <scenario.json>
```

### 변수 지정

```bash
sandy play <scenario.json> --var KEY=value --var KEY2=value2
```

### 디버그 모드

```bash
sandy play <scenario.json> --debug
```

### Dry Run (실제 실행 없이 검증)

```bash
sandy play <scenario.json> --dry-run
```

### 특정 스텝만 실행

```bash
# 스텝 2부터 시작
sandy play <scenario.json> --start 2

# 스텝 3까지만 실행
sandy play <scenario.json> --end 3

# 스텝 2~4만 실행
sandy play <scenario.json> --start 2 --end 4
```

---

## 변수 사용법

### 정적 변수

시나리오 파일에서 정의, 실행 시 오버라이드 가능:

```json
{
  "variables": {
    "REPO": "default/repo",
    "CHANNEL": "#general"
  }
}
```

빈 값은 필수 입력:
```json
{
  "variables": {
    "TITLE": ""
  }
}
```

### 스텝 결과 참조

이전 스텝 결과를 다음 스텝에서 사용:

```json
{
  "steps": [
    {
      "step": 1,
      "id": "create_issue",
      "tool": "mcp__github__create_issue",
      "output": {
        "number": "$.number",
        "url": "$.html_url"
      }
    },
    {
      "step": 2,
      "tool": "mcp__slack__post_message",
      "params": {
        "text": "Issue #{{create_issue.number}}: {{create_issue.url}}"
      }
    }
  ]
}
```

### JSONPath 문법

| 패턴 | 설명 |
|-----|------|
| `$` | 전체 결과 |
| `$.field` | 최상위 필드 |
| `$.data.name` | 중첩 필드 |
| `$[0]` | 배열 첫 번째 요소 |
| `$[0].id` | 배열 첫 번째 요소의 id |

---

## MCP 서버 설정

시나리오에서 사용하는 모든 MCP 서버는 설정 파일에 정의되어야 합니다.

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_xxx" }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-slack"],
      "env": { "SLACK_TOKEN": "xoxb-xxx" }
    },
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server"],
      "env": { "SUPABASE_URL": "...", "SUPABASE_KEY": "..." }
    },
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-chrome-devtools"]
    }
  }
}
```

---

## 에러 처리

### on_error 옵션

| 값 | 동작 |
|----|------|
| `"stop"` | 실행 중단 (기본값) |
| `"skip"` | 다음 스텝으로 진행 |
| `"retry"` | 재시도 |

### 재시도 설정

```json
{
  "on_error": "retry",
  "retry": {
    "count": 3,
    "delay": 500
  }
}
```

---

## 조건부 실행

특정 조건에서만 스텝 실행:

```json
{
  "step": 3,
  "condition": "{{create_issue.number}} != \"\"",
  "tool": "mcp__slack__post_message"
}
```
