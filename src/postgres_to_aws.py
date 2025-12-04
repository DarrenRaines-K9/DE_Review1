import os
from io import BytesIO
import pandas as pd
import boto3
import psycopg2
from dotenv import load_dotenv
from src.logger import get_logger

logger = get_logger()
load_dotenv()


def transfer_postgres_to_aws():
    """
    Read data from PostgreSQL and upload to AWS S3 bucket.
    """
    # Get PostgreSQL credentials from environment
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    # Get AWS credentials from environment
    aws_profile = os.getenv("AWS_PROFILE")
    aws_region = os.getenv("AWS_REGION")
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    s3_folder_prefix = os.getenv("S3_FOLDER_PREFIX")

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
    )
    cursor = conn.cursor()

    # Get list of all tables in the database
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """
    )
    tables = cursor.fetchall()

    if not tables:
        logger.info("No tables found in PostgreSQL database")
        conn.close()
        return

    # Connect to AWS S3 using boto3 with profile
    session = boto3.Session(profile_name=aws_profile, region_name=aws_region)
    s3 = session.client("s3")

    # Process each table
    for (table_name,) in tables:
        logger.info(f"Processing table: {table_name}")

        # Query all data from table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # Get column names
        cursor.execute(
            f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
            """
        )
        columns = [col[0] for col in cursor.fetchall()]

        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)
        logger.info(f"Retrieved {len(df)} rows from {table_name}")

        # Convert DataFrame to CSV in memory
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)

        # Upload to S3 with folder prefix
        file_name = f"{s3_folder_prefix}/{table_name}.csv"
        s3.put_object(Bucket=s3_bucket, Key=file_name, Body=csv_buffer.getvalue())
        logger.info(f"Uploaded {file_name} to S3 bucket: {s3_bucket}")

    cursor.close()
    conn.close()
    logger.info("Transfer to AWS S3 completed!")
