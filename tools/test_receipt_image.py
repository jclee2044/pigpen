"""Run in backend/.ocr-venv; no additional test dependency is needed."""
import unittest
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
from receipt_image import isolate_receipt, ReceiptBoundaryError


class IsolationTests(unittest.TestCase):
    def curved_receipt(self):
        image = np.full((1000, 900, 3), 40, np.uint8)
        for y in range(120, 900):
            bend = round(65 * np.sin((y - 120) / 780 * np.pi))
            shade = round(240 * (1 - .52 * np.exp(-((y - 510) / 110) ** 2)))
            image[y, 170 + bend:730 - bend] = shade
        cv2.putText(image, 'TOTAL 7.95', (275, 650), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, 'NOT THE SHOP', (120, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
        return image

    def test_curved_shaded_paper_preserves_text_and_excludes_background(self):
        image = self.curved_receipt()
        cropped = isolate_receipt(image)
        self.assertGreater(cropped.shape[0], 750)
        self.assertLess(cropped.shape[0], 850)
        self.assertGreater(cropped.shape[1], 530)
        self.assertLess(cropped.shape[1], 620)
        # No silhouette mask may erase letters on shaded paper.
        self.assertEqual(np.count_nonzero(np.all(cropped == 0, axis=2)), np.count_nonzero(np.all(image == 0, axis=2)))
        self.assertGreater(np.count_nonzero(np.all(cropped == 0, axis=2)), 300)

    def test_close_crop_preserved_for_manual_ocr(self):
        image = self.curved_receipt()[200:800]
        np.testing.assert_array_equal(isolate_receipt(image), image)

    def test_round_pale_object_rejected(self):
        image = np.full((1000, 900, 3), 40, np.uint8)
        cv2.ellipse(image, (450, 500), (250, 390), 0, 0, 360, (240, 240, 240), -1)
        with self.assertRaises(ReceiptBoundaryError):
            isolate_receipt(image)

    def test_separate_sheets_rejected(self):
        image = np.full((1000, 1100, 3), 40, np.uint8)
        image[100:900, 50:500] = 240
        image[100:900, 600:1050] = 240
        with self.assertRaises(ReceiptBoundaryError):
            isolate_receipt(image)

    def test_colored_curved_object_rejected(self):
        image = self.curved_receipt()
        paper = image[:, :, 0] > 100
        image[paper] = (100, 255, 100)
        with self.assertRaises(ReceiptBoundaryError):
            isolate_receipt(image)

    def test_background_is_excluded(self):
        image = np.full((1000, 900, 3), 45, np.uint8)
        cv2.putText(image, 'NOT THE SHOP', (120, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
        image[160:920, 190:710] = 240
        cv2.putText(image, 'RECEIPT', (240, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cropped = isolate_receipt(image)
        self.assertTrue(520 <= cropped.shape[1] < 580)
        self.assertTrue(760 <= cropped.shape[0] < 820)
        self.assertFalse(np.any(cropped == 255), "Exterior white lettering must be excluded")
        self.assertEqual(np.count_nonzero(np.all(cropped == 0, axis=2)), np.count_nonzero(np.all(image == 0, axis=2)))

    def test_real_photos_preserve_the_entire_document(self):
        fixtures = Path(__file__).parent / 'fixtures/receipt-photos'
        for path in sorted(fixtures.glob('*.jpg')):
            with self.subTest(photo=path.name):
                image = np.asarray(Image.open(path).convert('RGB'))
                cropped = isolate_receipt(image)
                if path.name == '1003-receipt.jpg':
                    # Annotated visible paper envelope, including curled footer.
                    _, _, location, _ = cv2.minMaxLoc(cv2.matchTemplate(image, cropped, cv2.TM_SQDIFF))
                    x, y = location; h, w = cropped.shape[:2]
                    self.assertLessEqual(x, 153); self.assertLessEqual(y, 44)
                    self.assertGreaterEqual(x+w, 607); self.assertGreaterEqual(y+h, 995)
                    np.testing.assert_array_equal(cropped, image[y:y+h, x:x+w])
                else:
                    # These uncertain/tight boundaries must retain every pixel.
                    np.testing.assert_array_equal(cropped, image)

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
