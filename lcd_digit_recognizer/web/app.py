import base64
import gc
import json
import os
import threading
import time
import traceback
from multiprocessing import freeze_support

from pympler import muppy, summary

import eventlet


eventlet.monkey_patch()

import numpy as np

import cv2
from flask import Flask, render_template, make_response, request
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO, send, emit, join_room

from lcd_digit_recognizer.web.recognition_service import RecognitionService

this_file_dir_path = os.path.dirname(os.path.realpath(__file__))

HTTP_PORT = 7894
HISTORY_DIR = "/tmp/cupr_history"
MAX_HISTORY_LENGTH = 1000

# run env initialization
RECOGNITION_SERVICE = None  # will be initialized later (due to process forking interference with flask)
os.makedirs(HISTORY_DIR, exist_ok=True)

# prepare server
app = Flask(__name__)
app.secret_key = b'effer234\n\xec]/'
Bootstrap(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


@app.route("/nocamera")
def nocamera():
    return render_template("nocamera.html")


@app.route("/static/<static_file>.css")
def dynamic_css(static_file):
    path = os.path.join(this_file_dir_path, f"static/{static_file}.css")
    with open(path) as f:
        r = make_response(f.read())
        r.headers["Content-type"] = "text/css"

    return r

@app.route("/static/<static_file>.js")
def dynamic_js(static_file):
    path = os.path.join(this_file_dir_path, f"static/{static_file}.js")
    with open(path) as f:
        r = make_response(f.read())
        r.headers["Content-type"] = "text/javascript"

    return r


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/camera_debug")
def camera_debug():
    return render_template("camera_debug.html")


@app.route("/history_filler")
def history_filler():
    return render_template("history_filler.html")

@app.route("/history")
def image_history():
    return render_template("history.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/recognition_history")
def recognition_history():
    result = []
    for file_name in os.listdir(HISTORY_DIR):
        if file_name.endswith(".rcg"):
            result.append(file_name[:-4])

    result.sort()
    result.reverse()
    return render_template("recognition_history.html", ids=result)


@app.route("/show_image/<id>")
def show_image(id):
    with open(f"{HISTORY_DIR}/{id}.png", "br") as f:
        image_binary = f.read()

    response = make_response(image_binary)
    response.headers.set("Content-Type", "image/png")
    return response


@app.route("/show_recognition_json/<id>")
def show_recognition_json(id):
    try:
        with open(f"{HISTORY_DIR}/{id}.rcg", "r") as f:
            recognition_json = f.read()
    except Exception:
        return json.dumps({
            "exception": traceback.format_exc()
        })

    response = make_response(recognition_json)
    response.headers.set("Content-Type", "application/json")
    return response

@app.route("/show_recognition/<id>")
def show_recognition(id):
    with open(f"{HISTORY_DIR}/{id}.rcg", "r") as f:
        recognized_number = f.read()

    return render_template("show_recognition.html", recognized_number=recognized_number, id=id)


@socketio.on("clear_history")
def handle_clear_history(message):
    sid = request.sid
    RECOGNITION_SERVICE.close_context(sid)

@socketio.on("frame")
def handle_frame(message):
    try:
        sid = request.sid

        image_bytes = base64.b64decode(message["image"])
        input_id = message.get("input_id", None)
        timestamp = time.time()
        server_image_id = str(timestamp)

        nparr = np.fromstring(image_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_np is None or len(img_np) == 0:
            raise AssertionError("Image could not be load correctly (probably incorrect format)")

        RECOGNITION_SERVICE.add_job(sid, server_image_id, img_np, input_id)

        output_path = f"{HISTORY_DIR}/{server_image_id}.png"
        cv2.imwrite(output_path, img_np)

        emit("frame_result", {
            "code": "ok",
            "input_id": input_id,
            "server_image_id": server_image_id,
            "sid": sid,
        })
    except Exception as e:
        emit("frame_result", {
            "code": "failed",
            "error": str(e),
            "input": message
        })


@socketio.on('connect')
def handle_connect():
    print('Client connected ' + request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print('Client disconnected ' + sid)
    RECOGNITION_SERVICE.close_context(sid)


@app.route("/.well-known/acme-challenge/<name>")
def cert(name):
    if "/" in name:
        # prevent file leaks
        return "Invalid path"

    with open(f"/tmp/.well-known/acme-challenge/{name}") as f:
        return f.read()


def report_recognition(sid, image_id, result):
    with open(os.path.join(HISTORY_DIR, image_id + ".rcg"), "w") as f:
        f.write(str(result))

    socketio.emit("recognition_result", result, room=sid)


def run_history_cleaner():
    gc.collect()
    all_objects = muppy.get_objects()
    sum1 = summary.summarize(all_objects)
    # Prints out a summary of the large objects
    summary.print_(sum1)

    remove_files(".png")
    remove_files(".rcg")

    threading.Timer(60, run_history_cleaner).start()


def remove_files(extension):
    file_paths = []
    for name in os.listdir(HISTORY_DIR):
        if not name.endswith(extension):
            continue

        file_paths.append(os.path.join(HISTORY_DIR, name))
    file_paths.sort()
    while len(file_paths) > MAX_HISTORY_LENGTH:
        path_to_delete = file_paths.pop(0)
        os.unlink(path_to_delete)


@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response


def print_banner(http_port):
    print("Today's menu:")
    print()
    print("    http://localhost:{}/".format(str(http_port)))
    print("    http://localhost:{}/camera_debug".format(str(http_port)))
    print("    http://localhost:{}/nocamera".format(str(http_port)))
    print("    http://localhost:{}/history".format(str(http_port)))
    print("    http://localhost:{}/history_filler".format(str(http_port)))
    print("    http://localhost:{}/recognition_history".format(str(http_port)))
    print("")


if __name__ == "__main__":
    freeze_support()
    run_history_cleaner()

    if "DEBUG_MODE" in os.environ:
        use_reloader = True
        debug = True
        start_recognition = False
    else:
        use_reloader = False
        debug = False
        start_recognition = True

    RECOGNITION_SERVICE = RecognitionService(recognition_callback=report_recognition)
    if start_recognition:
        RECOGNITION_SERVICE.start()


    print_banner(HTTP_PORT)
    socketio.run(app, host='0.0.0.0', port=HTTP_PORT, use_reloader=use_reloader, debug=debug)

