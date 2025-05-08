import base64
import numpy as np
import cv2
from app.config import SAMPLE_POINTS, MATCH_POINT


def get_image_code(image_base64: str) -> tuple:
    """
    Use OpenCV ORB model to detect and compute the image code.
    Accepts base64-encoded image string.
    """

    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception:
        return None, None

    img_array = np.frombuffer(image_bytes, np.uint8)
    image_gray = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB.create(nfeatures=SAMPLE_POINTS)
    if image_gray is None:
        return None, None
    mask = np.zeros(image_gray.shape, dtype=np.uint8)
    keypoints, descriptors = orb.detectAndCompute(image_gray, mask)
    return keypoints, descriptors


def match_with_db(code1: np.ndarray, code2: np.ndarray) -> bool:
    """
    Use NORM_HAMMING function to match the two images, calculate the distance of vectors
    from them, and if the match points stay in a close distance, thinking they are similar.
    :param code1: np.ndarray
    :param code2: np.ndarray
    :return: bool
    """
    if code1 is None or code2 is None:
        return False

    # Convert descriptors to uint8 if needed
    if code1.dtype != np.uint8:
        code1 = code1.astype(np.uint8)
    if code2.dtype != np.uint8:
        code2 = code2.astype(np.uint8)

    # Adjust descriptor columns to the minimum of both
    min_cols = min(code1.shape[1], code2.shape[1])
    if code1.shape[1] != min_cols:
        code1 = code1[:, :min_cols]
    if code2.shape[1] != min_cols:
        code2 = code2[:, :min_cols]

    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    try:
        matches = bf.knnMatch(code1, code2, k=2)
    except cv2.error:
        return False
    try:
        good_match = [m for (m, n) in matches if m.distance < 0.8 * n.distance]
    except ValueError:
        return False
    if len(matches) == 0:
        return False
    similarity = len(good_match) / len(matches)
    print(f"Similarity: {similarity}")
    return similarity > MATCH_POINT
