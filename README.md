# Crypto Market Data Pipeline

A hybrid, end-to-end data pipeline that pulls live CoinGecko cryptocurrency market data on an Azure Linux VM, algorithmically expands it into large analytical CSV datasets (3 million rows / 12 million data cells per batch), securely syncs the files to my local laptop over a private Tailscale mesh network, transforms and enriches them using PySpark, writes partitioned Parquet files directly to Azure Blob Storage, exposes the data through serverless Azure SQL views, and serves interactive BI dashboards in Apache Superset.

```
Azure VM (generate) → Tailscale (SCP) → Laptop (PySpark) → Azure Blob (Parquet) → Azure SQL views → Superset
```

---

## Architecture & How the Pipeline Works

The pipeline is split across two environments: a remote cloud VM that acts as the data generator and scheduler, and a local machine that handles distributed processing, cloud storage dispatch, and visualization.

```
+---------------------------------------------------------------------------------------+
| 1. Azure Linux VM ("newvm" in Sweden Central)                                         |
|    - Runs get_data.py to pull spot market data from CoinGecko API                     |
|    - Scales data synthetically to 1,000,000 rows across 3 relational topics           |
|    - Managed by systemd (our_daemon.service) running processer.py every 45s           |
+---------------------------------------------------------------------------------------+
                                           |
                                           | Tailscale WireGuard Mesh Tunnel (P2P SCP)
                                           v
+---------------------------------------------------------------------------------------+
| 2. Local Workstation (Landing Directory)                                              |
|    - Receives file1.csv (~89.8 MB), file2.csv (~40.9 MB), file3.csv (~32.2 MB)        |
|    - 3,000,000 rows total (~163 MB uncompressed)                                      |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| 3. Local Distributed Processing (PySpark: sspark.py)                                  |
|    - Multi-threaded SparkSession (local[4], 4GB driver memory)                        |
|    - Standardizes schemas, renames ROI metrics, injects source_file & processed_at    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| 4. Cloud Object Storage (Azure Blob / ADLS Gen2: azureprocessing.py)                  |
|    - Uses hadoop-azure:3.3.4 connector with wasbs:// protocol and SAS token auth      |
|    - Writes snappy-compressed columnar Parquet files into output_parquet/             |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| 5. Zero-Copy Query Virtualization (Azure SQL Serverless: initiation_db.sql)           |
|    - External data source [sql_blob] pointing to the Parquet container                |
|    - Creates virtual views (v_file1, v_file2, v_file3) using T-SQL OPENROWSET         |
|    - Direct queries over cloud Parquet without duplicate data copies                  |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| 6. BI & Analytics Layer (Apache Superset: docker-compose.yaml)                        |
|    - Containerized Superset on port 8422 with dynamic pymssql driver setup            |
|    - Connects directly to Azure SQL views for live dashboards                         |
+---------------------------------------------------------------------------------------+
```

---

## Compute Environment & Resource Footprint

The remote generation runs on an intentionally lean Azure VM to prove that high-throughput batch generation doesn't need expensive compute:

* **Host & OS:** Ubuntu 24.04.5 LTS (x86_64, Linux Kernel `6.17.0-1011-azure`, Hyper-V UEFI Release v4.1)
* **Processor:** 2 virtual CPUs powered by an **AMD EPYC 7763** server chip @ 3.241 GHz
* **Memory Footprint:** **892 MiB total RAM** — uses only **~253 MiB** while actively running the generation loop
* **System Stability:** **174+ days** of continuous uptime with zero memory leaks

---

## Setup & Prerequisites

### 1. Log in to Azure
Make sure the Azure CLI is installed and authenticated to your subscription:
```bash
az login
```

### 2. Configure Secrets in `.env`
Create a `.env` file in the project folder with your credentials. These are used by both Python scripts and Terraform:
```ini
# Tailscale API key (used by Terraform to mint auth keys for the VM)
tailscale_api=tskey-api-xxxxxxxxxxxxxxxxx

# VM administrative password
admin_password=YourSecurePassword123!

# Azure Storage Account & SAS token for Parquet upload and SQL views
storage_account=yourstorageaccountname
sas_token=sp=r&st=...&sig=...
```

