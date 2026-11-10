"""Conservative paper isolation using the existing OCR environment's OpenCV."""
import cv2
import numpy as np


class ReceiptBoundaryError(ValueError):
    pass


def isolate_receipt(image):
    """Return only the detected paper, or reject an ambiguous scene.

    Supports a dominant light paper quadrilateral and already tightly cropped
    scans with a continuous neutral paper border. This is not receipt semantics.
    """
    height, width = image.shape[:2]
    scale = min(1.0, 1000 / max(height, width))
    small = cv2.resize(image, (round(width * scale), round(height * scale)))
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    saturation = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)[:, :, 1]
    h, w = gray.shape
    smooth = cv2.GaussianBlur(gray, (5, 5), 0)
    otsu, _ = cv2.threshold(smooth, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    candidates = []
    masks = []
    for threshold in sorted(set([int(otsu), 120, 150, 180, 205])):
        mask = (smooth > threshold).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        masks.append((mask, cv2.RETR_EXTERNAL, 0))
    padded = cv2.copyMakeBorder(smooth, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=0)
    for low, high in [(20, 60), (40, 120), (70, 180)]:
        edges = cv2.Canny(padded, low, high)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        masks.append((edges, cv2.RETR_LIST, 4))
    for mask, mode, padding in masks:
        contours, _ = cv2.findContours(mask, mode, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            contour = contour - padding
            area = cv2.contourArea(contour)
            if not .22 * w * h < area < .98 * w * h:
                continue
            hull = cv2.convexHull(contour)
            polygon = cv2.approxPolyDP(hull, .025 * cv2.arcLength(hull, True), True)
            if len(polygon) != 4 or not cv2.isContourConvex(polygon):
                continue
            vertices = polygon.reshape(4, 2).astype(float)
            edges = np.roll(vertices, -1, axis=0) - vertices
            lengths = np.linalg.norm(edges, axis=1)
            if lengths.min() < min(w, h) * .18:
                continue
            cosines = np.sum(edges * np.roll(edges, -1, axis=0), axis=1) / (lengths * np.roll(lengths, -1))
            if np.max(np.abs(cosines)) > .28:
                continue
            polygon_area = cv2.contourArea(polygon)
            if polygon_area <= 0 or not .88 < area / polygon_area < 1.1:
                continue
            if cv2.pointPolygonTest(polygon, (w / 2, h / 2), False) < 0:
                continue
            paper = np.zeros_like(gray)
            cv2.fillConvexPoly(paper, polygon, 255)
            inside = cv2.erode(paper, np.ones((9, 9), np.uint8)) > 0
            ring = (cv2.dilate(paper, np.ones((21, 21), np.uint8)) > 0) & (paper == 0)
            if not inside.any() or np.count_nonzero(ring) < 50:
                continue
            brightness = float(np.median(gray[inside]))
            if brightness < 115 or np.median(saturation[inside]) > 85:
                continue
            if brightness - float(np.median(gray[ring])) < 25:
                continue
            supported_edges = 0
            clipped_edges = 0
            center = vertices.mean(axis=0)
            for start, end in zip(vertices, np.roll(vertices, -1, axis=0)):
                midpoint = (start + end) / 2
                inward = center - midpoint
                inward /= max(np.linalg.norm(inward), 1)
                contrasts = []
                for fraction in [.15, .3, .5, .7, .85]:
                    point = start + (end - start) * fraction
                    inner = np.rint(point + inward * 14).astype(int)
                    outer = np.rint(point - inward * 14).astype(int)
                    if all(2 <= x < w-2 and 2 <= y < h-2 for x, y in [inner, outer]):
                        ix, iy = inner; ox, oy = outer
                        contrasts.append(float(np.median(gray[iy-2:iy+3, ix-2:ix+3])) - float(np.median(gray[oy-2:oy+3, ox-2:ox+3])))
                if len(contrasts) < 3:
                    clipped_edges += 1
                elif sum(c > 15 for c in contrasts) >= 3:
                    supported_edges += 1
            if clipped_edges > 2 or supported_edges + clipped_edges < 4:
                continue
            candidates.append((polygon_area, polygon.reshape(4, 2)))
    if candidates:
        candidates.sort(key=lambda c: c[0], reverse=True)
        area, corners = candidates[0]
        # Different thresholds must agree on the document, not select conflicting
        # overlapping panels of a screen or several pieces of paper.
        if any(other_area > area * .65 and np.linalg.norm(other.mean(axis=0) - corners.mean(axis=0)) > min(w, h) * .1
               for other_area, other in candidates[1:]):
            raise ReceiptBoundaryError('Ambiguous paper boundaries')
        corners = corners.astype(np.float32) / scale
        # Polar ordering preserves cyclic adjacency, unlike sum/difference ties.
        center = corners.mean(axis=0)
        corners = corners[np.argsort(np.arctan2(corners[:, 1] - center[1], corners[:, 0] - center[0]))]
        corners = np.roll(corners, -np.argmin(corners.sum(axis=1)), axis=0)
        a, b, c, d = corners
        out_w = round(max(np.linalg.norm(b-a), np.linalg.norm(c-d)))
        out_h = round(max(np.linalg.norm(d-a), np.linalg.norm(c-b)))
        if min(out_w, out_h) < 100:
            raise ReceiptBoundaryError('Receipt too small')
        target = np.float32([[0, 0], [out_w-1, 0], [out_w-1, out_h-1], [0, out_h-1]])
        return cv2.warpPerspective(image, cv2.getPerspectiveTransform(corners, target), (out_w, out_h), borderValue=(255, 255, 255))
    # A digital receipt/close crop has paper along every edge; do not accept
    # colored scenes merely because they contain a few white pixels.
    band = max(2, round(min(w, h) * .012))
    edges = [(gray[:band], saturation[:band]), (gray[-band:], saturation[-band:]),
             (gray[:, :band], saturation[:, :band]), (gray[:, -band:], saturation[:, -band:])]
    coverage = [np.mean((g > 155) & (s < 55)) for g, s in edges]
    # A clipped footer can cross one edge of an otherwise paper-filled scan.
    if sum(c > .97 for c in coverage) >= 3 and min(coverage) > .8 or all(c > .92 for c in coverage):
        return image
    raise ReceiptBoundaryError('Receipt boundary not clear')
