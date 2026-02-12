# nanobot MCP Integration - Complete Guide

## 🎉 완성된 기능

nanobot이 이제 MCP (Model Context Protocol) 서버와 통신할 수 있습니다!

### ✅ 지원 기능

1. **HTTP Transport** (기본, 권장)
   - JSON-RPC 2.0 over HTTP
   - 의존성 없음 (httpx 내장)
   - Stateless, 간단함

2. **SSE Transport** (고급)
   - Server-Sent Events
   - MCP SDK 사용
   - 지속 연결, 낮은 레이턴시

3. **멀티 서버 지원**
   - 여러 MCP 서버 동시 연결
   - 서버별 독립 설정

4. **자동 도구 검색 및 등록**
   - MCP 서버의 도구를 자동으로 nanobot에 통합

---

## 🚀 빠른 시작

### 1. 테스트 서버 실행

```bash
# FastAPI 버전 (권장)
python test_mcp_server.py

# 또는 stdlib 버전 (의존성 없음)
python test_mcp_server_simple.py
```

### 2. nanobot 설정

`~/.nanobot/config.json`:
```json
{
  "tools": {
    "mcp": {
      "enabled": true,
      "servers": {
        "test": {
          "transport": "http",
          "url": "http://localhost:8080"
        }
      }
    }
  }
}
```

### 3. nanobot 실행

```bash
# MCP 도구 사용
nanobot agent -m "Use the echo tool to say Hello MCP!"
nanobot agent -m "Calculate 123 + 456 using the add tool"
nanobot agent -m "What time is it?"
```

---

## 📁 파일 구조

```
nanobot/
├── nanobot/
│   ├── mcp/                          # MCP client 모듈
│   │   ├── __init__.py              # (11 lines)
│   │   ├── client.py                # HTTP/SSE client (214 lines)
│   │   ├── manager.py               # 멀티 서버 관리 (107 lines)
│   │   └── tool_wrapper.py          # Tool 어댑터 (75 lines)
│   ├── config/schema.py             # MCPConfig 추가됨
│   └── agent/loop.py                # MCP 통합됨
│
├── test_mcp_server.py               # FastAPI 테스트 서버
├── test_mcp_server_simple.py        # stdlib 테스트 서버
│
├── MCP_SETUP.md                     # 설정 및 사용 가이드
├── MCP_TESTING_GUIDE.md             # 테스트 가이드
├── MCP_IMPLEMENTATION_SUMMARY.md    # 구현 요약
├── MCP_HTTP_TRANSPORT_UPDATE.md     # HTTP transport 추가 내역
└── README_MCP.md                    # 이 파일
```

---

## 🔧 설정 옵션

### HTTP Transport (권장)

```json
{
  "tools": {
    "mcp": {
      "enabled": true,
      "servers": {
        "my-server": {
          "transport": "http",
          "url": "http://localhost:8080",
          "timeout": 30,
          "headers": {
            "Authorization": "Bearer token123"
          }
        }
      }
    }
  }
}
```

### SSE Transport

```json
{
  "tools": {
    "mcp": {
      "enabled": true,
      "servers": {
        "my-server": {
          "transport": "sse",
          "url": "http://localhost:8080/sse",
          "timeout": 30,
          "auto_reconnect": true
        }
      }
    }
  }
}
```

---

## 🧪 테스트 결과

### ✅ 서버 테스트 (curl)

1. **Health Check**: ✅ 성공
   ```json
   {
     "status": "running",
     "tools_count": 5,
     "tools": ["echo", "add", "get_time", "reverse_string", "multiply"]
   }
   ```

2. **Initialize**: ✅ 성공
   ```json
   {
     "protocolVersion": "2024-11-05",
     "serverInfo": {"name": "test-mcp-server", "version": "1.0.0"}
   }
   ```

3. **Tools List**: ✅ 성공
   - 5개 도구 반환됨

