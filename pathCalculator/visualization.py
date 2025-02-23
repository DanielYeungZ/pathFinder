import cv2


def visualize_path(image, path, is_original=True):
    path_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if not is_original else image.copy()
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        cv2.line(path_image, (start[1], start[0]), (end[1], end[0]), (0, 0, 255), thickness=3)
    return path_image


def display_images(*images):
    for idx, img in enumerate(images):
        cv2.imshow(f"Image {idx + 1}", img)

