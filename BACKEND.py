from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import requests
import os
import json

app = FastAPI(
    title="Women Safety SOS WSS Backend"
)

# =========================================================
# CONFIGURATION
# =========================================================

# Render Environment Variable से Telegram Bot Token पढ़ेगा
TELEGRAM_BOT_TOKEN = os.getenv(
    "8830694274:AAFPQGz5-BWPPDTVQWUA3PBNMN8wQ7p9vgI",
    ""
)

# आपका Telegram Chat ID
TELEGRAM_CHAT_ID = "6168018748"


# =========================================================
# HOME / HEALTH CHECK
# =========================================================

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Women Safety SOS WSS Backend is running"
    }


# =========================================================
# TELEGRAM MESSAGE
# =========================================================

def send_telegram(data):

    # Token मौजूद है या नहीं
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing in Render Environment Variables"
        )

    device_id = data.get(
        "device_id",
        "UNKNOWN"
    )

    gps_valid = data.get(
        "gps_valid",
        False
    )

    latitude = data.get(
        "latitude",
        0.0
    )

    longitude = data.get(
        "longitude",
        0.0
    )

    # -----------------------------------------------------
    # GPS AVAILABLE
    # -----------------------------------------------------

    if gps_valid:

        map_link = (
            "https://www.google.com/maps/search/"
            f"?api=1&query={latitude},{longitude}"
        )

        message = (
            "🚨 WOMEN SAFETY SOS 🚨\n\n"
            f"Device: {device_id}\n"
            "Status: EMERGENCY\n\n"
            "📍 GPS LOCATION AVAILABLE\n\n"
            f"Latitude: {latitude:.6f}\n"
            f"Longitude: {longitude:.6f}\n\n"
            "🗺️ Google Maps:\n"
            f"{map_link}"
        )

    # -----------------------------------------------------
    # GPS NOT AVAILABLE
    # -----------------------------------------------------

    else:

        message = (
            "🚨 WOMEN SAFETY SOS 🚨\n\n"
            f"Device: {device_id}\n"
            "Status: EMERGENCY\n\n"
            "⚠️ GPS LOCATION NOT AVAILABLE\n\n"
            "SOS button was triggered, but "
            "the GPS module does not currently "
            "have a valid GPS fix.\n\n"
            "Please check the person's safety immediately."
        )

    # -----------------------------------------------------
    # TELEGRAM API URL
    # -----------------------------------------------------

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    # -----------------------------------------------------
    # SEND MESSAGE
    # -----------------------------------------------------

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=15
    )

    # -----------------------------------------------------
    # ERROR DEBUGGING
    # -----------------------------------------------------

    if response.status_code != 200:

        print(
            "❌ TELEGRAM STATUS:",
            response.status_code
        )

        print(
            "❌ TELEGRAM RESPONSE:",
            response.text
        )

        raise RuntimeError(
            f"Telegram API error: "
            f"{response.status_code} "
            f"{response.text}"
        )

    print("✅ Telegram API response:", response.text)

    return True


# =========================================================
# WSS WEBSOCKET
# =========================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()

    print()
    print("================================")
    print("✅ WSS CLIENT CONNECTED")
    print("================================")

    try:

        while True:

            # ------------------------------------------------
            # RECEIVE MESSAGE FROM ESP32
            # ------------------------------------------------

            message = await websocket.receive_text()

            print()
            print("================================")
            print("📥 MESSAGE RECEIVED")
            print("================================")

            print(message)

            # ------------------------------------------------
            # JSON PARSE
            # ------------------------------------------------

            try:

                data = json.loads(message)

            except json.JSONDecodeError:

                print("❌ Invalid JSON received")

                await websocket.send_json({
                    "success": False,
                    "message": "Invalid JSON"
                })

                continue

            # ------------------------------------------------
            # CHECK SOS EVENT
            # ------------------------------------------------

            if data.get("event") == "SOS":

                print()
                print("================================")
                print("🚨 SOS RECEIVED")
                print("================================")

                print(
                    "Device:",
                    data.get(
                        "device_id",
                        "UNKNOWN"
                    )
                )

                print(
                    "GPS Valid:",
                    data.get(
                        "gps_valid",
                        False
                    )
                )

                # --------------------------------------------
                # GPS INFORMATION
                # --------------------------------------------

                if data.get("gps_valid"):

                    print(
                        "Latitude:",
                        data.get("latitude")
                    )

                    print(
                        "Longitude:",
                        data.get("longitude")
                    )

                else:

                    print(
                        "GPS: NO FIX"
                    )

                # --------------------------------------------
                # SEND TELEGRAM
                # --------------------------------------------

                try:

                    send_telegram(data)

                    print()
                    print(
                        "================================"
                    )
                    print(
                        "✅ TELEGRAM MESSAGE SENT"
                    )
                    print(
                        "================================"
                    )

                    await websocket.send_json({
                        "success": True,
                        "message": "SOS sent to Telegram"
                    })

                except Exception as error:

                    print()
                    print(
                        "================================"
                    )
                    print(
                        "❌ TELEGRAM ERROR"
                    )
                    print(
                        "================================"
                    )

                    print(
                        str(error)
                    )

                    await websocket.send_json({
                        "success": False,
                        "message": "Telegram failed"
                    })

            else:

                # ------------------------------------------------
                # NORMAL MESSAGE
                # ------------------------------------------------

                await websocket.send_json({
                    "success": True,
                    "message": "Message received"
                })

    except WebSocketDisconnect:

        print()
        print(
            "⚠️ WSS CLIENT DISCONNECTED"
        )

    except Exception as error:

        print()
        print(
            "❌ WebSocket error:",
            str(error)
        )