import easyocr

class OCRProcessor:
    def __init__(self):
        # Initialize the EasyOCR reader for English language.
        self.reader = easyocr.Reader(['en'])

    def recognize(self, image):
        """
        Perform OCR on the provided image using EasyOCR.
        
        Args:
            image: A NumPy array representing the image.
        
        Returns:
            A list of dictionaries, each containing:
              - "bbox": The bounding box coordinates for the detected text,
              - "text": The recognized text,
              - "confidence": The confidence score of the detection.
        """
        results = self.reader.readtext(image)
        texts = []
        for bbox, text, conf in results:
            texts.append({
                "bbox": bbox,
                "text": text,
                "confidence": conf
            })
        return texts

# For testing purposes:
if __name__ == "__main__":
    import cv2
    # Load a test image (update the path as necessary)
    image = cv2.imread("test_image.jpg")
    ocr_processor = OCRProcessor()
    ocr_results = ocr_processor.recognize(image)
    print("OCR Results:", ocr_results)
