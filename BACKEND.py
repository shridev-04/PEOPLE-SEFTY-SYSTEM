from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import requests
import json
import logging
import traceback

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("women-safety")

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Women Safety SOS WSS Backend"
)

# =========================================================
# TELEGRAM CONFIG
# =========================================================

# यहां अपना नया BotFather token डालो
# पुराने exposed token का इस्तेमाल मत करना।
TELEGRAM_BOT_TOKEN = "8830694274:AAFPQGz5-BWPPDTVQWUA3PBNMN8wQ7p9vgI"

TELEGRAM_CHAT_ID = "6168018748"


# =========================================================
# HOME
# =========================================================

@app.get("/")
async def home():

    return {
        "status": "online",
        "message": "Women Safety SOS WSS Backend is running",
        "websocket": "/ws",
        "telegram_configured": (
            TELEGRAM_BOT_TOKEN !=
            "PASTE_NEW_BOTFATHER_TOKEN_HERE"
        )
    }


# =========================================================
# TELEGRAM SEND
# =========================================================

def send_telegram(data):

    if (
        not TELEGRAM_BOT_TOKEN
        or TELEGRAM_BOT_TOKEN ==
        "PASTE_NEW_BOTFATHER_TOKEN_HERE"
    ):
        raise RuntimeError(
            "Telegram Bot Token is not configured in BACKEND.py"
        )

    device_id = data.get(
        "device_id",
        "UNKNOWN"
    )

    gps_valid = bool(
        data.get(
            "gps_valid",
            False
        )
    )

    latitude = float(
        data.get(
            "latitude",
            0.0
        )
    )

    longitude = float(
        data.get(
            "longitude",
            0.0
        )
    )

    # =====================================================
    # GPS AVAILABLE
    # =====================================================

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

    # =====================================================
    # GPS NOT AVAILABLE
    # =====================================================

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

    # =====================================================
    # TELEGRAM API
    # =====================================================

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    logger.info("Sending SOS to Telegram...")

    try:

        response = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=20
        )

    except Exception as error:

        logger.error(
            "Telegram connection error: %s",
            str(error)
        )

        raise RuntimeError(
            f"Telegram connection error: {error}"
        )

    # =====================================================
    # TELEGRAM RESPONSE
    # =====================================================

    logger.info(
        "Telegram HTTP status: %s",
        response.status_code
    )

    logger.info(
        "Telegram response: %s",
        response.text
    )

    if response.status_code != 200:

        raise RuntimeError(
            "Telegram API error: "
            f"{response.status_code} "
            f"{response.text}"
        )

    return True


# =========================================================
# TEST TELEGRAM
# =========================================================

@app.get("/telegram-test")
async def telegram_test():

    logger.info("Telegram test started")

    test_data = {
        "device_id": "TEST_DEVICE",
        "gps_valid": False,
        "latitude": 0.0,
        "longitude": 0.0
    }

    try:

        send_telegram(test_data)

        return {
            "success": True,
            "message": "Telegram test message sent"
        }

    except Exception as error:

        logger.error(
            "Telegram test failed: %s",
            str(error)
        )

        return {
            "success": False,
            "message": "Telegram failed",
            "error": str(error)
        }


# =========================================================
# WSS
# =========================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()

    logger.info(
        "================================"
    )

    logger.info(
        "WSS CLIENT CONNECTED"
    )

    logger.info(
        "================================"
    )

    try:

        while True:

            # ---------------------------------------------
            # RECEIVE ESP32 MESSAGE
            # ---------------------------------------------

            message = await websocket.receive_text()

            logger.info(
                "MESSAGE RECEIVED: %s",
                message
            )

            # ---------------------------------------------
            # JSON
            # ---------------------------------------------

            try:

                data = json.loads(message)

            except json.JSONDecodeError:

                logger.error(
                    "Invalid JSON received"
                )

                await websocket.send_json({
                    "success": False,
                    "message": "Invalid JSON"
                })

                continue

            # ---------------------------------------------
            # SOS
            # ---------------------------------------------

            if data.get("event") == "SOS":

                logger.info(
                    "================================"
                )

                logger.info(
                    "🚨 SOS RECEIVED"
                )

                logger.info(
                    "Device: %s",
                    data.get(
                        "device_id",
                        "UNKNOWN"
                    )
                )

                logger.info(
                    "GPS Valid: %s",
                    data.get(
                        "gps_valid",
                        False
                    )
                )

                # -----------------------------------------
                # SEND TELEGRAM
                # -----------------------------------------

                try:

                    send_telegram(data)

                    logger.info(
                        "✅ TELEGRAM MESSAGE SENT"
                    )

                    await websocket.send_json({
                        "success": True,
                        "message": "SOS sent to Telegram"
                    })

                except Exception as error:

                    logger.error(
                        "❌ TELEGRAM FAILED: %s",
                        str(error)
                    )

                    logger.error(
                        traceback.format_exc()
                    )

                    await websocket.send_json({
                        "success": False,
                        "message": "Telegram failed",
                        "error": str(error)
                    })

            else:

                await websocket.send_json({
                    "success": True,
                    "message": "Message received"
                })

    except WebSocketDisconnect:

        logger.info(
            "WSS CLIENT DISCONNECTED"
        )

    except Exception as error:

        logger.error(
            "WebSocket error: %s",
            str(error)
        )

        logger.error(
            traceback.format_exc()
        )