### 3. Run the Setup Script
The `setup_vm.py` script automatically inspects your Azure subscription for the VM, writes all required Terraform input variables (`TF_VAR_*`) into `.env`, and initializes Terraform:
```bash
python3 setup_vm.py
```

What `setup_vm.py` does behind the scenes:
1. Calls `az vm list` and `az vm show` to extract the VM's ID, Resource Group, Location, Size (`Standard_B2ats_v2`), OS disk caching, image reference, and Network Interface ID.
2. Writes these values to `.env` as `TF_VAR_subscription`, `TF_VAR_ressource_group_name`, `TF_VAR_vm_name`, `TF_VAR_location`, `TF_VAR_size`, etc.
3. Automatically triggers `terraform init`, `terraform plan`, and `terraform apply`.

### 4. Check the Terraform Plan
You can verify the infrastructure state at any time:
```bash
terraform plan
```

---

## How the Code Gets to the VM and Runs

1. **Automatic Network Join on Boot:**
   Terraform installs Tailscale onto the Azure VM using an `azurerm_virtual_machine_extension` (CustomScript). Terraform creates a reusable, non-ephemeral Tailscale auth key (`tailscale_tailnet_key.vm_auth_key`) and injects it into the VM extension's startup script. As soon as the VM provisions, it automatically connects to your private Tailnet under the hostname `newvm` without requiring manual SSH logins or opening public inbound ports.

2. **Pushing Code to the VM:**
   The `sendtovm.py` script sends the application files directly to the remote VM over SCP across Tailscale:
   ```bash
   python3 sendtovm.py
   ```
   This copies `processer.py`, `get_data.py`, `sendfiles.py`, and `our_daemon.service` into `/home/vmw/folder/files/` on the VM.

3. **Background Daemon Management:**
   The data generator is managed by Linux systemd through `our_daemon.service`. The service executes `processer.py` using the VM's Python virtual environment. If the process ever exits or encounters an issue, systemd automatically restarts it after 45 seconds (`RestartSec=45s`).

To manually install and start the service on the VM:
```bash
# SSH into the VM over Tailscale
ssh vmw@newvm

# Copy unit file to systemd directory and start it
sudo cp our_daemon.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now our_daemon

# Check service status and live logs
sudo systemctl status our_daemon
journalctl -u our_daemon -f
```

---

## Datasets Generated

The generator (`get_data.py`) takes live spot prices, trading volumes, and ROI percentages from the CoinGecko REST API and uses NumPy to scale them into 3 distinct relational CSV files with 1,000,000 rows each:

| Dataset | Primary Columns | Rows | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`file1.csv`** | `ticket_symbol`, `live_price_usd`, `24_hour_trading_volume`, `highest_last24h`, `lowest_last24h`, `data_snapshot__date` | 1,000,000 | ~89.8 MB | Market pricing, trading liquidity, and daily volatility spreads. |
| **`file2.csv`** | `times`, `currency`, `percentage` | 1,000,000 | ~40.9 MB | Historical Return on Investment (ROI) horizons, base currencies, and percentage returns. |
| **`file3.csv`** | `all_times_high_price`, `when_all_times_occured`, `market_cap_rank` | 1,000,000 | ~32.2 MB | All-time high (ATH) benchmark records, occurrence dates, and market cap ranks. |
| **Total** | **12 Columns Total** | **3,000,000** | **~163 MB** | **12,000,000 individual data cells generated per cycle.** |

Once generated, `processer.py` calls `sendback_file()` from `sendfiles.py` to transfer the three CSV files back to the local laptop landing directory over Tailscale.

---

## Files in the Repository

