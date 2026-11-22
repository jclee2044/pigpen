"""Conservative paper framing using the existing OCR environment's OpenCV.

Never erase pixels inside a receipt or force curved paper into four corners.
An uncertain boundary keeps the original frame for OCR and content validation.
"""
import cv2
import numpy as np


class ReceiptBoundaryError(ValueError):
    pass


def isolate_receipt(image):
    height, width = image.shape[:2]
    scale = min(1.0, 1000 / max(height, width))
    small = cv2.resize(image, (round(width * scale), round(height * scale)))
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    # A permissive paper mask includes shadowed/warm paper, not just the
    # brightest patch. Fill ink-sized gaps before looking at whole sheets.
    mask = ((gray > 65) & (hsv[:, :, 1] < 100)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = gray.shape
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    if not contours or cv2.contourArea(contours[0]) < .25 * w * h:
        raise ReceiptBoundaryError('No dominant paper region')
    area = cv2.contourArea(contours[0])
    if any(cv2.contourArea(c) > max(area * .45, w * h * .12) for c in contours[1:]):
        raise ReceiptBoundaryError('Multiple paper regions')
    x, y, cw, ch = cv2.boundingRect(contours[0])
    (_, _), (rw, rh), _ = cv2.minAreaRect(contours[0])
    if min(rw, rh) < min(w, h) * .18 or area / max(rw * rh, 1) < .80:
        raise ReceiptBoundaryError('Paper shape unclear')
    # A close crop or pale surface can merge with paper. Do not invent a
    # boundary or cut away a dark header/footer; let OCR validate the content.
    if x < 3 or y < 3 or x + cw > w - 3 or y + ch > h - 3:
        return image
    # Trim only the exterior bounding rectangle, with a generous margin.
    # No perspective warp or silhouette mask can delete ink within this frame.
    margin = max(8, round(min(w, h) * .025))
    left = max(0, int((x - margin) / scale))
    top = max(0, int((y - margin) / scale))
    right = min(width, int(np.ceil((x + cw + margin) / scale)))
    bottom = min(height, int(np.ceil((y + ch + margin) / scale)))
    if min(right - left, bottom - top) < 100:
        raise ReceiptBoundaryError('Receipt too small')
    return image[top:bottom, left:right].copy()
