import os
import requests
from dotenv import load_dotenv

load_dotenv()
default_url = os.getenv("MCP_SERVER_URL")

def call_mcp_uri(uri: str, rpc_id: int = 1) -> str:
    payload = {
        "jsonrpc": "2.0",
        "method":  "call_tool",
        "params":  {"uri": uri},
        "id":       rpc_id,
    }
    resp = requests.post(default_url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["result"]["content"][0]["text"]

def get_weather_client(city: str, units: str = "metric") -> str:
    return call_mcp_uri(f"mcp://weather/current/{city}/{units}")

def get_forecast_client(city: str, days: int = 3, units: str = "metric") -> str:
    return call_mcp_uri(f"mcp://weather/forecast/{city}/{days}/{units}")

def get_news_headlines_client(category: str, country: str = None, limit: int = 5) -> str:
    uri = f"mcp://news/headlines/{category}"
    if country:
        uri += f"/{country}"
    uri += f"/{limit}"
    return call_mcp_uri(uri)

def search_web_client(query: str, num_results: int = 5) -> str:
    return call_mcp_uri(f"mcp://news/search/{query}/{num_results}")
