import logging
from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from cachetools import TTLCache
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import uvicorn

from tools import (
    get_weather_client,
    get_forecast_client,
    get_news_headlines_client,
    search_web_client,
)


logging.basicConfig(level=logging.INFO)
app = FastAPI(title="MCP Challenge")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


cache = TTLCache(maxsize=100, ttl=300)


class TextContent(BaseModel):
    type: str
    text: str

class CallToolResult(BaseModel):
    content: List[TextContent]

class RPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: Optional[int]


@app.post("/mcp")
@limiter.limit("50/minute")
async def mcp(request: Request, rpc: RPCRequest):
    # Validate JSON-RPC envelope
    if rpc.jsonrpc != "2.0" or rpc.method.lower() != "call_tool":
        raise HTTPException(status_code=400, detail="Invalid JSON-RPC call")

    params = rpc.params or {}
    uri = params.get("uri")
    if not uri:
        raise HTTPException(status_code=400, detail="Missing 'uri' in params")

    # Parse mcp://<service>/<action>/[…]
    parsed = urlparse(uri)
    if parsed.scheme.lower() != "mcp":
        raise HTTPException(status_code=400, detail="URI must start with mcp://")

    service = parsed.netloc
    parts   = parsed.path.strip("/").split("/")
    action  = parts[0]
    args    = parts[1:]

    # Caching
    if uri in cache:
        result_text = cache[uri]
    else:
        # Dispatch
        if service == "weather" and action == "current":
            result_text = await get_weather_client(args[0])
        elif service == "weather" and action == "forecast":
            result_text = await get_forecast_client(args[0], int(args[1]))
        elif service == "news" and action == "headlines":
            result_text = await get_news_headlines_client(args[0], args[1])
        elif service == "news" and action == "search":
            result_text = await search_web_client(args[0])
        else:
            raise HTTPException(status_code=404, detail=f"Unknown MCP URI: {uri}")

        cache[uri] = result_text

    # Wrap and return
    content = [TextContent(type="text", text=result_text)]
    result  = CallToolResult(content=content).dict()

    return {
        "jsonrpc": "2.0",
        "id":      rpc.id,
        "result":  result,
    }

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)