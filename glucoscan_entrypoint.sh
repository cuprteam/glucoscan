#!/usr/bin/env bash

# Define the number of workers
WORKERS=2

# Run web app
cd /app/lcd_digit_recognizer/web/
python3 app.py &

# Run workers
cd /app/lcd_digit_recognizer/web/recognition_processor

for (( i = 0; i < $WORKERS; i++ ))
do
  echo "Starting Worker Thread nr.$i"
  python3 local_recognition_worker.py &
done

echo "Sleeping infinitely"
sleep inf



