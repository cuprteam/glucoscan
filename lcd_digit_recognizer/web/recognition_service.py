import base64
import datetime
import pickle
import time
from collections import Counter

from lcd_digit_recognizer.web.recognition_processor.remote_processor_pool import RemoteProcessorPool

RECOGNITION_EXPIRATION_TIME = 5  # how long recognized value is considered [seconds]



class RecognitionService(object):
    def __init__(self, recognition_callback):
        if recognition_callback is None:
            raise AssertionError("recognition_callback has to be specified")

        self._recognition_callback = recognition_callback
        self._recognition_contexts = {}
        self._pool = RemoteProcessorPool(self._recognizer_result_callback)

    def start(self):
        self._pool.start()

    def _recognizer_result_callback(self, res):
        sid = res["sid"]
        image_id = res["image_id"]
        number = res["number"]
        metadata = res["metadata"]

        if number is None and metadata is None:
            return  # nothing to report about

        self._report_result(sid, image_id, number, metadata)

    def add_job(self, sid, image_id, image, input_id):
        image_data = base64.b64encode(pickle.dumps(image)).decode('ascii')
        self._pool.add_job(
            {"sid": sid, "image_id": image_id, "image_data": image_data, "input_id": input_id, "time": time.time()}
        )

    def close_context(self, sid):
        self._recognition_contexts.pop(sid)

    def _report_result(self, sid, image_id, number, metadata):
        """
        This has to be run via _worker
        """
        if sid not in self._recognition_contexts:
            self._recognition_contexts[sid] = RecognitionContext()

        context = self._recognition_contexts[sid]
        context.add(number)

        result = {
            'sid': sid,
            'current_image_recognition': number,
            'current_image_metadata': metadata,
            'recognition_history': context.history,
        }

        self._recognition_callback(sid, image_id, result)


class RecognitionContext(object):
    def __init__(self):
        self._timed_values = []

    @property
    def history(self):
        self._prune_values()
        return Counter(v[1] for v in self._timed_values)

    def add(self, number):
        if number is None:
            return

        self._timed_values.append((datetime.datetime.now(), number))

    def _prune_values(self):
        threshold = datetime.datetime.now() - datetime.timedelta(seconds=RECOGNITION_EXPIRATION_TIME)
        for i in reversed(range(len(self._timed_values))):
            time = self._timed_values[i][0]

            if time < threshold:
                del self._timed_values[i]
