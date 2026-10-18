from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, count, when

sparksessio = SparkSession.builder \
    .master("local[4]") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-azure:3.3.4") \
    .config("spark.driver.memory", "4g") \
    .appName("df_handling") \
    .getOrCreate()

df1 = sparksessio.read.csv("file1.csv", header=True, inferSchema=True)
df2 = sparksessio.read.csv("file2.csv", header=True, inferSchema=True)
df3 = sparksessio.read.csv("file3.csv", header=True, inferSchema=True)

df2 = df2.withColumnRenamed("times", "roi_times")
df2 = df2.withColumnRenamed("currency", "which_roi_currency")
df2 = df2.withColumnRenamed("percentage", "roi_percentage")

print("Schema for file1:")
df1.printSchema()

print("Schema for file2:")
df2.printSchema()

print("Schema for file3:")
df3.printSchema()


df1 = df1.withColumn("source_file", lit("file1.csv"))
df1 = df1.withColumn("processed_at", current_timestamp())

df2 = df2.withColumn("source_file", lit("file2.csv"))
df2 = df2.withColumn("processed_at", current_timestamp())

df3 = df3.withColumn("source_file", lit("file3.csv"))
df3 = df3.withColumn("processed_at", current_timestamp())


