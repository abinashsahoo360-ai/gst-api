from flask import Flask, jsonify, request
import requests
import uuid
import base64
from asgiref.wsgi import WsgiToAsgi

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)

gstSessions = {}

# --------------------- EXISTING ROUTES ---------------------

@app.route("/api/v1/getCaptcha", methods=["GET"])
def getCaptcha():
    try:
        captcha_url = "https://services.gst.gov.in/services/captcha"
        session = requests.Session()
        sid = str(uuid.uuid4())

        # Load GST homepage (needed to generate session)
        session.get("https://services.gst.gov.in/services/searchtp")

        # Get captcha image
        captchaResponse = session.get(captcha_url)
        captchaBase64 = base64.b64encode(captchaResponse.content).decode("utf-8")

        gstSessions[sid] = {"session": session}

        return jsonify({
            "sessionId": sid,
            "image": "data:image/png;base64," + captchaBase64,
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/v1/getGSTDetails", methods=["POST"])
def getGSTDetails():
    try:
        sessionId = request.json.get("sessionId")
        GSTIN = request.json.get("GSTIN")
        captcha = request.json.get("captcha")

        sdata = gstSessions.get(sessionId)
        if sdata is None:
            return jsonify({"error": "Invalid session id"})

        session = sdata['session']

        payload = {
            "gstin": GSTIN,
            "captcha": captcha
        }

        response = session.post(
            "https://services.gst.gov.in/services/api/search/taxpayerDetails",
            json=payload
        )

        return jsonify(response.json())

    except Exception as e:
        return jsonify({"error": str(e)})

# --------------------- NEW ROUTE (DIRECT GST VERIFY) ---------------------

@app.route("/gst/verify/<gstin>", methods=["GET"])
def directGST(gstin):
    try:
        # Step 1: Get captcha and session
        captcha_url = "https://services.gst.gov.in/services/captcha"
        session = requests.Session()

        session.get("https://services.gst.gov.in/services/searchtp")
        captchaResponse = session.get(captcha_url)
        captchaBytes = captchaResponse.content

        # ------------ IMPORTANT ----------------
        # The captcha must be solved by you manually OR using an OCR API.
        # For testing, we return "Captcha Required".
        # ---------------------------------------

        return jsonify({
            "success": False,
            "message": "Captcha Required. Your current code cannot auto-solve GST captcha.",
            "note": "Use /api/v1/getCaptcha + /api/v1/getGSTDetails flow."
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# --------------------- RUN APP ---------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=5001)
