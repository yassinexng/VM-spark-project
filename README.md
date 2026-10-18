# Cryptocurrency Market Data Pipeline

## 1. Project Purpose & Current Implementation Status

This repository contains an end-to-end data engineering pipeline designed to collect live cryptocurrency market data, scale it synthetically into high-volume analytical datasets, transfer the data across an isolated mesh network, process and standardize it with Apache Spark (PySpark), export the transformed datasets to cloud object storage (Azure Blob / ADLS Gen2) as Parquet files, expose the data via SQL views, and visualize metrics through Apache Superset.

### Current Implementation Status
* **Status**: Functional prototype under active local dashboard development.
* **Verified Components**:
  * Infrastructure configuration with Terraform for Azure Linux VM extension & Tailscale mesh networking.
  * Python synthetic data generation using CoinGecko market inputs.
  * Local multi-threaded PySpark ingestion, schema standardization, audit column enrichment (`source_file`, `processed_at`).
  * Cloud Parquet export script configured for Azure Blob Storage via Hadoop Azure connector (`wasbs://` protocol with SAS token).
  * SQL script (`initiation_db.sql`) defining Azure SQL / Synapse Serverless views using `OPENROWSET` over the Parquet outputs.
  * Dockerized Apache Superset container setup (`docker-compose.yaml`) with `pymssql` driver installation for Azure SQL connectivity.
* **Known Limitations & Pending Tasks**:
  * Line 2 of `processer.py` contains a syntax error caused by an accidental shell command paste (`ssh vmw@...` inside the import statement) which prevents it from compiling in this directory without correction.
  * Cloud storage uploads, remote VM transfers, and live database queries require user-supplied Azure credentials and active remote network endpoints.

---

## 2. Pipeline Architecture

Below is a text diagram of the verified data pipeline flow:

```
+-------------------------------------------------------------------------------+
| 1. Remote Data Generation (Ubuntu Azure VM: newvm)                            |
|    - CoinGecko Market API -> get_data.py -> processer.py                      |
|    - Generates 1,000,000 rows each for 3 topics -> file1.csv, file2.csv, file3.csv|
|    - Managed by systemd: our_daemon.service                                   |
+-------------------------------------------------------------------------------+
                                      |
                                      | (Tailscale Mesh Network / SCP via sendfiles.py)
                                      v
+-------------------------------------------------------------------------------+
| 2. Local Ingestion & Storage (Local Machine)                                 |
|    - Landing directory: /home/ysn/Documents/projects/proji_2/files/           |
|    - Raw CSV files: file1.csv (~89.8 MB), file2.csv (~40.9 MB), file3.csv (~32.2 MB)|
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 3. Local Distributed Processing (PySpark: sspark.py)                          |
|    - SparkSession (local[4], 4GB driver memory)                               |
|    - Ingests raw CSVs, enforces schemas, renames columns (ROI metrics)        |
|    - Appends metadata: source_file, processed_at                              |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 4. Cloud Storage Export (PySpark Azure: azureprocessing.py)                   |
|    - Hadoop Azure connector (org.apache.hadoop:hadoop-azure:3.3.4)            |
|    - Writes partitioned Parquet files to Azure Blob Storage (output_parquet/) |
|    - Endpoint: wasbs://output@<storage_account>.blob.core.windows.net/        |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 5. Analytics Layer (Azure SQL / Synapse: initiation_db.sql)                   |
|    - Database scoped credentials & external data source ([sql_blob])          |
|    - SQL Views: v_file1, v_file2, v_file3 via OPENROWSET(BULK ... PARQUET)   |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| 6. Business Intelligence (Apache Superset: docker-compose.yaml)               |
|    - Containerized Superset with pymssql driver                               |
|    - Dashboards connected to Azure SQL views (port 8422)                      |
+-------------------------------------------------------------------------------+
```

---

## 3. Technology Stack & Roles