4. **Tool Call (echo)**: ✅ 성공
   ```json
   {"content": [{"type": "text", "text": "Echo: Hello from nanobot!"}]}
   ```

5. **Tool Call (add)**: ✅ 성공
   ```json
   {"content": [{"type": "text", "text": "The sum of 123 and 456 is 579"}]}
   ```

6. **Tool Call (get_time)**: ✅ 성공
   ```json
   {"content": [{"type": "text", "text": "Current server time: 2026-02-12T..."}]}
   ```

---

## 📊 코드 통계

### MCP 모듈
- **총 407 lines**
  - client.py: 214 lines (HTTP + SSE)
  - manager.py: 107 lines
  - tool_wrapper.py: 75 lines
  - __init__.py: 11 lines

### 테스트 서버
- test_mcp_server.py: ~250 lines (FastAPI, 5 tools)
- test_mcp_server_simple.py: ~150 lines (stdlib, 3 tools)

---

## 🎯 제공되는 테스트 도구

### FastAPI 서버 (5개)
1. **echo** - 메시지 반환
2. **add** - 두 숫자 더하기
3. **get_time** - 현재 시간
4. **reverse_string** - 문자열 뒤집기
5. **multiply** - 두 숫자 곱하기

### stdlib 서버 (3개)
1. **echo**
2. **add**
3. **get_time**

---

## 📚 문서

| 파일 | 설명 |
|------|------|
| `MCP_SETUP.md` | 설정 및 사용 가이드 |
| `MCP_TESTING_GUIDE.md` | 테스트 가이드 (curl, nanobot) |
| `MCP_IMPLEMENTATION_SUMMARY.md` | 전체 구현 요약 |
| `MCP_HTTP_TRANSPORT_UPDATE.md` | HTTP transport 추가 |
| `README_MCP.md` | 이 파일 (종합 가이드) |

---

## 🔍 트러블슈팅

### Q: MCP 서버 시작이 안 됨
```bash
# FastAPI 설치
pip install fastapi uvicorn

# 또는 stdlib 버전 사용 (의존성 없음)
python test_mcp_server_simple.py
```

### Q: nanobot이 MCP 도구를 못 찾음
1. 서버 실행 확인: `curl http://localhost:8080/`
2. 로그 확인: `nanobot agent --logs -m "test"`
3. 설정 확인:
   - `mcp.enabled: true`
   - `transport: "http"`
   - `url: "http://localhost:8080"`

### Q: 도구 실행 실패
- 서버 터미널에서 에러 로그 확인
- curl로 직접 테스트
- 파라미터 형식 확인

---

## 🌟 다음 단계

### 실제 사용 시나리오

1. **파일 시스템 MCP 서버**
   ```json
   {
     "filesystem": {
       "transport": "http",
       "url": "http://localhost:8080"
     }
   }
   ```

2. **GitHub MCP 서버**
   ```json
   {
     "github": {
       "transport": "http",
       "url": "http://localhost:8081",
       "headers": {
         "Authorization": "Bearer ghp_..."
       }
     }
   }
   ```

3. **커스텀 MCP 서버**
   - `test_mcp_server.py`를 기반으로 커스터마이징
   - 원하는 도구 추가
   - 인증/인가 구현
   - 프로덕션 배포

---

## 🎉 결론

✅ **nanobot MCP 통합 완료!**

- HTTP/SSE 두 transport 지원
- 멀티 서버 지원
- 테스트 서버 제공
- 완전한 문서화
- 실전 테스트 완료

nanobot을 외부 MCP 서버와 연동하여 무한한 확장이 가능합니다! 🚀

---

## 📞 참고 자료

- MCP 프로토콜: https://modelcontextprotocol.io/
- JSON-RPC 2.0: https://www.jsonrpc.org/specification
- FastAPI: https://fastapi.tiangolo.com/
- nanobot: https://github.com/HKUDS/nanobot
