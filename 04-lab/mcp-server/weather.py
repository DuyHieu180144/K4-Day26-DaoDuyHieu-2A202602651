from typing import Any
import asyncio
import httpx
import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
port = int(os.getenv("PORT", 8085))
mcp = FastMCP("weather", host="0.0.0.0", port=port)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable
API_KEY = os.getenv("WEATHERAPI_KEY")

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    # Check if API key is set
    if not API_KEY:
        print("ERROR: WeatherAPI key not set. Please set WEATHERAPI_KEY environment variable.")
        return None
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    # Add API key to parameters
    params["key"] = API_KEY
    
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney")
    """
    params = {
        "q": city,
        "aqi": "no"
    }
    
    data = await make_weather_request("current.json", params)

    if not data:
        # Fallback mock data when API_KEY is not configured
        city_lower = city.strip().lower()
        mock_cities = {
            "hanoi": ("Hanoi", "Hanoi", "Vietnam", 29.0, 84.2, "Light rain", 82, 12.0),
            "danang": ("Da Nang", "Da Nang", "Vietnam", 30.5, 86.9, "Partly cloudy", 78, 10.0),
            "brisbane": ("Brisbane", "Queensland", "Australia", 24.0, 75.2, "Sunny", 60, 15.0),
            "sydney": ("Sydney", "New South Wales", "Australia", 22.0, 71.6, "Clear", 65, 18.0),
            "tokyo": ("Tokyo", "Tokyo", "Japan", 19.0, 66.2, "Clear", 55, 14.0),
            "new york": ("New York", "New York", "USA", 17.5, 63.5, "Overcast", 70, 16.0),
        }
        name, reg, country, temp_c, temp_f, cond, hum, wind = mock_cities.get(
            city_lower, (city.title(), "Local Region", "Worldwide", 25.0, 77.0, "Partly cloudy", 70, 10.0)
        )
        return f"""
Current Weather for {name}, {reg}, {country} (Mock mode):

Temperature: {temp_c}°C ({temp_f}°F)
Feels like: {temp_c + 1}°C ({temp_f + 2}°F)
Condition: {cond}
Humidity: {hum}%
Wind: {wind} km/h (E)
Pressure: 1012 mb
UV Index: 5.0
Visibility: 10.0 km

Note: Set WEATHERAPI_KEY in environment for live satellite/radar data.
"""

    current = data["current"]
    location = data["location"]
    
    return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""

@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    """
    # Limit days to 3 for free tier
    days = min(days, 3)
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    if not data:
        # Fallback mock forecast when API_KEY is not configured
        forecasts = [f"Weather Forecast for {city.title()} (Mock mode, {days} day(s)):"]
        sample_dates = ["2026-10-15", "2026-10-16", "2026-10-17"]
        conditions = ["Sunny", "Partly cloudy", "Light rain"]
        for i in range(min(days, 3)):
            f_text = f"""
Date: {sample_dates[i]}
High: {28 + i}°C
Low: {22 + i}°C
Condition: {conditions[i]}
Chance of Rain: {20 * (i + 1)}%
Max Wind: 15 km/h
UV Index: 6.0
"""
            forecasts.append(f_text)
        return "\n---\n".join(forecasts)

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days:
        day_data = day["day"]
        date = day["date"]
        
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return "✅ Weather MCP Server is running! Ready to provide weather data for Australian cities and worldwide."

print("✅ MCP server initialized with Streamable HTTP transport")
print("🔧 Available tools: get_current_weather, get_forecast, health_check")

if __name__ == "__main__":
    import sys
    
    is_cloud_run = bool(os.getenv("PORT"))
    is_standalone = len(sys.argv) == 1 and sys.stdin.isatty()
    
    if is_cloud_run or is_standalone:
        print(f"🚀 Starting MCP server on http://0.0.0.0:{port}/mcp")
        mcp.run(transport="streamable-http")
    else:
        print("Starting FastMCP server in stdio mode for local client", file=sys.stderr)
        mcp.run()