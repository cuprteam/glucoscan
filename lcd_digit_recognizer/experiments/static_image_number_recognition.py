import os

import cv2

from lcd_digit_recognizer.recognition.number_recognizer import recognize_digits
from lcd_digit_recognizer.visualization.utils import join_images

INPUT_DIR = "test_images"
OUTPUT_DIR = "output_images"

for name in os.listdir(INPUT_DIR):
    input_path = os.path.join(INPUT_DIR, name)
    output_path = os.path.join(OUTPUT_DIR, name)
    print()
    print()
    print(f"PATH: {input_path}")
    image = cv2.imread(input_path)

    numbers, imgs = recognize_digits(image, with_visualization=True)
    for number in numbers:
        print(number)

    if imgs:
        img = join_images(imgs)

        cv2.imwrite(output_path, img)
        if False and name == "lcd2.png":
            cv2.imshow("output", img)
            cv2.waitKey()
