let recognitionOutput = document.getElementById('recognition_output');
let debugOutput = document.getElementById('debug_output');
let annotatedImageEl = document.getElementById('annotated_image');
let recognitionCounterEl = document.getElementById('recognition_counter');
let recognitionHistoryEl = document.getElementById('recognition_history');

let CURRENT_RECOGNITION_GENERATION = 0;
let CURRENT_RECOGNITION_COUNT = 0;
let RECOGNITION_MANAGER = recognitionOutput ? RecognitionManager(recognitionOutput) : null;

let SOCKET = null;

let logMessages = [];

const arrowPhrases = {
    "": " ",
    null: " ",
    " ": " ",
    "w": "increasing sharply",
    "e": "increasing",
    "d": "stable",
    "x": "decreasing",
    "z": "decreasing sharply"
};

const arrowSymbols = {
    "": " ",
    null: " ",
    " ": " ",
    "w": "🡑",
    "e": "🡕",
    "d": "🡒",
    "x": "🡖",
    "z": "🡓"
};

let currentConstraintTryNumber = null;
const constraintHierarchy = [
    {
        video: {
            facingMode: {
                exact: 'environment',
            },
        },
    },
    {
        video: {},
    }
];


function logDebug(data) {
    console.log(data);

    if (!debugOutput) {
        return;
    }

    message = document.createElement('div');
    message.innerText = "[" + new Date().toISOString() + "] " + data;

    logMessages.push(message);
    while (logMessages.length > 5) {
        var oldMessage = logMessages[0];
        logMessages.splice(0, 1);
        debugOutput.removeChild(oldMessage);
    }
    // utility for showing debug info on the page

    debugOutput.insertBefore(message, debugOutput.firstChild);
}

function translateArrows(value, addArrowPhrase = true) {
    value = value.trimLeft();
    let tokens = value.split(" ");
    let result = tokens[0];

    if (tokens.length > 1 && addArrowPhrase) {
        result = result + " " + arrowPhrases[tokens[1].toLowerCase()];
    }

    return result;
}

function runRecognitionFromCamera() {
    hookDrawingHandlers();
    startCameraStream();
    setInterval(sendCanvasToServer, 1000 * 1.0 / frameRateForSending);
}

function sendCanvasToServer(){
    canvasAsBase64withPreamble = saveCanvasToFrameBase64(STREAMED_CANVAS);
    canvasAsBase64 = canvasAsBase64withPreamble.split(',')[1];

    let img = document.getElementById("img1");
    img.src = canvasAsBase64withPreamble;

    SOCKET.emit("frame", {
        "image": canvasAsBase64,
        "input_id": (CURRENT_RECOGNITION_GENERATION + "")
    });
}


function startSocket() {
    SOCKET = io("/", {secure: 'https:' === location.protocol});

    // register handlers
    SOCKET.on("frame_result", function (data) {
        logDebug("frame_result: " + JSON.stringify(data));
    });

    SOCKET.on("recognition_result", function (data) {
        if ("recognition_history" in data) {
            var received_generation = data["current_image_metadata"]["input_id"];
            if (received_generation !== (CURRENT_RECOGNITION_GENERATION + "")) {
                return;
            }
            var history = data["recognition_history"];

            var maxHypothesis = null;
            var maxHypothesisValue = null;
            for (var hypothesis in history) {
                var currentValue = history[hypothesis];
                if (maxHypothesisValue == null || currentValue > maxHypothesisValue) {
                    maxHypothesis = hypothesis;
                    maxHypothesisValue = currentValue;
                }
            }

            if (maxHypothesisValue != null && maxHypothesisValue > 1) {
                RECOGNITION_MANAGER.setRecognizedValue(maxHypothesis);
            }

            if (recognitionHistoryEl) {
                recognitionHistoryEl.innerText = JSON.stringify(history);
            }
        } else {
            if (recognitionHistoryEl) {
                recognitionHistoryEl.innerText = "no history";
            }
        }

        var status = "undefined";
        var metadata = data["current_image_metadata"];
        if ("display_detected" in metadata) {
            if (metadata["display_detected"]) {
                status = "displayed";
            } else {
                status = "not_displayed";
            }
        }
        $(".display_indicator").removeClass("display_displayed");
        $(".display_indicator").removeClass("display_not_displayed");
        $(".display_indicator").removeClass("display_undefined");

        $(".display_indicator").addClass("display_" + status);

        if ("current_image_recognition" in data && data["current_image_recognition"] != null) {
            CURRENT_RECOGNITION_COUNT += 1;
        }

        if (recognitionCounterEl) {
            recognitionCounterEl.innerText = CURRENT_RECOGNITION_COUNT;
        }

        if (annotatedImageEl && "annotated_image" in metadata) {
            annotatedImageEl.src = "data:image/png;base64, " + metadata["annotated_image"];
        }

        logDebug("recognized: " + JSON.stringify(data));
    });
}

