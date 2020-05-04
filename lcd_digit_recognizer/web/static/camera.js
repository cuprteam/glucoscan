let frameRateForSending = 3;
let frameQuality = 0.5;
let frameContentType = "image/jpeg";

let resizingRatio = 2.0;

let width = 1920 / resizingRatio;
let height = 1080 / resizingRatio;
let smallerSideFixedCanvas = 432;


let VIDEO_SOURCE = document.querySelector('video');
let STREAMED_CANVAS = document.querySelector('canvas');


function getSmallerSide(width, height) {
    if (width <= height) {
        return "width";
    } else
        return "height";
}

function draw(video, canvas, context, frameRateForSending) {
    let width = video.videoWidth;
    let height = video.videoHeight;

    if (getSmallerSide(width, height) === "height") {
        // landscape mode:
        // console.log("Landscape mode ");
        canvas.height = smallerSideFixedCanvas;

        // fill vertically
        var canvasComputedWidth = (canvas.height / video.videoHeight) * video.videoWidth;
        canvas.width = canvasComputedWidth;
        context.drawImage(video, 0, 0, canvasComputedWidth, canvas.height);
    } else {
        // portrait mode
        // console.log("Portrait mode");
        canvas.width = smallerSideFixedCanvas;
        // fill horizontally
        var canvasComputedHeight = (canvas.width / video.videoWidth) * video.videoHeight;
        canvas.height = canvasComputedHeight;

        context.drawImage(video, 0, 0, canvas.width, canvasComputedHeight);
    }

    canvasAsBase64 = saveCanvasToFrameBase64(canvas);
    setTimeout(draw, 1 / frameRateForSending, video, canvas, context, frameRateForSending);
}

function saveCanvasToFrameBase64(canvas) {
    var canvasAsBase64 = canvas.toDataURL(frameContentType, frameQuality);
    return canvasAsBase64
}

function hookDrawingHandlers() {
    let context = STREAMED_CANVAS.getContext('2d');
    VIDEO_SOURCE.addEventListener('play', function () {
        // console.log("In AddEventListener");
        draw(this, STREAMED_CANVAS, context, frameRateForSending);
    }, false);
}

function gotStream(stream) {
    window.stream = stream; // make stream available to console
    VIDEO_SOURCE.srcObject = stream;
}

function startCameraStream() {
    if (window.stream) {
        window.stream.getTracks().forEach(track => {
            track.stop();
        });
    }

    if (currentConstraintTryNumber === null) {
        currentConstraintTryNumber = 0;
    } else {
        currentConstraintTryNumber += 1;
    }

    if (currentConstraintTryNumber >= constraintHierarchy.length) {
        logDebug("Giving up with constraint tries");
        return
    }

    let currentConstraints = constraintHierarchy[currentConstraintTryNumber];

    logDebug("Trying constraints " + currentConstraintTryNumber + " " + JSON.stringify(currentConstraints));

    navigator.mediaDevices
        .getUserMedia(currentConstraints)
        .then(gotStream)
        .catch(startCameraStream)
    ;
}