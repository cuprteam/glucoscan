import base64
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from recognize_seven_segment.detectors.detect_digits import detect_digits


def recognize_number(image: np.ndarray) -> Tuple[Optional[str], Dict]:
    annotation, metadata = detect_digits(image)

    if "annotated_image" in metadata:
        annotated_image = metadata["annotated_image"]
        image_png_str = cv2.imencode('.png', annotated_image)[1].tostring()
        base64_encoded_image = str(base64.b64encode(image_png_str), "utf-8")
        metadata["annotated_image"] = base64_encoded_image

    return annotation, metadata