| Technology | Found in Repository | Role in Pipeline |
| :--- | :--- | :--- |
| **Python 3** | `*.py` | Core scripting language for data generation, synchronization, and PySpark driver execution. |
| **Apache Spark (PySpark)** | `sspark.py`, `azureprocessing.py` | Large-scale local data transformation, schema management, and Parquet serialization. |
| **Hadoop Azure Connector** | `sspark.py`, `azureprocessing.py` | Provides `wasbs://` filesystem adapter (`hadoop-azure:3.3.4`) for direct Azure Blob writes. |
| **Terraform** | `main.tf`, `terraform.tfstate` | Infrastructure as Code (IaC) to configure VM extensions and Tailscale authentication keys. |
| **Tailscale** | `main.tf`, `setup_vm.py`, `sendfiles.py` | Secure peer-to-peer mesh VPN allowing SCP transfers between local PC and cloud VM. |
| **Azure Linux VM** | `main.tf`, `setup_vm.py`, `our_daemon.service`| Remote compute host (`newvm`, Ubuntu, `Standard_B2ats_v2`) running data generation. |
| **systemd** | `our_daemon.service` | Linux daemon supervisor for automated, scheduled execution of `processer.py`. |
| **Azure Blob / ADLS Gen2** | `azureprocessing.py`, `initiation_db.sql` | Target cloud storage for partitioned Parquet datasets (`output_parquet`). |
| **Azure SQL / Synapse** | `initiation_db.sql` | Serverless query layer creating virtual views (`v_file1`, `v_file2`, `v_file3`) via `OPENROWSET`. |
| **Docker & Compose** | `docker-compose.yaml` | Container orchestration hosting Apache Superset. |
| **Apache Superset** | `docker-compose.yaml` | Business intelligence web dashboard platform (accessible on port 8422). |

---

## 4. Implementation vs. Planned Components

| Component | Status | Repository Evidence | Notes |
| :--- | :--- | :--- | :--- |
| **Local PySpark Processing** | **Implemented** | `sspark.py` | Validated local Spark session, schema definitions, and transformations. |
| **Azure Parquet Storage Script**| **Implemented** | `azureprocessing.py` | Configured with `wasbs://` writes; requires live Azure SAS credentials. |
| **Terraform IaC** | **Implemented & Validated** | `main.tf`, `terraform.tfstate` | Provider config and VM extension valid (`terraform validate` passes). |
| **Tailscale Integration** | **Configured** | `main.tf`, `setup_vm.py`, `sendfiles.py`| Terraform resources and SCP transfer scripts configured. |
| **systemd Daemon Service** | **Configured** | `our_daemon.service` | Unit configuration file present for deployment to `/etc/systemd/system/`. |
| **Azure SQL Views** | **Configured (Template)** | `initiation_db.sql` | SQL view definitions ready; requires execution on Azure SQL database. |
| **Apache Superset Dashboard** | **Implemented / In Progress** | `docker-compose.yaml` | Compose config validated (`docker compose config` passes); user creating charts. |
| **Azure Data Factory (ADF)** | **Planned / Absent** | None | Discussed in architectural notes, but no ADF JSON or Bicep templates exist. |
| **Apache Airflow** | **Absent** | None | Removed from design; no DAGs or Airflow configurations in repo. |
| **Apache Kafka** | **Absent** | None | Removed from design; no streaming brokers or producers in repo. |
| **Databricks** | **Absent** | None | Removed from design; PySpark is executed locally. |
| **GitHub Actions (CI/CD)** | **Planned / Absent** | None | No `.github/workflows` present. |
| **scikit-learn / MLflow** | **Planned / Absent** | None | No machine learning training or tracking code found in repo. |

---

## 5. Repository Layout & Dataset Paths

```
/home/ysn/Documents/projects/proji_2/files/
├── azureprocessing.py      # Azure Blob Parquet export using PySpark
├── docker-compose.yaml     # Apache Superset container definition & entrypoint
├── file1.csv               # 1,000,000 records of cryptocurrency market metrics (~89.8 MB)
├── file2.csv               # 1,000,000 records of ROI metrics (~40.9 MB)
├── file3.csv               # 1,000,000 records of ATH & market cap rank metrics (~32.2 MB)
├── get_data.py             # Fetches CoinGecko API data & generates synthetic data
├── initiation_db.sql       # Azure SQL setup: external data source, credentials & views
├── main.tf                 # Terraform config for VM extension & Tailscale key
├── our_daemon.service      # systemd service unit file for VM background execution
├── processer.py            # Orchestrator script for data generation & SCP dispatch
├── README.md               # Repository documentation and architecture guide
├── sendfiles.py            # SCP utility functions for file transfers
├── sendtovm.py             # Remote execution trigger script (local -> VM)
├── setup_vm.py             # Discovers Azure VM metadata, writes .env & triggers Terraform
├── sspark.py               # PySpark ETL script reading local CSV files
└── .terraform.lock.hcl     # Terraform dependency lock file
```

### Verified Input and Output Paths

