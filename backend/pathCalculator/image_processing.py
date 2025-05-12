import cv2
import numpy as np


def read_image(image_path):
    return cv2.imread(image_path)


def apply_color_mask(image):
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    lower_green = np.array([40, 100, 100])
    upper_green = np.array([80, 255, 255])

    mask_red1 = cv2.inRange(image, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(image, lower_red2, upper_red2)
    mask_green = cv2.inRange(image, lower_green, upper_green)

    mask = cv2.bitwise_or(mask_red1, mask_red2)
    mask = cv2.bitwise_or(mask, mask_green)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    image_copy = image.copy()
    image_copy[mask > 0] = [255, 255, 255]  # Convert to white
    return image_copy


def convert_to_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def apply_threshold(gray_image, threshold_value=170):
    _, binary_image = cv2.threshold(gray_image, threshold_value, 255, cv2.THRESH_BINARY)
    return binary_image


def resize_image(image, scale_percent=50):
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
