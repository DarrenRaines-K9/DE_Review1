import logging
import os
from datetime import datetime


def get_logger():

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_filename = f"{log_dir}/pipeline_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_filename)],
    )
    logger = logging.getLogger()
    return logger
