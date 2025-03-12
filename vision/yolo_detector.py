from ultralytics import YOLO

class YoloDetector:
    def __init__(self, model_path):
        # Load the YOLOv8x model from the given path
        self.model = YOLO(model_path)

    def detect(self, image):
        """
        Perform object detection on the input image.
        
        Args:
            image: A NumPy array representing the image.
        
        Returns:
            A list of detections, where each detection is a dictionary with:
            - "bbox": [x1, y1, x2, y2] coordinates
            - "class": Detected class name
            - "confidence": Confidence score of the detection
        """
        results = self.model(image)
        detections = []
        for result in results:
            # Iterate over detected boxes in each result
            for box in result.boxes:
                coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                confidence = box.conf[0].item()
                class_id = int(box.cls[0].item())
                class_name = result.names.get(class_id, "unknown") if result.names else "unknown"
                detections.append({
                    "bbox": coords,
                    "class": class_name,
                    "confidence": confidence
                })
        return detections

# For testing purposes:
if __name__ == "__main__":
    import cv2
    # Load an image for testing (update the path as needed)
    image = cv2.imread("test_image.jpg")
    detector = YoloDetector("yolov8x.pt")
    results = detector.detect(image)
    print("Detections:", results)
