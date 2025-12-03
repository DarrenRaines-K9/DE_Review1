import os
from io import BytesIO
import pandas as pd
import boto3
from dotenv import load_dotenv
from src.logger import get_logger

logger = get_logger()
load_dotenv()


def transfer_raw_to_clean():
    """
    Read CSV files from MinIO raw bucket, capitalize column names,
    and upload to clean bucket.
    """
    # Get credentials from environment
    minio_url = os.getenv("MINIO_URL", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    raw_bucket = os.getenv("BUCKET_NAME", "raw")
    clean_bucket = "clean"

    # Connect to MinIO using boto3
    s3 = boto3.client(
        "s3",
        endpoint_url=minio_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    # Ensure buckets exist
    for bucket in [raw_bucket, clean_bucket]:
        try:
            s3.head_bucket(Bucket=bucket)
            logger.info(f"Bucket '{bucket}' already exists")
        except:
            s3.create_bucket(Bucket=bucket)
            logger.info(f"Created bucket '{bucket}'")

    # List all files in raw bucket
    response = s3.list_objects_v2(Bucket=raw_bucket)

    if "Contents" not in response:
        logger.info("No files found in raw bucket")
        return

    # Process each file
    for obj in response["Contents"]:
        file_name = obj["Key"]
        logger.info(f"Processing: {file_name}")

        # Read CSV from raw bucket
        file_obj = s3.get_object(Bucket=raw_bucket, Key=file_name)
        df = pd.read_csv(BytesIO(file_obj["Body"].read()))

        # Capitalize column names
        df.columns = df.columns.str.upper()

        # Write CSV to clean bucket
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)

        # Change filename to capitals_clean.csv
        clean_file_name = "capitals_clean.csv"
        # Put in clean bucket
        s3.put_object(
            Bucket=clean_bucket, Key=clean_file_name, Body=csv_buffer.getvalue()
        )
        logger.info(f"Uploaded: {clean_file_name}")

    logger.info("Transfer completed!")
