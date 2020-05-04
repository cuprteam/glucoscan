import os
from typing import List

import cv2
import numpy as np


def load_image(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path)
    return image


def list_image_paths(image_dir: str, suffix: str = ".jpg") -> List[str]:
    image_names = os.listdir(image_dir)
    image_names = [name for name in image_names if name.endswith(suffix)]
    image_names = [image_dir + name for name in image_names]
    return image_names


def get_image_name(image_path: str) -> str:
    return image_path.split("/")[-1].split(".")[0]


def create_dir_if_it_doesnt_exist(dir_path: str):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
