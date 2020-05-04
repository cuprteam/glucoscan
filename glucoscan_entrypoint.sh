#!/usr/bin/env bash

# Run web app
cd /app/lcd_digit_recognizer/web/
python3 app.py &

# Run worker
cd /app/lcd_digit_recognizer/web/recognition_processor
python3 local_recognition_worker.py





