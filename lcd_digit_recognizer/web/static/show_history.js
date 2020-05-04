let historyOutputEl = document.getElementById('history_output');
let historyStorageKey = "value_history";
let valueMaxHistoryLength = 120;

function hideShowHistorySaved(){
    document.getElementById("history_saved").style.visibility= "hidden" ;
}



function clipboardHistoryExport() {
    let values = readStoredValues();
    let encodedHistory = urlEncodeHistory(values);

    let exportedUrl = "https://glucoscan.org/dashboard?data=" + encodedHistory;
    copyStringToClipboard(exportedUrl);

    document.getElementById("history_saved").style.visibility= "visible" ;
    setTimeout(hideShowHistorySaved,1000);
}

function readStoredValues() {
    let value = localStorage.getItem(historyStorageKey);
    if (value === null) {
        return []
    }

    return JSON.parse(value);
}

function renderValues(el, historyItems) {
    for (let historyItem of historyItems.reverse()) {
        renderValue(el, historyItem);
    }
}

function renderValue(el, historyItem) {
    // create item structure
    let itemEl = document.createElement('div');
    let valueEl = document.createElement('div');
    let dateEl = document.createElement('div');
    let arrowEl = document.createElement('img');

    itemEl.className = "history_item";
    valueEl.className = "history_value";
    dateEl.className = "history_date";
    arrowEl.className = "history_arrow";

    itemEl.appendChild(dateEl);
    itemEl.appendChild(valueEl);

    // fill the items
    let parsedDate = new Date(historyItem["date"]);
    let arrowChar = getArrowChar(historyItem["value"]);
    // arrowEl.innerText = arrowSymbols[arrowChar];
    // arrowEl.title = arrowPhrases[arrowChar];

    valueEl.innerText = translateArrows(historyItem["value"], false);
    if (arrowChar !== null && arrowChar.trim().length > 0) {
        arrowEl.src = "/static/arrow_" + arrowChar + ".png";
        arrowEl.alt = arrowPhrases[arrowChar];
        valueEl.appendChild(arrowEl);
    }

    dateEl.innerText = parsedDate.toLocaleString([], {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });

    el.appendChild(itemEl);
}

function renderHistory() {
    renderValues(historyOutputEl, readStoredValues());
}

function saveHistoryValue(value) {
    let date = Date();
    let item = {
        'date': date,
        'value': value
    }

    let history = localStorage.getItem(historyStorageKey);
    if (history === null) {
        history = [];
    } else {
        history = JSON.parse(history);
    }

    history.push(item);

    while (history.length > valueMaxHistoryLength) {
        history.splice(0, 1);
    }

    localStorage.setItem(historyStorageKey, JSON.stringify(history));
}

function decodeUrlValues() {
    let url = new URL(window.location.href);
    let inputBase64 = url.searchParams.get("data");
    let inputBytes = Uint8Array.from(atob(inputBase64), c => c.charCodeAt(0));
    inputBytes = Array.prototype.slice.call(inputBytes);
    let baseTimeStamp = readNum8B(inputBytes);

    let result = [];
    let currentTimeStamp = baseTimeStamp;
    while (inputBytes.length > 0) {
        let value = readGlycemicValue3B(inputBytes);
        let item = {
            'date': convertUTCDateToLocalDate(new Date(currentTimeStamp)),
            'value': value
        };
        result.push(item);

        let timeDiff = readNum3B(inputBytes);
        currentTimeStamp += timeDiff;
    }

    return result;
}

function urlEncodeHistory(history) {
    let byteBuffer = [];
    let currentTimeStamp = null;
    for (let item of history) {
        let itemTimestamp = getUtcTimestamp(new Date(item['date']));
        let value = item['value'];
        let timeBytes;
        if (currentTimeStamp == null) {
            timeBytes = numTo8B(itemTimestamp);
        } else {
            let diff = itemTimestamp - currentTimeStamp
            timeBytes = numTo3B(diff);
        }
        currentTimeStamp = itemTimestamp;

        fillWith(byteBuffer, timeBytes);

        let valueBytes = glycemicValueTo3B(value);
        fillWith(byteBuffer, valueBytes);
    }

    let base64String = btoa(String.fromCharCode(...new Uint8Array(byteBuffer)));
    return base64String;
}

function getUtcTimestamp(d) {
    let utcD = new Date(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), d.getUTCHours(), d.getUTCMinutes(), d.getUTCSeconds());
    return utcD;
}

function convertUTCDateToLocalDate(d) {
    let newDate = new Date(d.getTime() + d.getTimezoneOffset() * 60 * 1000);

    let offset = d.getTimezoneOffset() / 60;
    let hours = d.getHours();

    newDate.setHours(hours - offset);

    return newDate;
}

function fillWith(target, input) {
    for (let inputValue of input) {
        target.push(inputValue);
    }
}

function numTo2B(num) {
    return numToBytes(num, 2);
}

function numTo3B(num) {
    return numToBytes(num, 3);
}

function numTo8B(num) {
    return numToBytes(num, 8);
}

function numToBytes(num, byteCount) {
    result = [];
    for (let i = 0; i < byteCount; ++i) {
        byte = num % 255;
        result.push(byte);
        num = Math.floor(num / 255);
    }
    return result.reverse();
}

function readNumFromBytes(bytes, byteCount) {
    let value = 0;
    for (let i = 0; i < byteCount; ++i) {
        value = value * 255;
        value += bytes[0];
        bytes.splice(0, 1);
    }

    return value;
}

function getArrowChar(value) {
    value = value.trimLeft();
    let tokens = value.split(" ");
    let arrowChar;
    if (tokens.length > 1) {
        arrowChar = tokens[1];
    } else {
        arrowChar = " ";
    }
    return arrowChar.replace(String.fromCharCode(0), "").toLowerCase();
}

function glycemicValueTo3B(value) {
    let rawValue = translateArrows(value, false);
    let sanitizedValue = rawValue.replace(".", "");
    let numValue = parseInt(sanitizedValue);

    let arrowChar = getArrowChar(value);


    result = numTo2B(numValue);
    result.push(arrowChar.charCodeAt(0));
    return result;
}

function readGlycemicValue3B(buffer) {
    let sanitizedValue = readNum2B(buffer);
    let valueStr = "" + sanitizedValue;
    if (valueStr.length > 1) {
        valueStr = valueStr.substr(0, valueStr.length - 1) + "." + valueStr.substr(valueStr.length - 1)
    }

    let arrowCh = readNum1B(buffer);
    return valueStr + " " + String.fromCharCode(arrowCh);
}

function readNum8B(buffer) {
    return readNumFromBytes(buffer, 8);
}

function readNum2B(buffer) {
    return readNumFromBytes(buffer, 2);
}

function readNum1B(buffer) {
    return readNumFromBytes(buffer, 1);
}

function readNum3B(buffer) {
    return readNumFromBytes(buffer, 3);
}

function copyStringToClipboard(str) {
    // Create new element
    let el = document.createElement('textarea');
    // Set value (string to be copied)
    el.value = str;
    // Set non-editable to avoid focus and move outside of view
    el.setAttribute('readonly', '');
    el.style = {position: 'absolute', left: '-9999px'};
    document.body.appendChild(el);
    // Select text inside element
    el.select();
    // Copy text to clipboard
    document.execCommand('copy');
    // Remove temporary element
    document.body.removeChild(el);
}
