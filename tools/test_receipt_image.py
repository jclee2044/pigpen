"""Run in backend/.ocr-venv; no additional test dependency is needed."""
import unittest
import cv2
import numpy as np
from receipt_image import isolate_receipt, ReceiptBoundaryError


class IsolationTests(unittest.TestCase):
    def test_background_is_excluded(self):
        image = np.full((1000, 900, 3), 45, np.uint8)
        cv2.putText(image, 'NOT THE SHOP', (120, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
        image[160:920, 190:710] = 240
        cv2.putText(image, 'RECEIPT', (240, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cropped = isolate_receipt(image)
        self.assertLess(abs(cropped.shape[1] - 520), 12)
        self.assertLess(abs(cropped.shape[0] - 760), 12)
        self.assertGreater(float(np.mean(cropped[:30])), 220)

    def test_tight_scan_unchanged(self):
        image = np.full((700, 500, 3), 250, np.uint8)
        cv2.putText(image, 'TOTAL 7.95', (40, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        np.testing.assert_array_equal(isolate_receipt(image), image)

    def test_colored_scene_does_not_become_receipt(self):
        with self.assertRaises(ReceiptBoundaryError):
            isolate_receipt(np.full((700, 500, 3), (0, 255, 0), np.uint8))

    def test_tight_scan_with_footer_crossing_one_edge(self):
        image = np.full((700, 500, 3), 250, np.uint8)
        image[-10:, 200:260] = 0
        np.testing.assert_array_equal(isolate_receipt(image), image)

    def test_dark_scene_rejected(self):
        with self.assertRaises(ReceiptBoundaryError):
            isolate_receipt(np.full((700, 500, 3), 35, np.uint8))


if __name__ == '__main__':
    unittest.main()
