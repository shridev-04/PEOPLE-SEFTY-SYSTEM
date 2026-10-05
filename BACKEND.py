from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
import requests

app = FastAPI(title="Women Safety SOS Backend")


# =========================
# SETTINGS
# =========================

ESP32_API_KEY = "SHRIDEV"

TELEGRAM_BOT_TOKEN = "8830694274:AAFPQGz5-BWPPDTVQWUA3PBNMN8wQ7p9vgI"
TELEGRAM_CHAT_ID = "6168018748"


# =========================
# DATA FORMAT
# =========================

class GPSData(BaseModel):
    device_id: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


# =========================
# HOME ENDPOINT
# =========================

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Women Safety SOS Backend is running"
    }


# =========================
# TELEGRAM
# =========================

def send_telegram(latitude, longitude, device_id):

    map_link = (
        "https://www.google.com/maps/search/"
        f"?api=1&query={latitude},{longitude}"
    )

    message = (
        "🚨 WOMEN SAFETY SOS 🚨\n\n"
        f"Device: {device_id}\n"
        "Status: EMERGENCY\n\n"
        "📍 GPS LOCATION\n"
        f"Latitude: {latitude}\n"
        f"Longitude: {longitude}\n\n"
        f"🗺️ Google Maps:\n{map_link}"
    )

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=10
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)


# =========================
# GPS ENDPOINT
# =========================

@app.post("/gps")
def receive_gps(
    gps: GPSData,
    x_api_key: str = Header(default="")
):

    # ESP32 authentication
    if x_api_key != ESP32_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    print("\n==============================")
    print("🚨 SOS LOCATION RECEIVED")
    print("==============================")
    print(f"Device    : {gps.device_id}")
    print(f"Latitude  : {gps.latitude}")
    print(f"Longitude : {gps.longitude}")
    print("==============================")

    try:

        send_telegram(
            gps.latitude,
            gps.longitude,
            gps.device_id
        )

        print("✅ Telegram message sent")

        return {
            "success": True,
            "message": "Location sent to Telegram"
        }

    except Exception as error:

        print("❌ Telegram error:", error)

        raise HTTPException(
            status_code=500,
            detail="Telegram message failed"
        )