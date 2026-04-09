import requests
from flask import Flask, render_template, request

app = Flask(__name__)

WEATHER_API_KEY = 'YOUR_NEW_API_KEY_HERE'


# -----------------------------
# Get city from user's IP
# -----------------------------
def get_city_from_ip():
    try:
        # Get user's real IP address
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        # If running locally, this avoids using 127.0.0.1
        if ip == "127.0.0.1":
            ip = ""

        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()

        if data["status"] == "success":
            return data["city"]

    except:
        pass

    return "New York"  # fallback city


# -----------------------------
# Get weather from OpenWeather
# -----------------------------
def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=imperial"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()

    return None


# -----------------------------
# Home Route
# -----------------------------
@app.route('/')
def home():
    city = get_city_from_ip()
    weather_data = get_weather(city)

    context = {
        "city": city,
        "temp": round(weather_data['main']['temp'], 1) if weather_data else "N/A",
        "description": weather_data['weather'][0]['description'] if weather_data else "No data"
    }

    return render_template('index.html', **context)


if __name__ == "__main__":
    app.run(debug=True)