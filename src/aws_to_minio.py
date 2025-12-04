import os
from io import BytesIO
import boto3
from dotenv import load_dotenv
from src.logger import get_logger

logger = get_logger()
load_dotenv()


def transfer_aws_to_minio():
    """
    Read capitals_clean.csv from AWS S3 bucket and upload to MinIO gold bucket.
    """
    # Get AWS credentials from environment
    aws_profile = os.getenv("AWS_PROFILE")
    aws_region = os.getenv("AWS_REGION")
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    s3_folder_prefix = os.getenv("S3_FOLDER_PREFIX")

    # Get MinIO credentials from environment
    minio_url = os.getenv("MINIO_URL", "http://localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    gold_bucket = "gold"

    # Specific file to transfer
    target_file = "capitals_clean.csv"

    # Connect to AWS S3 using boto3 with profile
    session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
    aws_s3 = session.client("s3")

    # Connect to MinIO using boto3
    minio_s3 = boto3.client(
        "s3",
        endpoint_url=minio_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    # Ensure gold bucket exists in MinIO
    try:
        minio_s3.head_bucket(Bucket=gold_bucket)
        logger.info(f"Bucket '{gold_bucket}' already exists in MinIO")
    except:
        minio_s3.create_bucket(Bucket=gold_bucket)
        logger.info(f"Created bucket '{gold_bucket}' in MinIO")

    # Construct the full S3 key for the target file
    s3_key = f"{s3_folder_prefix}/{target_file}" if s3_folder_prefix else target_file

    logger.info(f"Attempting to download '{s3_key}' from AWS S3 bucket '{s3_bucket}'")

    try:
        # Download file from AWS S3
        file_obj = aws_s3.get_object(Bucket=s3_bucket, Key=s3_key)
        file_content = file_obj["Body"].read()
        logger.info(f"Successfully downloaded '{s3_key}' from AWS S3")

        # Upload to MinIO gold bucket
        minio_s3.put_object(Bucket=gold_bucket, Key=target_file, Body=file_content)
        logger.info(f"Successfully uploaded '{target_file}' to MinIO gold bucket")

        logger.info(
            f"Transfer completed! '{target_file}' transferred from AWS S3 to MinIO gold bucket!🚚"
        )

    except Exception as e:
        logger.error(f"Failed to transfer '{s3_key}': {str(e)}")
        raise
