import time
from queue import Queue, LifoQueue
from threading import Thread
from typing import Callable, Dict

from lcd_digit_recognizer.web.recognition_processor.networking.server import Server
from lcd_digit_recognizer.web.recognition_processor.networking.socket_client import SocketClient


class RemoteProcessorPool(object):
    port = 43621

    def __init__(self, response_callback: Callable[[Dict], None]):
        if response_callback is None:
            raise AssertionError("response callback has to be defined")

        self._response_callback = response_callback
        self._job_queue = LifoQueue()
        self._response_queue = Queue()

        self._server = None
        self._worker_master_thread = None
        self._response_sender_thread = None

    def start(self):
        self._server = Server(RemoteProcessorPool.port)
        self._worker_master_thread = Thread(target=self._worker_accepter)
        self._worker_master_thread.daemon = True
        self._worker_master_thread.start()

        self._response_sender_thread = Thread(target=self._response_sender)
        self._response_sender_thread.daemon = True
        self._response_sender_thread.start()

    def _worker_accepter(self):
        print("Accepting remote pool clients")
        while True:
            new_worker = self._server.accept_next_client()
            new_worker_thread = Thread(target=self._worker, args=[new_worker])
            new_worker_thread.daemon = True
            new_worker_thread.start()

    def _response_sender(self):
        while True:
            response = self._response_queue.get()
            self._response_callback(response)

    def _worker(self, worker_client: SocketClient):
        print("Remote processor pool worker started")
        while worker_client.is_connected:
            job = self._job_queue.get()

            if job is None:
                return  # signal to end

            job_age = time.time() - job["time"]
            if job_age > 2:
                print(f"Skipping too old job {job_age:.2f}s")
                continue  # outdated job

            worker_client.send_json(job)
            response = worker_client.read_next_json()
            if response is None:
                # client disconnected, renew the job
                print("Renewing failed job")
                self._job_queue.put(job)
                continue

            self._response_queue.put(response)

        print("Remote processor pool worker ended")

    def add_job(self, job):
        self._job_queue.put(job)
