# HTTP Transport 추가 완료 ✅

## 변경 사항

### 1. Config Schema 업데이트
**파일:** `nanobot/config/schema.py`

- `MCPServerConfig`에 `transport` 필드 추가 (기본값: "http")
- SSE와 HTTP 중 선택 가능

```python
class MCPServerConfig(BaseModel):
    enabled: bool = True
    transport: str = "http"  # "http" (default) or "sse"
    url: str = ""
    timeout: int = 30
    headers: dict[str, str] = Field(default_factory=dict)
    auto_reconnect: bool = True  # Only for SSE transport
```

### 2. MCP Client 재구현
**파일:** `nanobot/mcp/client.py` (88 lines → 214 lines)

**주요 변경:**
- HTTP와 SSE 모두 지원하는 통합 클라이언트
- Transport에 따라 다른 초기화 및 통신 방식 사용
- HTTP: JSON-RPC 2.0 over HTTP (httpx 사용)
- SSE: MCP SDK 사용 (기존 방식 유지)

**새로운 메서드:**
- `_initialize_http()` - HTTP transport 초기화
- `_initialize_sse()` - SSE transport 초기화 (기존)
- `_http_request()` - JSON-RPC HTTP 요청
- `_call_tool_http()` - HTTP로 도구 호출
- `_call_tool_sse()` - SSE로 도구 호출 (기존)

### 3. Manager 업데이트
**파일:** `nanobot/mcp/manager.py`

- `MCPClient` 생성 시 `transport` 파라미터 전달

### 4. 문서 업데이트
**파일:** `MCP_SETUP.md`

- HTTP transport 사용법 추가
- Transport 비교표 추가
- 설정 예시 업데이트

## HTTP vs SSE 비교

### HTTP Transport
**장점:**
- ✅ 추가 의존성 없음 (httpx는 이미 설치됨)
- ✅ Stateless - 구현이 단순
- ✅ 방화벽/프록시 친화적
- ✅ 자동 재연결 (각 요청이 독립적)

**단점:**
- ⚠️ 요청당 레이턴시 (연결 오버헤드)
- ⚠️ 스트리밍 응답 미지원 (현재)

### SSE Transport
**장점:**
- ✅ 지속적 연결 - 낮은 레이턴시
- ✅ 스트리밍 지원
- ✅ MCP SDK 공식 지원

**단점:**
- ⚠️ MCP SDK 의존성 필요
- ⚠️ 연결 관리 복잡도
- ⚠️ 재연결 로직 필요

## 설정 예시

### HTTP (권장)
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

### SSE
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

## 테스트 결과

### ✅ Import 테스트
- 업데이트된 MCPClient import 성공

### ✅ Transport 설정 테스트
- HTTP transport 설정 성공
- SSE transport 설정 성공
- 잘못된 transport 거부 확인

### ✅ 클라이언트 생성 테스트
- HTTP 클라이언트 생성 성공
- Transport 검증 정상 동작

## 코드 통계

- **client.py**: 88 lines → 214 lines (+126 lines)
- HTTP transport 구현으로 약 126줄 추가
- 전체적으로 명확하고 유지보수하기 쉬운 구조

## 구현 세부사항

### HTTP Transport - JSON-RPC 2.0

HTTP transport는 JSON-RPC 2.0 프로토콜을 사용합니다:

**초기화:**
```json
POST http://localhost:8080
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "nanobot", "version": "0.1.0"}
  }
}
```

**도구 목록:**
```json
POST http://localhost:8080
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**도구 호출:**
```json
POST http://localhost:8080
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {"path": "/tmp/test.txt"}
  }
}
```

### 에러 처리

- HTTP 에러: httpx.HTTPError 캐치
- JSON-RPC 에러: response에 "error" 필드 체크
- 타임아웃: httpx AsyncClient의 timeout 설정 사용

## 다음 단계 (선택사항)

1. **stdio transport 추가** - 로컬 subprocess 기반
2. **HTTP 스트리밍** - Server-Sent Events를 HTTP로도 지원
3. **Connection pooling** - HTTP 연결 재사용
4. **Retry logic** - 실패 시 재시도 메커니즘
5. **Health checks** - 서버 상태 주기적 확인

## 결론

✅ **HTTP transport 성공적으로 추가됨!**

이제 nanobot은:
- HTTP (기본, 권장) - 단순하고 안정적
- SSE (고급) - 낮은 레이턴시, 스트리밍

두 가지 transport 방식을 모두 지원하여 다양한 MCP 서버 환경에 대응할 수 있습니다.
