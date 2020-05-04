import base64
import pickle
import traceback
from time import sleep
import time

from lcd_digit_recognizer.web.recognition_processor.networking.socket_client import SocketClient
from lcd_digit_recognizer.web.recognition_processor.remote_processor_pool import RemoteProcessorPool
from recognize_seven_segment.hackathon_api import recognize_number


class LocalRecognitionWorker(object):
    def __init__(self, host: str, port: str):
        self._host = host
        self._port = port

    def blocking_run(self):
        client = None

        while True:
            if client is None:
                print("connecting SocketClient")
                client = SocketClient()
                client.connect(self._host, self._port)

            job = client.read_next_json()
            if job is not None:
                print("job accepted")
                start = time.time()
                response = self.run_recognition(job)
                client.send_json(response)
                end =  time.time()
                print(f"response sent after {end - start:.2f} ")

            if not client.is_connected:
                client = None
                sleep(1)

    def run_recognition(self, job):
        pickle_bytes = base64.b64decode(job["image_data"].encode('ascii'))
        image = pickle.loads(pickle_bytes)
        sid = job["sid"]
        image_id = job["image_id"]

        try:
            number, metadata = recognize_number.recognize_number(image)
        except Exception as e:
            print(f"RECOGNIZER EXCEPTION: {e}")
            formatted_exception = traceback.format_exc()
            print(formatted_exception)
            number = None
            metadata = {"exception": formatted_exception}

        metadata["input_id"] = job["input_id"]

        result = {
            "sid": sid,
            "image_id": image_id,
            "number": number,
            "metadata": metadata
        }

        return result


worker = LocalRecognitionWorker("127.0.0.1", RemoteProcessorPool.port)
worker.blocking_run()
