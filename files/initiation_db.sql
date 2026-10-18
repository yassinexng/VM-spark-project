=============

-- run once:
ALTER DATABASE [sql-db] SET COMPATIBILITY_LEVEL = 160;

-- MASTER KEY (run once):
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'P@0ssw#rd123';

-- 1. Trust your SAS token (run once):
CREATE DATABASE SCOPED CREDENTIAL [SAS_token]
WITH IDENTITY = 'SHARED ACCESS SIGNATURE',
SECRET = 'PASTE_SAS_TOKEN_HERE';

-- 2. Point at your container (run once):
CREATE EXTERNAL DATA SOURCE [sql_blob]
WITH (
    LOCATION = 'adls://output@storagenamehh.dfs.core.windows.net',
    CREDENTIAL = [SAS_token]
);

-- 3. Create views (run once):
CREATE VIEW v_file1 AS
SELECT * FROM OPENROWSET(
    BULK 'output_parquet/file1/*.parquet',
    DATA_SOURCE = 'sql_blob',
    FORMAT = 'PARQUET'
) AS [result];

CREATE VIEW v_file2 AS
SELECT * FROM OPENROWSET(
    BULK 'output_parquet/file2/*.parquet',
    DATA_SOURCE = 'sql_blob',
    FORMAT = 'PARQUET'
) AS [result];

CREATE VIEW v_file3 AS
SELECT * FROM OPENROWSET(
    BULK 'output_parquet/file3/*.parquet',
    DATA_SOURCE = 'sql_blob',
    FORMAT = 'PARQUET'
) AS [result];

-- 4. Query (run as often as you want):
SELECT TOP 10 * FROM v_file1;
SELECT TOP 10 * FROM v_file2;
SELECT TOP 10 * FROM v_file3;   