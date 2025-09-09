from loguru import logger
from pathlib import Path
import sys

def setup_logging(data_dir: str):
    Path(data_dir, "logs").mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(Path(data_dir, "logs", "backend.log"), rotation="5 MB", retention=5, level="INFO")