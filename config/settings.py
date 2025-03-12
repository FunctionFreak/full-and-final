from pydantic import BaseModel, Field
import os
print("GROQ_API_KEY loaded:", os.getenv("GROQ_API_KEY"))

class BrowserSettings(BaseModel):
    headless: bool = Field(default=True, description="Run browser in headless mode")
    user_data_dir: str = Field(
        default=os.getenv("CHROME_USER_PATH", r"C:\Users\aashi\AppData\Local\Google\Chrome\User Data"),
        description="Chrome user data directory"
    )

class VisionSettings(BaseModel):
    yolo_model_path: str = Field(
        default=os.getenv("YOLO_MODEL_PATH", "yolov8x.pt"),
        description="Path to the YOLOv8x model"
    )
    use_easyocr: bool = Field(
        default=True,
        description="Enable EasyOCR for text extraction"
    )

class LLMSettings(BaseModel):
    groq_api_key: str = Field(
        default=os.getenv("GROQ_API_KEY", ""),
        description="Groq API Key for DeepSeek"
    )
    groq_model: str = Field(
        default=os.getenv("GROQ_MODEL", "deepseek-r1-distill-llama-70b"),
        description="Groq model name"
    )
    temperature: float = Field(
        default=float(os.getenv("GROQ_TEMPERATURE", 0.6)),
        description="Temperature for LLM responses"
    )
    max_completion_tokens: int = Field(
        default=int(os.getenv("GROQ_MAX_TOKENS", 4096)),
        description="Maximum tokens for LLM responses"
    )
    top_p: float = Field(
        default=float(os.getenv("GROQ_TOP_P", 0.95)),
        description="Top-p sampling parameter"
    )

class Settings(BaseModel):
    browser: BrowserSettings = BrowserSettings()
    vision: VisionSettings = VisionSettings()
    llm: LLMSettings = LLMSettings()
    max_steps: int = Field(
        default=int(os.getenv("MAX_STEPS", 100)),
        description="Maximum steps for the agent loop"
    )
    use_vision: bool = Field(
        default=os.getenv("USE_VISION", "true").lower() in ["true", "1"],
        description="Enable vision processing"
    )

def load_settings() -> Settings:
    return Settings()
