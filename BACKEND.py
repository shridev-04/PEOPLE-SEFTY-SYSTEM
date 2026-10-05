from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import requests
import os
import json

app = FastAPI(
    title="Women Safety SOS WSS Backend"
)

# ===============================
# CONFIG
# ===============================

TELEGRAM_BOT_TOKEN = os.getenv(
    "8830694274:AAFPQGz5-BWPPDTVQWUA3PBNMN8wQ7p9vgI",
    ""
)

TELEGRAM_CHAT_ID = "6168018748"


# ===============================
# HOME
# ===============================

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Women Safety SOS WSS Backend is running"
    }


# ===============================
# TELEGRAM
# ===============================

def send_telegram(data):

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing"
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

    # ---------------------------
    # GPS AVAILABLE
    # ---------------------------

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

    # ---------------------------
    # GPS NOT AVAILABLE
    # ---------------------------

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

    # ---------------------------
    # Telegram API
    # ---------------------------

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


# ===============================
# WSS WEBSOCKET
# ===============================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()

    print()
    print("================================")
    print("WSS CLIENT CONNECTED")
    print("================================")

    try:

        while True:

            # Receive message from ESP32
            message = await websocket.receive_text()

            print()
            print("================================")
            print("MESSAGE RECEIVED")
            print("================================")

            print(message)

            try:

                data = json.loads(message)

            except json.JSONDecodeError:

                print(
                    "❌ Invalid JSON received"
                )

                await websocket.send_json({
                    "success": False,
                    "message": "Invalid JSON"
                })

                continue


            # ===============================
            # CHECK SOS
            # ===============================

            if data.get("event") == "SOS":

                print()
                print("🚨 SOS RECEIVED")
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

                if data.get("gps_valid"):

                    print(
                        "Latitude:",
                        data.get(
                            "latitude"
                        )
                    )

                    print(
                        "Longitude:",
                        data.get(
                            "longitude"
                        )
                    )

                else:

                    print(
                        "GPS: NO FIX"
                    )


                # ===============================
                # SEND TELEGRAM
                # ===============================

                try:

                    send_telegram(data)

                    print(
                        "✅ Telegram message sent"
                    )

                    await websocket.send_json({
                        "success": True,
                        "message": "SOS sent to Telegram"
                    })

                except Exception as error:

                    print(
                        "❌ Telegram error:",
                        error
                    )

                    await websocket.send_json({
                        "success": False,
                        "message": "Telegram failed"
                    })


            else:

                # Normal response
                await websocket.send_json({
                    "success": True,
                    "message": "Message received"
                })


    except WebSocketDisconnect:

        print()
        print(
            "WSS CLIENT DISCONNECTED"
        )

    except Exception as error:

        print(
            "❌ WebSocket error:",
            error
        )