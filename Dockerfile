FROM python:3.6-slim

ENV DEBIAN_FRONTEND noninteractive

COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN apt-get update && \
    apt-get install build-essential libglib2.0-0 libsm6 libxext6 libxrender-dev -y && \
    apt-get clean && \
    pip3 install -r requirements.txt && \
    rm -rf ~/.cache/pip && \
    apt-get remove build-essential gcc -y && \
    apt-get autoremove -y

ENV PYTHONPATH /app/

COPY lcd_digit_recognizer/ /app/lcd_digit_recognizer/
COPY recognize_seven_segment/ /app/recognize_seven_segment/

COPY glucoscan_entrypoint.sh /app/glucoscan_entrypoint.sh

RUN chmod +x glucoscan_entrypoint.sh
CMD /app/glucoscan_entrypoint.sh