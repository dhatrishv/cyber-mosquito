from flask import Flask, Response
import cv2

app = Flask(__name__)

camera = cv2.VideoCapture(0)

def frames():
    while True:
        ok, frame = camera.read()

        if not ok:
            continue

        ok, encoded = cv2.imencode(".jpg", frame)

        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + encoded.tobytes()
            + b"\r\n"
        )

@app.get("/")
def index():
    return "Cyber Mosquito camera server"

@app.get("/video")
def video():
    return Response(
        frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True,
    )