* **Raw Input CSVs** (Local landing folder):
  * `file1.csv`: `ticket_symbol`, `live_price_usd`, `24_hour_trading_volume`, `highest_last24h`, `lowest_last24h`, `data_snapshot__date`
  * `file2.csv`: `times`, `currency`, `percentage`
  * `file3.csv`: `all_times_high_price`, `when_all_times_occured`, `market_cap_rank`
* **Transformed Parquet Outputs** (Cloud Azure Blob):
  * `wasbs://output@<storage_account>.blob.core.windows.net/output_parquet/file1`
  * `wasbs://output@<storage_account>.blob.core.windows.net/output_parquet/file2`
  * `wasbs://output@<storage_account>.blob.core.windows.net/output_parquet/file3`
* **SQL Server Views** (Exposed to Superset):
  * `v_file1`: Virtual table over `output_parquet/file1/*.parquet`
  * `v_file2`: Virtual table over `output_parquet/file2/*.parquet`
  * `v_file3`: Virtual table over `output_parquet/file3/*.parquet`

---

## 6. Setup and Execution Instructions

### Prerequisites
* Linux environment (Ubuntu / Debian recommended).
* Python 3.10+ with `pyspark`, `pandas`, `requests`, `numpy`, `python-dotenv`.
* Java OpenJDK 8 or 11 (required by PySpark).
* Docker & Docker Compose (for Apache Superset).
* Terraform 1.5+ (for infrastructure extension).
* Azure CLI (`az`) logged in (`az login`).

### Running the Components

#### 1. Infrastructure Validation
```bash
cd /home/ysn/Documents/projects/proji_2/files
terraform init
terraform validate
```

#### 2. Local PySpark Processing
To test and execute data transformation on the existing CSV files:
```bash
python3 sspark.py
```

#### 3. Uploading Parquet Data to Azure
Ensure the following variables are defined in your `.env` file:
* `storage_account`: Name of your Azure Storage Account.
* `sas_token`: Valid Shared Access Signature (SAS) token with Read/Write/List permissions on the `output` container.

Run the upload script:
```bash
python3 azureprocessing.py
```

#### 4. Launching Apache Superset
```bash
docker compose up -d
```
Access the Superset UI at `http://127.0.0.1:8422` (default credentials: `admin` / `admin`). Connect Apache Superset to Azure SQL using `mssql+pymssql://<username>:<password>@<server>.database.windows.net:1433/<database>`.

---

## 7. Observed Validation Results

All checks performed were strictly safe and non-destructive:

1. **Python Syntax Compilation**:
   * `setup_vm.py`, `sendfiles.py`, `sendtovm.py`, `get_data.py`, `sspark.py`, `azureprocessing.py`: **Pass (Exit Code 0)**.
   * `processer.py`: **SyntaxError** on line 2 (`from sendfilesssh vmw@...`).
2. **Terraform Validation**:
   * `terraform validate`: **Pass (Success! The configuration is valid.)**.
3. **Docker Compose Validation**:
   * `docker compose config --dry-run`: **Pass (Valid YAML, container port 8422 correctly mapped)**.
4. **Data File Verification**:
   * `file1.csv`: 1,000,001 rows (header + 1M records), 89,780,134 bytes.
   * `file2.csv`: 1,000,001 rows (header + 1M records), 40,859,477 bytes.
   * `file3.csv`: 1,000,001 rows (header + 1M records), 32,229,194 bytes.
   * Column definitions verified to match `get_data.py` and `sspark.py`.

---

## 8. Limitations & Manual Azure Setup Required

1. **Syntax Fix Needed in `processer.py`**:
   Line 2 contains an accidental bash command paste and should be updated from:
   `from sendfilesssh vmw@100.112.78.72 "ls /home/vmw/folder/files/"    import sendback_file`
   to:
   `from sendfiles import sendback_file`
2. **Azure Storage Account & Container**:
   A container named `output` must exist on the target Azure Storage Account, and a SAS token must be generated and stored in `.env`.
3. **Database Setup (`initiation_db.sql`)**:
   Line 1 contains non-SQL divider characters (`=============`) which must be removed or commented out before execution in SQL Server. In addition, the placeholder credentials (`PASTE_SAS_TOKEN_HERE` and `storagenamehh`) must be replaced with your actual Azure resource details.
4. **Tailscale Configuration**:
   The local machine (`ysnslaptop`) and the remote VM (`newvm`) must be authenticated to the same Tailnet to enable passwordless SCP/SSH data transfer.
