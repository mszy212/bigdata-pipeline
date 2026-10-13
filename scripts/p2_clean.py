from pyspark.sql import SparkSession

# Create SparkSession 创建会话
spark = SparkSession.builder.appName("p2_spark").getOrCreate()

# 从hdfs中读取数据
df = spark.read.csv('hdfs://localhost:9000/data/ods/orders_raw.csv', header=True, inferSchema=True)
# 统计
# print(df.count())
# print("空雷:", df.filter("user_id IS NULL").count())
# df.show(5)
# print("毒雷:", df.filter("order_price < 0").count())
# print("重复:", df.count() - df.dropDuplicates().count())
clean_df = df.filter("user_id IS NOT NULL") \
    .filter("order_price >= 0") \
    .dropDuplicates()
# 计算订单总价
clean_df = clean_df.withColumn("order_total", clean_df.order_price * clean_df.quantity)
clean_df.show(5)

# 保存写入hdfs
clean_df.write.mode("overwrite").parquet("hdfs://localhost:9000/data/dwd/orders_clean.csv")

check = spark.read.parquet("hdfs://localhost:9000/data/dwd/orders_clean.csv")
print(check.count())
# 运行： spark-submit p2_spark.py
# 开启hbase  start-hbase.sh
# 运行hbase网关 ： hbase-daemon.sh start thrift