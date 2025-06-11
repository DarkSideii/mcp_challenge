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
    days: int = 3,
    units: str = "metric",
) -> str:
    """Fetch a multi-day weather forecast for a city."""
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

        # Get forecast data (every 3-hour step; 8 steps per day)
        resp = await client.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={
                "lat": lat,
                "lon": lon,
                "units": units,
                "cnt": days * 8,
                "appid": OPENWEATHER_KEY,
            },
        )
        resp.raise_for_status()
        forecast = resp.json()

    # Decide on the unit symbol
    symbol = "C" if units == "metric" else "F"

    lines = []
    for i in range(days):
        entry = forecast["list"][i * 8]             # pick the same time each day
        date = datetime.fromtimestamp(entry["dt"]).strftime("%Y-%m-%d")
        desc = entry["weather"][0]["description"].capitalize()
        temp = entry["main"]["temp"]                # actual temperature
        lines.append(f"{date}: {desc}, {temp}°{symbol}")

    return "\n".join(lines)

async def get_news_headlines_client(category: str, country: str | None = None, limit: int = 5,) -> str:
    """
    Return top headlines for a given category and country.
    """
    base = "https://newsapi.org/v2/top-headlines"
    query_parts = [f"apiKey={NEWS_API_KEY}", f"pageSize={limit}"]
    if country:
        query_parts.append(f"country={country}")
    if category:
        query_parts.append(f"category={category}")

    url = f"{base}?{'&'.join(query_parts)}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
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

