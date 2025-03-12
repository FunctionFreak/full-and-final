import base64
import cv2
import numpy as np
from vision.yolo_detector import YoloDetector

try:
    import easyocr
except ImportError:
    easyocr = None

class VisionProcessor:
    def __init__(self, vision_settings):
        # Initialize the YOLOv8x detector using the provided model path.
        self.yolo_detector = YoloDetector(vision_settings.yolo_model_path)
        self.use_easyocr = vision_settings.use_easyocr
        # If OCR is enabled and the module is available, initialize the OCR reader.
        if self.use_easyocr and easyocr is not None:
            self.ocr_reader = easyocr.Reader(['en'])
        else:
            self.ocr_reader = None

    async def process(self, screenshot_base64, state):
        """
        Process a screenshot (provided as a base64 string) and return vision analysis.
        
        Args:
            screenshot_base64 (str): The screenshot encoded in base64.
            state (dict): The current browser state (for additional context if needed).
        
        Returns:
            dict: A dictionary containing YOLO detections and OCR text regions.
                  Format: { "detections": [...], "text_regions": [...] }
        """
        # Decode the screenshot from base64 to a NumPy array image.
        screenshot_bytes = base64.b64decode(screenshot_base64)
        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Run YOLO detection on the image.
        detections = self.yolo_detector.detect(image)

        text_regions = []
        # If OCR is enabled, attempt to extract text from regions identified as textual.
        if self.ocr_reader:
            for detection in detections:
                # Customize this logic: here, we assume detections with class containing "text" are candidates.
                if "text" in detection["class"].lower():
                    x1, y1, x2, y2 = map(int, detection["bbox"])
                    roi = image[y1:y2, x1:x2]
                    ocr_results = self.ocr_reader.readtext(roi)
                    for bbox, text, conf in ocr_results:
                        text_regions.append({
                            "bbox": bbox,
                            "text": text,
                            "confidence": conf
                        })

        return {
            "detections": detections,
            "text_regions": text_regions
        }

# For testing purposes:
if __name__ == "__main__":
    import asyncio

    async def main():
        # Load a test screenshot file (update the file path as needed) and encode it as base64.
        with open("test_screenshot.png", "rb") as f:
            screenshot_b64 = base64.b64encode(f.read()).decode("utf-8")
        from config.settings import load_settings
        settings = load_settings()
        processor = VisionProcessor(settings.vision)
        result = await processor.process(screenshot_b64, {})
        print("Vision Results:", result)
    
    asyncio.run(main())
