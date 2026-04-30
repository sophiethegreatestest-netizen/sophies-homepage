import requests
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

        # If running locally, let ipinfo auto-detect
        if ip == "127.0.0.1":
            ip = ""

        response = requests.get(f"https://ipinfo.io/{ip}/json")
        data = response.json()

        city = data.get("city", "New York")
        country = data.get("country", "US")
        return city, country

    except:
        pass

    return "New York", "US"  # fallback


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
    city, country = get_location_from_ip()
    weather_data = get_weather(city)
    news_articles = get_news(city, country)

    context = {
        "city": city,
        "country": country,
        "temp": round(weather_data['main']['temp'], 1) if weather_data else "N/A",
        "description": weather_data['weather'][0]['description'] if weather_data else "No data",
        "articles": news_articles,
    }

    return render_template('index.html', **context)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)