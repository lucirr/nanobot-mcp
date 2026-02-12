# MCP Server Testing Guide

nanobot과 MCP 서버 통신을 테스트하기 위한 가이드입니다.

## 제공되는 테스트 서버

### 1. test_mcp_server.py (FastAPI 버전 - 권장)

**특징:**
- ✅ FastAPI 기반 (현대적, 빠름)
- ✅ 자동 문서화 (Swagger UI)
- ✅ 5개의 테스트 도구 제공
- ✅ 상세한 로깅

**의존성:**
```bash
pip install fastapi uvicorn
```

**실행:**
```bash
python test_mcp_server.py
```

### 2. test_mcp_server_simple.py (stdlib 버전)

**특징:**
- ✅ Python 표준 라이브러리만 사용
- ✅ 의존성 없음
- ✅ 3개의 기본 테스트 도구
- ✅ 가볍고 간단함

**실행:**
```bash
python test_mcp_server_simple.py
```

## 테스트 절차

### Step 1: 테스트 서버 실행

**터미널 1에서:**
```bash
cd /Users/lucirr/workspace/nanobot

# FastAPI 버전 (권장)
python test_mcp_server.py

# 또는 stdlib 버전
python test_mcp_server_simple.py
```

서버가 시작되면 다음과 같은 메시지가 표시됩니다:
```
🚀 Starting Test MCP Server
Tools: 5 available
  - echo
  - add
  - get_time
  - reverse_string
  - multiply
🔥 Server running on http://localhost:8080
```

### Step 2: nanobot 설정

`~/.nanobot/config.json`에 다음 추가:

```json
{
  "tools": {
    "mcp": {
      "enabled": true,
      "servers": {
        "test": {
          "transport": "http",
          "url": "http://localhost:8080",
          "timeout": 30
        }
      }
    }
  }
}
```

### Step 3: nanobot으로 테스트

**터미널 2에서:**

```bash
# 1. MCP 도구 확인 (로그에서 확인)
nanobot agent --logs -m "hello"

# 2. Echo 테스트
nanobot agent -m "Use the echo tool to say 'Hello MCP!'"

# 3. 계산 테스트
nanobot agent -m "Use the add tool to calculate 123 + 456"

# 4. 시간 확인 테스트
nanobot agent -m "What time is it on the server?"

# 5. 문자열 뒤집기 테스트
nanobot agent -m "Reverse the string 'nanobot'"

# 6. 곱셈 테스트
nanobot agent -m "Multiply 7 and 8 using the multiply tool"
```

### Step 4: 서버 로그 확인

서버 터미널에서 다음과 같은 로그를 확인할 수 있습니다:

```
📨 Received: initialize
✅ Initialize: {...}
📨 Received: tools/list
✅ Tools listed: 5 tools
📨 Received: tools/call
🔧 Calling tool 'echo' with args: {'message': 'Hello MCP!'}
✅ Tool executed successfully
```

## 제공되는 테스트 도구

### FastAPI 버전 (5개 도구)

1. **echo** - 메시지를 그대로 반환
   ```
   Input: {"message": "Hello!"}
   Output: "Echo: Hello!"
   ```

2. **add** - 두 숫자 더하기
   ```
   Input: {"a": 10, "b": 20}
   Output: "The sum of 10 and 20 is 30"
   ```

3. **get_time** - 현재 서버 시간
   ```
   Input: {}
   Output: "Current server time: 2024-..."
   ```

4. **reverse_string** - 문자열 뒤집기
   ```
   Input: {"text": "hello"}
   Output: "Reversed: olleh"
   ```

5. **multiply** - 두 숫자 곱하기
   ```
   Input: {"x": 5, "y": 6}
   Output: "5 × 6 = 30"
   ```

### stdlib 버전 (3개 도구)

- echo
- add
- get_time

## 수동 테스트 (curl)

서버가 정상 동작하는지 curl로 직접 테스트할 수 있습니다:


### 1. Health Check
```bash
curl http://localhost:8080/
```

### 2. Initialize
```bash
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }'
```

### 3. List Tools
```bash
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

### 4. Call Tool (Echo)
```bash
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {"message": "Hello from curl!"}
    }
  }'
```

### 5. Call Tool (Add)
```bash
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "add",
      "arguments": {"a": 42, "b": 58}
    }
  }'
```

## 트러블슈팅

### 서버가 시작되지 않음

**FastAPI 버전:**
```bash
pip install fastapi uvicorn
```

**포트 충돌:**
```bash
# 다른 포트 사용
# test_mcp_server.py 마지막 줄 수정:
uvicorn.run(app, host="0.0.0.0", port=8081)
```

### nanobot이 MCP 도구를 찾지 못함

1. 서버가 실행 중인지 확인:
   ```bash
   curl http://localhost:8080/
   ```

2. nanobot 로그 확인:
   ```bash
   nanobot agent --logs -m "test"
   ```

3. config.json 확인:
   - `mcp.enabled: true`
   - `servers.test.url: "http://localhost:8080"`
   - `servers.test.transport: "http"`

### 도구 실행 실패

서버 로그를 확인하여 에러 메시지를 확인하세요.

## 다음 단계

테스트가 성공하면:

1. ✅ nanobot MCP client가 정상 작동함을 확인
2. ✅ 실제 MCP 서버 구축 가능
3. ✅ 커스텀 도구 추가 가능

실제 프로덕션 MCP 서버를 만들 때:
- 인증/인가 추가
- 에러 처리 강화
- 로깅 및 모니터링
- Rate limiting
- 보안 강화

## 참고 자료

- MCP 프로토콜: https://modelcontextprotocol.io/
- JSON-RPC 2.0: https://www.jsonrpc.org/specification
- FastAPI: https://fastapi.tiangolo.com/