| File | Purpose |
| :--- | :--- |
| `main.tf` | Terraform configuration: imports existing Azure VM, creates reusable Tailscale key, and provisions Tailscale VM extension. |
| `setup_vm.py` | Python automation: queries Azure CLI for VM metadata, populates `.env` variables, and runs Terraform commands. |
| `get_data.py` | Core data generator: pulls from CoinGecko API and algorithmically scales the data into three 1M-row DataFrames. |
| `processer.py` | Orchestration script: calls generation functions, writes local CSVs on the VM, and triggers SCP dispatch back to the laptop. |
| `sendfiles.py` | SCP utility functions for pushing scripts to the VM and syncing CSV datasets back to the local machine. |
| `sendtovm.py` | Automated local deployment script: sends updated scripts to the VM over SCP and triggers execution via SSH. |
| `our_daemon.service` | Linux systemd service configuration file for continuous, supervised execution on the VM (`RestartSec=45s`). |
| `sspark.py` | Local Apache Spark ETL: initializes 4-core SparkSession, enforces schemas, renames ROI columns, and injects lineage metadata. |
| `azureprocessing.py` | Cloud export script: uses `hadoop-azure` connector (`wasbs://`) to write partitioned, Snappy-compressed Parquet to Azure Blob Storage. |
| `initiation_db.sql` | SQL setup script: creates database-scoped SAS credential, external data source, and `OPENROWSET` views in Azure SQL. |
| `docker-compose.yaml` | Container definition for Apache Superset: maps port `8422`, configures admin credentials, and automatically installs `pymssql`. |
| `requirements.txt` | Python library dependencies (`pyspark`, `pandas`, `numpy`, `requests`, `python-dotenv`, `pymssql`). |
| `.gitignore` | Protects secrets (`.env`), Terraform state files, Python caches, and large raw CSV datasets from Git. |

---

## Running the Local Steps

Once the CSV files have landed in the local directory, execute the pipeline steps in order:

### 1. Process the CSVs with PySpark
Ingests the three CSV files, enforces column data types, renames ROI columns for semantic clarity, and adds `source_file` and `processed_at` timestamp audit fields:
```bash
python3 sspark.py
```

### 2. Upload Parquet to Azure Blob Storage
Uploads the transformed DataFrames as partitioned Snappy Parquet files directly into your Azure Storage container:
```bash
python3 azureprocessing.py
```
*Note: Make sure `storage_account` and `sas_token` are set in your `.env` file before running.*

### 3. Create Azure SQL Serverless Views
Open `initiation_db.sql` in Azure Data Studio, VS Code, or Azure Portal Query Editor. Replace `PASTE_SAS_TOKEN_HERE` and `storagenamehh` with your real Azure Storage details, and run the script:
```sql
-- Creates virtual views querying Parquet files directly from Azure Blob Storage
CREATE VIEW v_file1 AS
SELECT * FROM OPENROWSET(
    BULK 'output_parquet/file1/*.parquet',
    DATA_SOURCE = 'sql_blob',
    FORMAT = 'PARQUET'
) AS [result];
```

### 4. Launch Apache Superset
Start the Superset container using Docker Compose:
```bash
docker compose up -d
```
Access the Superset UI at `http://127.0.0.1:8422` (default login: `admin` / `admin`).

Connect Superset to Azure SQL by navigating to **Data → Databases → + Database** and entering your SQLAlchemy connection URI:
```
mssql+pymssql://<user>:<password>@<server>.database.windows.net:1433/<database>
```
Once connected, create datasets from `v_file1`, `v_file2`, and `v_file3` to build live dashboards tracking trading volume, price volatility, and ROI distributions.

---

## Requirements

* **Local Machine:** Linux (Ubuntu/Debian recommended), Python 3.10+, Java OpenJDK 8 or 11 (required by PySpark), Docker with Compose, Terraform 1.5+, Azure CLI (`az`).
* **Networking:** A Tailscale account with both your local machine and the Azure VM authenticated to the same Tailnet.
* **Cloud Resources:** An active Azure subscription with an Azure Linux VM, an Azure Blob Storage account with an `output` container, and an Azure SQL database.

---

## Status

- **Working & Verified:** 
  - Terraform configuration validates cleanly (`terraform validate` passes).
  - Python scripts compile and run without errors.
  - Local PySpark processing runs on 4 driver cores with schema enforcement.
  - Docker Compose configuration validates cleanly and starts Superset on port `8422`.
  - All three raw CSV datasets generated (exactly 1,000,001 rows each).
- **Needs Active Cloud Credentials:** Cloud upload to Azure Blob, remote SCP transfer over Tailscale, and live SQL view queries require active credentials in `.env`.
