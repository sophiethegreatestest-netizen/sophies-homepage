import requests
import os
import time
from flask import Flask, render_template, request

app = Flask(__name__)

WEATHER_API_KEY = '15b2fac0366d9a684010f2a8f7e76306'
NEWS_API_KEY = '94fecc9221144ad48b4a2725b3e8e317'


# -----------------------------
# Get city from user's IP
# -----------------------------
def get_location_from_ip():
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        # X-Forwarded-For can be a comma-separated list, take the first (real) IP
        if ip:
            ip = ip.split(',')[0].strip()

        # If still local, clear it so ipinfo auto-detects
        if ip == "127.0.0.1":
            ip = ""

        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        data = response.json()

        city = data.get("city", "New York")
        country = data.get("country", "US")
        lat, lon = None, None
        if data.get("loc"):
            lat, lon = data["loc"].split(",")
        return city, country, lat, lon

    except:
        pass

    return "New York", "US", None, None  # fallback


# -----------------------------
# Get weather from OpenWeather
# -----------------------------
def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=imperial"
    response = requests.get(url)
    print(f"Weather status: {response.status_code}, Response: {response.json()}")

    if response.status_code == 200:
        return response.json()

    return None


# -----------------------------
# Get severe weather alerts
# (requires lat/lon via OpenWeather One Call API)
# -----------------------------
def get_severe_weather(lat, lon):
    if not lat or not lon:
        return []

    url = (
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,current"
        f"&appid={WEATHER_API_KEY}"
    )
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        alerts = data.get("alerts", [])
        return [{"event": a.get("event", "Alert"), "description": a.get("description", "")} for a in alerts]

    return []


# -----------------------------
# Get daily high/low temps + 3-day forecast
# -----------------------------
def get_daily_temps(city):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=imperial&cnt=24"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        items = data.get("list", [])

        # High/low from first 8 entries (~today)
        today_temps = [item["main"]["temp"] for item in items[:8]]
        temp_high = round(max(today_temps), 1) if today_temps else None
        temp_low  = round(min(today_temps), 1) if today_temps else None

        # Group by day to get avg temp per day
        from collections import defaultdict
        from datetime import datetime
        day_temps = defaultdict(list)
        for item in items:
            date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
            day_temps[date].append(item["main"]["temp"])

        sorted_days = sorted(day_temps.keys())
        forecast = []
        for day in sorted_days[:3]:
            avg = round(sum(day_temps[day]) / len(day_temps[day]), 1)
            forecast.append({"date": day, "avg": avg})

        return temp_high, temp_low, forecast

    return None, None, []


# -----------------------------
# Get news from NewsAPI
# -----------------------------
def get_news(city, country):
    country_code = country.lower()

    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?country={country_code}"
        f"&pageSize=6"
        f"&apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    print(f"News status: {response.status_code}, Response: {response.json()}")

    if response.status_code == 200:
        articles = response.json().get("articles", [])
        return [a for a in articles if a.get("title") and a.get("url")]

    return []


# -----------------------------
# Home Route
# -----------------------------
@app.route('/')
def home():
    city, country, lat, lon = get_location_from_ip()
    weather_data = get_weather(city)
    news_articles = get_news(city, country)
    severe_alerts = get_severe_weather(lat, lon)
    temp_high, temp_low, forecast = get_daily_temps(city)

    context = {
        "city": city,
        "country": country,
        "temp": round(weather_data['main']['temp'], 1) if weather_data else "N/A",
        "description": weather_data['weather'][0]['description'] if weather_data else "No data",
        "articles": news_articles,
        "severe_alerts": severe_alerts,
        "temp_high": temp_high if temp_high else "N/A",
        "temp_low": temp_low if temp_low else "N/A",
        "forecast": forecast,
        "updated_at": int(time.time()),
    }

    return render_template('index.html', **context)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)