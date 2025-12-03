import requests
import pandas as pd
import os
from dotenv import load_dotenv
from src.logger import get_logger

logger = get_logger()

load_dotenv()


def get_api_data(save_to_csv=True, output_file="capitals.csv"):
    api_url = os.getenv("API_BASE_URL")
    logger.info(f"Fetching data from API: {api_url}")

    response = requests.get(api_url)
    response.raise_for_status()

    data = response.json()
    capitals = pd.DataFrame(data)

    logger.info(f"Total records fetched: {len(capitals)}")

    if save_to_csv and not capitals.empty:
        capitals.to_csv(output_file, index=False)
        logger.info(f"Data saved to {output_file}")

    return capitals
