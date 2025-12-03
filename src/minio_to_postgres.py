import os
from io import BytesIO
import pandas as pd
import boto3
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from src.logger import get_logger

logger = get_logger()
load_dotenv()


def transfer_clean_to_postgres():
    """
    Read CSV files from MinIO clean bucket and upload to PostgreSQL.
    """
    # Get MinIO credentials from environment
    minio_url = os.getenv("MINIO_URL", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    clean_bucket = "clean"

    # Get PostgreSQL credentials from environment
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    # Connect to MinIO using boto3
    s3 = boto3.client(
        "s3",
        endpoint_url=minio_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
    )
    cursor = conn.cursor()

    # List all files in clean bucket
    response = s3.list_objects_v2(Bucket=clean_bucket)

    if "Contents" not in response:
        logger.info("No files found in clean bucket")
        conn.close()
        return

    # Process each file
    for obj in response["Contents"]:
        file_name = obj["Key"]
        logger.info(f"Processing: {file_name}")

        # Read CSV from clean bucket
        file_obj = s3.get_object(Bucket=clean_bucket, Key=file_name)
        df = pd.read_csv(BytesIO(file_obj["Body"].read()))

        # Derive table name from file name (remove .csv extension)
        table_name = file_name.replace(".csv", "").lower()

        # Create table dynamically based on DataFrame columns
        create_table_query = f"DROP TABLE IF EXISTS {table_name};"
        cursor.execute(create_table_query)

        # Generate CREATE TABLE statement
        column_defs = []
        for col in df.columns:
            # Use TEXT for simplicity, can be refined based on data types
            column_defs.append(f"{col} TEXT")

        create_table_query = f"CREATE TABLE {table_name} ({', '.join(column_defs)});"
        cursor.execute(create_table_query)
        logger.info(f"Created table: {table_name}")

        # Insert data into table
        columns = df.columns.tolist()
        values = [tuple(row) for row in df.to_numpy()]

        insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s"
        execute_values(cursor, insert_query, values)

        conn.commit()
        logger.info(f"Inserted {len(df)} rows into {table_name}")

    cursor.close()
    conn.close()
    logger.info("Transfer to PostgreSQL completed!")
