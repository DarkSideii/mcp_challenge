import os
import httpx
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Ensure API keys are present
if not OPENWEATHER_KEY:
    raise RuntimeError("Missing OPENWEATHER_API_KEY in environment")
if not NEWS_API_KEY:
    raise RuntimeError("Missing NEWS_API_KEY in environment")

async def get_weather_client(city: str, units: str = "metric") -> str:
    """Fetch current weather for a given city."""
    async with httpx.AsyncClient() as client:
        # Geocode city to coordinates
        resp = await client.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": city, "limit": 1, "appid": OPENWEATHER_KEY},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return f"City '{city}' not found"
        lat, lon = data[0]["lat"], data[0]["lon"]

        # Get current weather
        resp = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": lat, "lon": lon, "units": units, "appid": OPENWEATHER_KEY},
        )
        resp.raise_for_status()
        w = resp.json()

    desc = w["weather"][0]["description"].capitalize()
    temp = w["main"]["temp"]
    symbol = "C" if units == "metric" else "F"
    return f"{desc}, {temp}°{symbol}"

async def get_forecast_client(
    city: str,
    days: int,
    units: str = "metric",
) -> str:
    """
    Fetch a multi-day weather forecast for a city using One Call API 3.0.
    `days` must be between 2 and 8 inclusive.
    """
    # --- validate days ---
    if days < 2 or days > 8:
        return "Error: `days` parameter must be between 2 and 8."

    async with httpx.AsyncClient() as client:
        # Geocode city to coordinates
        resp = await client.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": city, "limit": 1, "appid": OPENWEATHER_KEY},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return f"City '{city}' not found"
        lat, lon = data[0]["lat"], data[0]["lon"]

        # One Call 3.0: daily forecasts (up to 8 days)
        resp = await client.get(
            "https://api.openweathermap.org/data/3.0/onecall",
            params={
                "lat": lat,
                "lon": lon,
                "units": units,
                "exclude": "current,minutely,hourly,alerts",
                "appid": OPENWEATHER_KEY,
            },
        )
        resp.raise_for_status()
        o = resp.json()

    # Format the next N days out of `daily`
    symbol = "C" if units == "metric" else "F"
    lines = []
    for entry in o.get("daily", [])[:days]:
        date = datetime.fromtimestamp(entry["dt"]).strftime("%Y-%m-%d")
        desc = entry["weather"][0]["description"].capitalize()
        temp = entry["temp"]["day"]
        lines.append(f"{date}: {desc}, {temp}°{symbol}")
    return "\n".join(lines)

async def get_news_headlines_client(category: str, country: str | None = None, limit: int = 5) -> str:
    """
    Return top headlines for a given category and optional country.
    """
    base = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey":   NEWS_API_KEY,
        "pageSize": limit,
        "category": category,
    }
    if country:
        params["country"] = country

    async with httpx.AsyncClient() as client:
        resp = await client.get(base, params=params)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])

    if not articles:
        return "No headlines found."
    return "\n".join(f"- {a['title']} ({a['url']})" for a in articles[:limit])

async def search_web_client(query: str, num_results: int = 5) -> str:
    """
    Perform an asynchronous DuckDuckGo search using LangChain's DuckDuckGoSearchAPIWrapper.
    """
    # Initialize the wrapper with desired settings
    wrapper = DuckDuckGoSearchAPIWrapper(
        region="wt-wt",  # default global region
        time="d",  # results from the past day
        max_results=num_results,
        source="text"  # plain text search
    )
    # Perform async search
    return wrapper.run(query)

