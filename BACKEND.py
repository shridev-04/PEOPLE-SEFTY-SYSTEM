from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
import requests
import os


# ==================================================
# APP
# ==================================================

app = FastAPI(
    title="Women Safety SOS Backend"
)


# ==================================================
# SETTINGS
# ==================================================

# ESP32 में भी यही API key है
ESP32_API_KEY = "SHRIDEV"

# Telegram Bot Token Render Environment Variable से आएगा
TELEGRAM_BOT_TOKEN = os.getenv(
    "8830694274:AAFPQGz5-BWPPDTVQWUA3PBNMN8wQ7p9vgI",
    ""
)

# तुम्हारा Telegram Chat ID
TELEGRAM_CHAT_ID = "6168018748"


# ==================================================
# GPS DATA
# ==================================================

class GPSData(BaseModel):

    device_id: str

    # True  = GPS fix available
    # False = GPS fix unavailable
    gps_valid: bool = False

    latitude: float = Field(
        default=0.0,
        ge=-90,
        le=90
    )

    longitude: float = Field(
        default=0.0,
        ge=-180,
        le=180
    )


# ==================================================
# HOME
# ==================================================

@app.get("/")
def home():

    return {
        "status": "online",
        "message": "Women Safety SOS Backend is running"
    }


# ==================================================
# TELEGRAM
# ==================================================

def send_telegram(gps: GPSData):

    if not TELEGRAM_BOT_TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing"
        )


    # ==================================================
    # GPS AVAILABLE
    # ==================================================

    if gps.gps_valid:

        map_link = (
            "https://www.google.com/maps/search/"
            f"?api=1&query="
            f"{gps.latitude},{gps.longitude}"
        )

        message = (
            "🚨 WOMEN SAFETY SOS 🚨\n\n"
            f"Device: {gps.device_id}\n"
            "Status: EMERGENCY\n\n"
            "📍 GPS LOCATION AVAILABLE\n\n"
            f"Latitude: {gps.latitude:.6f}\n"
            f"Longitude: {gps.longitude:.6f}\n\n"
            "🗺️ Google Maps:\n"
            f"{map_link}"
        )


    # ==================================================
    # GPS NOT AVAILABLE
    # ==================================================

    else:

        message = (
            "🚨 WOMEN SAFETY SOS 🚨\n\n"
            f"Device: {gps.device_id}\n"
            "Status: EMERGENCY\n\n"
            "⚠️ GPS LOCATION NOT AVAILABLE\n\n"
            "The SOS button was triggered, but "
            "the GPS module does not currently "
            "have a valid GPS fix.\n\n"
            "Please check the person's safety immediately."
        )


    # ==================================================
    # TELEGRAM API
    # ==================================================

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )


    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=15
    )


    if response.status_code != 200:

        raise RuntimeError(
            f"Telegram API error: {response.text}"
        )


    return True


# ==================================================
# ESP32 GPS / SOS ENDPOINT
# ==================================================

@app.post("/gps")
def receive_gps(
    gps: GPSData,
    x_api_key: str = Header(default="")
):

    # ==================================================
    # API KEY CHECK
    # ==================================================

    if x_api_key != ESP32_API_KEY:

        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )


    # ==================================================
    # SERVER LOG
    # ==================================================

    print()
    print("================================")
    print("🚨 SOS RECEIVED")
    print("================================")

    print(
        f"Device    : {gps.device_id}"
    )

    print(
        f"GPS Valid : {gps.gps_valid}"
    )


    if gps.gps_valid:

        print(
            f"Latitude  : {gps.latitude}"
        )

        print(
            f"Longitude : {gps.longitude}"
        )

    else:

        print(
            "GPS       : NO FIX"
        )

    print("================================")


    # ==================================================
    # SEND TELEGRAM
    # ==================================================

    try:

        send_telegram(gps)

        print(
            "✅ Telegram message sent"
        )


        return {
            "success": True,
            "message": "SOS sent to Telegram",
            "gps_valid": gps.gps_valid
        }


    except Exception as error:

        print(
            "❌ Telegram error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail="Telegram message failed"
        )