# DE_Review1 - Data Engineering Pipeline Project

First Self Assessment for Data Engineering

## Project Overview

This is a **Data Engineering ETL Pipeline** that demonstrates a multi-stage data movement workflow through various storage layers (Bronze → Silver → Gold architecture pattern). The project fetches country/capital data from a REST API and orchestrates its movement through local object storage (MinIO), relational database (PostgreSQL), cloud storage (AWS S3), and back to local object storage.

## Architecture & Data Flow

### Pipeline Stages (5 Steps)

**Stage 1: Data Ingestion** (`src/request_service.py`)

- **Source:** REST Countries API (`https://restcountries.com/v3.1/all`)
- **Action:** Fetches 250 country records with fields: name, capital, population, region, subregion, languages, currencies, flags, area, timezones
- **Output:** Saves raw data to `capitals.csv` in project root
- **Technology:** `requests` library + `pandas` DataFrame

**Stage 2: Bronze → Silver Transformation** (`src/minio_raw_to_clean.py`)

- **Source:** MinIO "raw" bucket (Bronze layer)
- **Transformation:** Capitalizes all column names (e.g., `name` → `NAME`)
- **Destination:** MinIO "clean" bucket (Silver layer) as `capitals_clean.csv`
- **Technology:** MinIO via boto3 S3 client
- **Pattern:** Object storage-to-object storage transformation

**Stage 3: Silver → Relational Database** (`src/minio_to_postgres.py`)

- **Source:** MinIO "clean" bucket
- **Action:**
  - Dynamically creates PostgreSQL table `capitals_clean` with TEXT columns
  - Drops existing table if present (destructive operation)
  - Bulk inserts 250 rows using `execute_values` for performance
- **Destination:** PostgreSQL database `de` on localhost:5432
- **Technology:** `psycopg2` for PostgreSQL, boto3 for MinIO

**Stage 4: Database → Cloud Storage** (`src/postgres_to_aws.py`)

- **Source:** PostgreSQL `capitals_clean` table
- **Action:**
  - Queries all public tables from PostgreSQL
  - Exports each table to CSV format
  - Uploads to AWS S3 with folder prefix structure
- **Destination:** AWS S3 bucket `de-october-individual-folders` under `Raines/` prefix
- **Technology:** AWS boto3 with SSO profile authentication

**Stage 5: Cloud → Local Gold Layer** (`src/aws_to_minio.py`)

- **Source:** AWS S3 `Raines/capitals_clean.csv`
- **Action:** Downloads file from S3 and uploads to MinIO "gold" bucket
- **Destination:** MinIO "gold" bucket (final gold layer)
- **Pattern:** Cloud repatriation / hybrid cloud architecture

## Technical Stack

### Core Technologies

- **Python 3.13** (latest version)
- **Data Processing:** `pandas` for DataFrame operations
- **HTTP Client:** `requests` for API calls
- **Databases:**
  - `psycopg2-binary` for PostgreSQL
  - `pymysql`, `pyodbc` installed but unused
- **Object Storage:** `boto3` for both MinIO (S3-compatible) and AWS S3
- **Configuration:** `python-dotenv` for environment variables
- **ORM:** `sqlalchemy` installed but not used in code

### Infrastructure (Docker Compose)

`docker-compose.yml` provisions:

1. **PostgreSQL 15**

   - Database: `de`
   - Credentials: `myuser:mypassword`
   - Port: 5432
   - Persistent volume: `db_data`

2. **MinIO (S3-compatible object storage)**
   - API Port: 9000
   - Console Port: 9001
   - Credentials: `minioadmin:minioadmin`
   - Persistent volume: `minio_data`
   - Three buckets created during execution: `raw`, `clean`, `gold`

## Project Structure

```
DE_Review1/
├── main.py                      # Pipeline orchestration entry point
├── src/
│   ├── logger.py               # Centralized logging configuration
│   ├── request_service.py      # API data ingestion
│   ├── minio_raw_to_clean.py   # Bronze → Silver transformation
│   ├── minio_to_postgres.py    # Silver → PostgreSQL loading
│   ├── postgres_to_aws.py      # PostgreSQL → AWS S3 export
│   └── aws_to_minio.py         # AWS S3 → MinIO gold repatriation
├── logs/                        # Daily pipeline execution logs
├── capitals.csv                 # Raw data output
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Infrastructure definition
└── .env                         # Configuration & credentials
```

## Setup & Installation

### Prerequisites

- Python 3.13+
- Docker & Docker Compose
- AWS CLI configured with SSO
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd DE_Review1
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   - Copy `.env.example` to `.env` (if applicable)
   - Update credentials and endpoints as needed

5. **Start infrastructure**

   ```bash
   docker-compose up -d
   ```

6. **Run the pipeline**
   ```bash
   python main.py
   ```

## Configuration

### Environment Variables (.env)

**MinIO Configuration:**

```
MINIO_URL=http://localhost:9000
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
BUCKET_NAME=
```

**PostgreSQL Configuration:**

```
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=5432
DB_NAME=
```

