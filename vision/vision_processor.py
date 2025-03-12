import base64
import cv2
import numpy as np
import logging
import asyncio
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class VisionProcessor:
    def __init__(self, vision_settings):
        self.yolo_model_path = vision_settings.yolo_model_path
        self.use_easyocr = vision_settings.use_easyocr
        self.model = None
        self.ocr_reader = None
        
        # Lazy-load the models when first needed
        # This avoids loading them if they're not used
        
    async def _load_models(self):
        """Load YOLO and OCR models when first needed"""
        if self.model is None:
            try:
                from ultralytics import YOLO
                logger.info(f"Loading YOLO model from {self.yolo_model_path}")
                self.model = YOLO(self.yolo_model_path)
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
                self.model = False  # Set to False to indicate loading failed
        
        if self.use_easyocr and self.ocr_reader is None:
            try:
                import easyocr
                logger.info("Loading EasyOCR model")
                self.ocr_reader = easyocr.Reader(['en'])
                logger.info("EasyOCR model loaded successfully")
            except ImportError:
                logger.warning("EasyOCR not installed. Text detection will be skipped.")
                self.ocr_reader = False
            except Exception as e:
                logger.error(f"Failed to load EasyOCR model: {e}")
                self.ocr_reader = False

    async def process(self, screenshot_base64, state):
        """
        Process a screenshot (provided as a base64 string) and return vision analysis.
        """
        # Load models if needed
        await self._load_models()
        
        # Decode the screenshot from base64 to a NumPy array image
        try:
            # Convert base64 to bytes
            screenshot_bytes = base64.b64decode(screenshot_base64)
            
            # Convert to PIL Image first
            image_pil = Image.open(BytesIO(screenshot_bytes))
            
            # Convert PIL to OpenCV format (numpy array)
            image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
            
            # Initialize results
            analysis_results = {
                "detections": [],
                "text_regions": []
            }
            
            # Run YOLO detection if model loaded successfully
            if self.model and self.model is not False:
                try:
                    detections = await self._run_object_detection(image)
                    analysis_results["detections"] = detections
                except Exception as e:
                    logger.error(f"Error in object detection: {e}")
            
            # Run OCR if enabled and loaded successfully
            if self.ocr_reader and self.ocr_reader is not False:
                try:
                    text_regions = await self._run_ocr(image)
                    analysis_results["text_regions"] = text_regions
                except Exception as e:
                    logger.error(f"Error in OCR: {e}")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Failed to process screenshot: {e}")
            return {"error": str(e), "detections": [], "text_regions": []}

    async def _run_object_detection(self, image):
        """Run YOLO object detection on the image"""
        detections = []
        
        # Run in a thread to avoid blocking the event loop
        def detect():
            results = self.model(image)
            obj_detections = []
            
            for result in results:
                boxes = result.boxes
                for i, box in enumerate(boxes):
                    # Get box coordinates (x1, y1, x2, y2 format)
                    coords = box.xyxy[0].tolist()
                    # Get confidence score
                    conf = float(box.conf[0])
                    # Get class ID and name
                    cls_id = int(box.cls[0].item())
                    cls_name = result.names[cls_id]
                    
                    obj_detections.append({
                        "class": cls_name,
                        "confidence": conf,
                        "bbox": coords
                    })
            
            return obj_detections
        
        # Run detection in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(None, detect)
        
        return detections

    async def _run_ocr(self, image):
        """Run OCR on the image to detect text"""
        text_regions = []
        
        # Run in a thread to avoid blocking the event loop
        def recognize_text():
            results = self.ocr_reader.readtext(image)
            regions = []
            
            for bbox, text, conf in results:
                # Convert bbox points to x1,y1,x2,y2 format
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                x1, y1 = min(x_coords), min(y_coords)
                x2, y2 = max(x_coords), max(y_coords)
                
                regions.append({
                    "text": text,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2]
                })
            
            return regions
        
        # Run OCR in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        text_regions = await loop.run_in_executor(None, recognize_text)
        
        return text_regions