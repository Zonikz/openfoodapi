"""Configuration management"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    DEBUG: bool = True
    PORT: int = 8000
    
    # Models
    MODEL_NAME: str = "food101-resnet50"
    MODEL_PATH: str = "./models/food101_resnet50.pt"
    ENABLE_DETECTOR: bool = False
    DETECTOR_MODEL: str = "yolov8n.pt"
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/gains_food.db"
    
    # Inference
    MAX_IMAGE_SIZE: int = 1024
    TOP_K_PREDICTIONS: int = 5
    CONFIDENCE_THRESHOLD: float = 0.1
    
    # Data sources
    COFID_CSV_PATH: str = "./seeds/data/cofid.csv"
    OFF_DUMP_PATH: str = "./seeds/data/openfoodfacts.csv"
    USDA_CSV_PATH: str = "./seeds/data/usda.csv"
    
    # Performance
    TORCH_NUM_THREADS: int = 4
    USE_GPU: bool = False
    
    # GAINS Scoring weights
    GAINS_PROTEIN_WEIGHT: float = 0.25
    GAINS_CARB_WEIGHT: float = 0.20
    GAINS_FAT_WEIGHT: float = 0.15
    GAINS_PROCESSING_WEIGHT: float = 0.25
    GAINS_TRANSPARENCY_WEIGHT: float = 0.15
    
    # Paths
    @property
    def data_dir(self) -> Path:
        """Data directory"""
        path = Path("./data")
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def models_dir(self) -> Path:
        """Models directory"""
        path = Path("./models")
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def label_map_path(self) -> Path:
        """Label map file"""
        return Path("./app/mapping/label_map.json")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