**AWS S3 Configuration:**

```
AWS_PROFILE=
AWS_REGION=
S3_BUCKET_NAME=
S3_FOLDER_PREFIX=
```

**API Configuration:**

```
API_BASE_URL=https://restcountries.com/v3.1/all?fields=name,capital,population,region,subregion,languages,currencies,flags,area,timezones
```

## Data Sample

The pipeline processes **250 country records** with the following structure:

**Fields:**

- `flags`: Dictionary with PNG/SVG URLs and alt text
- `name`: Nested dict with common/official/native names
- `currencies`: Currency codes with names and symbols
- `capital`: Array of capital cities
- `region`: Continental region (Americas, Europe, Asia, etc.)
- `subregion`: More specific region
- `languages`: Language codes and names
- `area`: Numeric area in km²
- `population`: Current population count
- `timezones`: Array of UTC offset strings

## Logging System

- **Pattern:** Centralized logger factory function
- **Configuration:**
  - Dual output: Console (stdout) + File
  - Log files: `logs/pipeline_YYYYMMDD.log`
  - Format: Timestamp - Level - Message
  - Auto-creates logs directory
- **Visual indicators:** Emoji-based progress tracking (🐐 🚚 ✅)

## Execution Metrics

**Typical Pipeline Run:**

- ✅ 250 records fetched from API (~365ms)
- ✅ Raw data saved to CSV
- ✅ Transformed and uploaded to clean bucket
- ✅ 250 rows inserted into PostgreSQL table
- ✅ Data exported to AWS S3 (~1.5s upload time)
- ✅ Data retrieved from S3 and stored in gold bucket
- **Total execution time:** ~3 seconds

## Architectural Patterns Demonstrated

1. **Medallion Architecture:** Bronze (raw) → Silver (clean) → Gold (final)
2. **ETL Pipeline:** Extract (API) → Transform (column capitalization) → Load (multiple destinations)
3. **Infrastructure as Code:** Docker Compose for reproducible environments
4. **Configuration Management:** Environment variables for all credentials
5. **Hybrid Cloud:** Mix of local (MinIO, PostgreSQL) and cloud (AWS S3) storage
6. **Idempotent Operations:** Bucket/table creation checks before operations

## Key Technical Features

### Strengths

- ✅ Clear separation of concerns - Each module handles one transformation
- ✅ Comprehensive logging - Full audit trail in log files
- ✅ Dual storage paradigm - Both object storage and relational DB
- ✅ AWS SSO integration - Modern authentication pattern
- ✅ Containerized dependencies - Easy local setup with Docker
- ✅ Modular design - Easy to extend or modify individual stages

### Technical Considerations

- Data type handling: All PostgreSQL columns are TEXT (no type optimization)
- Error handling: Some bare `except:` clauses could be more specific
- Destructive operations: `DROP TABLE IF EXISTS` loses historical data
- No incremental loading: Full table replacement on each run
- Hardcoded bucket names: "clean" and "gold" not configurable via .env
- Single file assumption: Pipeline designed for one CSV file
- Unused dependencies: sqlalchemy, pymysql, pyodbc installed but not used
- No data validation: API response not validated before processing

## Data Pipeline Metrics

- **Source Data:** 250 country records
- **Total Pipeline Stages:** 5
- **Storage Systems:** 4 (MinIO, PostgreSQL, AWS S3, MinIO again)
- **Data Formats:** CSV throughout
- **Transformation Steps:** 1 (column name capitalization)
- **Average Execution Time:** ~3 seconds
- **Log File Size:** ~20KB per day

## Purpose & Learning Objectives

This project demonstrates:

- Multi-stage ETL pipeline development
- Working with diverse storage systems (object storage, relational DB, cloud storage)
- API integration and data ingestion
- Infrastructure provisioning with Docker
- Python data engineering stack proficiency
- AWS cloud services integration
- Logging and observability practices

## Troubleshooting

**MinIO Connection Issues:**

- Ensure Docker containers are running: `docker-compose ps`
- Check MinIO console at `http://localhost:9001`

**PostgreSQL Connection Issues:**

- Verify PostgreSQL is running: `docker-compose logs db`
- Test connection: `psql -h localhost -U myuser -d de`

**AWS S3 Access Issues:**

- Verify AWS SSO login: `aws sso login --profile draines20`
- Check credentials: `aws sts get-caller-identity --profile draines20`

## Future Enhancements

Potential improvements for production readiness:

- Add data quality validation and schema enforcement
- Implement incremental loading with CDC patterns
- Add proper error handling with retries and dead letter queues
- Implement data versioning and lineage tracking
- Add unit and integration tests
- Implement proper type inference for PostgreSQL columns
- Add monitoring and alerting capabilities
- Implement configuration-driven bucket naming
- Add support for multiple file processing
- Implement proper secret management (e.g., AWS Secrets Manager)

## License

This project is for educational and assessment purposes.

## Contact

For questions or feedback regarding this Data Engineering assessment project, please refer to the project repository or contact information provided separately.
