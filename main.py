from src.logger import get_logger
from src.request_service import get_api_data
from src.minio_raw_to_clean import transfer_raw_to_clean
from src.minio_to_postgres import transfer_clean_to_postgres

logger = get_logger()


def run_pipeline():
    # get data from API
    logger.info("🐐Starting pipeline.")
    get_api_data(save_to_csv=True, output_file="capitals.csv")
    logger.info("✅ API data retrieval completed.")

    # Transfer data from raw to clean bucket in MINIO
    logger.info("🚚 Starting transfer from raw to clean bucket.")
    transfer_raw_to_clean()
    logger.info("✅ Transfer from raw to clean bucket completed.")

    # Transfer data from clean bucket to PostgreSQL
    logger.info("🚚 Starting transfer from clean bucket to PostgreSQL.")
    transfer_clean_to_postgres()
    logger.info("✅ Transfer from clean bucket to PostgreSQL completed.")


if __name__ == "__main__":
    run_pipeline()
