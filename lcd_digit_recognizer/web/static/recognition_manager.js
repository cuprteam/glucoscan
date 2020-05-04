let HAS_RECOGNIZED_VALUE_CLASS = "contains_recognized_value";


RecognitionManager = function (displayEl) {
    let _currentRecognizedValue = null;
    let _currentMessage = null;
    let _areRecognizedValuesBlocked = false;
    let _messageTimeout = null;

    function _runRecognitionTextRefresh() {
        if (_messageTimeout != null) {
            // don't reread when there is a flashed message
            return;
        }
        _renderDisplay();
        setTimeout(_runRecognitionTextRefresh, 2000);
    }

    function _renderDisplay() {
        if (!_areRecognizedValuesBlocked && _currentRecognizedValue !== null) {
            displayEl.innerText = translateArrows(_currentRecognizedValue);
            return;
        }

        if (_currentMessage != null) {
            displayEl.innerText = _currentMessage;
            return;
        }

        displayEl.innerText = "Detecting";
    }

    function _clearMessage() {
        if (_messageTimeout === null)
            return; // nothing to do here

        clearTimeout(_messageTimeout);
        _messageTimeout = null;
        _currentMessage = null;
        _areRecognizedValuesBlocked = false;

        _renderDisplay();
    }

    _runRecognitionTextRefresh();

    return {
        setRecognizedValue: function (value) {
            if (_areRecognizedValuesBlocked)
                return; // wait until message is displayed

            if (value === _currentRecognizedValue)
                return; // reassigning could cause unwanted reread

            _clearMessage();

            _currentRecognizedValue = value;
            _renderDisplay();

            if (!$(displayEl).hasClass(HAS_RECOGNIZED_VALUE_CLASS)) {
                $(displayEl).addClass(HAS_RECOGNIZED_VALUE_CLASS);
            }
        },

        showMessage: function (message, duration, blockValues = false) {
            _clearMessage();

            _currentMessage = message;
            _areRecognizedValuesBlocked = blockValues;
            _renderDisplay();

            _messageTimeout = setTimeout(function () {
                _currentMessage = null;
                _areRecognizedValuesBlocked = false;
                _renderDisplay();
            }, Math.floor(duration * 1000));
        },

        getCurrentValue: function () {
            return _currentRecognizedValue;
        },

        clearCurrentValue: function () {
            _clearMessage();
            _currentRecognizedValue = null;
            $(displayEl).removeClass(HAS_RECOGNIZED_VALUE_CLASS);
            _renderDisplay();
        },

        hasCurrentValue: function () {
            return _currentRecognizedValue !== null;
        }
    };
};