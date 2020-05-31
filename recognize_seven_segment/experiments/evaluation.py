from typing import Dict, Callable, Tuple

import cv2
import numpy as np
from tqdm import tqdm

from recognize_seven_segment.detectors.detect_digits import detect_digits
from recognize_seven_segment.utils.input_output import list_image_paths, load_image


def get_label(image_path: str) -> str:
    label_path = image_path[:-len(".jpg")] + ".txt"
    with open(label_path, "r") as file:
        label = file.readline()
    return str(label)


def evaluate(image_dir: str, predict_function: Callable[[np.ndarray], Tuple[str, Dict]]) -> Dict[str, float]:
    image_paths = list_image_paths(image_dir)

    correctly_classified_count = 0
    classified_count = 0

    for image_path in tqdm(image_paths):
        image = load_image(image_path)
        label = get_label(image_path)

        predicted_label, metadata = predict_function(image)

        if predicted_label is not None:
            classified_count += 1

            annotated_display = metadata["annotated_image"]
            cv2.imwrite(f"/tmp/annotations/{image_path.split('/')[-1]}", annotated_display)

            if label == predicted_label:
                correctly_classified_count += 1

    return {"certain_and_correct": correctly_classified_count,
            "total_certain": classified_count,
            "total": len(image_paths)}


def main():
    evaluation_images_dir = "/tmp/images/"

    evaluation = evaluate(evaluation_images_dir, detect_digits)
    print(evaluation)


if __name__ == "__main__":
    main()
