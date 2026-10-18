from sspark import sparksessio
import os
from dotenv import load_dotenv

from sspark import df1,df2,df3

load_dotenv()

storage_account = os.getenv("storage_account")
#the Shared Access Signature token must be set to all 7 permissions except: immutable storage 
#it's the BLOB SAS token from within the: storage account -> storageuchose -> shared access signature, pick the container, service and object

container="output"
sas_token = os.getenv("sas_token")



hadoop_conf = sparksessio.sparkContext._jsc.hadoopConfiguration()
hadoop_conf.set(f"fs.azure.sas.{container}.{storage_account}.blob.core.windows.net", sas_token)   

output_path = f"wasbs://{container}@{storage_account}.blob.core.windows.net/output_parquet"   

print("Partitions: ")
print("df1: ", df1.rdd.getNumPartitions())
print("df2: ", df2.rdd.getNumPartitions())
print("df3: ", df3.rdd.getNumPartitions())


df1.write.format("parquet").mode("overwrite").save(f"{output_path}/file1")
df2.write.format("parquet").mode("overwrite").save(f"{output_path}/file2")
df3.write.format("parquet").mode("overwrite").save(f"{output_path}/file3")


print(f"DFs written to {output_path}. ")

#let's see the data written:
df_read1 = sparksessio.read.format("parquet").load(f"{output_path}/file1")
df_read2 = sparksessio.read.format("parquet").load(f"{output_path}/file2")
df_read3 = sparksessio.read.format("parquet").load(f"{output_path}/file3")

df_read1.show()
df_read2.show()
df_read3.show()