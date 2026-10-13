# 导入模块
import hashlib   # 算MD5.主要用来设计rowkey  
import happybase # 访问HBase 
from pyspark.sql import SparkSession # 
from pyspark.sql.functions import sum as _sum, col
# 启动happybase
# hbase-daemon.sh start thrift

# 创建SparkSession
spark = SparkSession.builder.appName("p3_hbase").getOrCreate()

# 读取数据
df = spark.read.parquet('hdfs://localhost:9000/data/dwd/orders_clean.csv')

# df.show()
# 统计数据商品总销售额和商品总销售量
stat = df.groupBy('product_id').agg(
    _sum('order_price').alias('total_price'),
    _sum('quantity').alias('total_quantity'))

# stat.orderBy(col('product_id')).show(50)

# 创建HBase连接
conn = happybase.Connection('localhost', 9090)

# 创建表(判断表是否存在)
if b'product_stat' not in conn.tables():
    conn.create_table('product_stat', {'stat': dict()})
    print('创建表成功')
table = conn.table('product_stat')

# 将数据带回python
rows = stat.collect()
#  循环 put： md5 RowKey 设计
for r in rows:
    pid = str(r.product_id)
    rowkey = hashlib.md5(pid.encode('utf-8')).hexdigest()[:4] + '_' + pid
    table.put(rowkey, {'stat:total_price': str(r.total_price),
                        'stat:total_quantity': str(r.total_quantity)})


print('数据写入成功', '总条数：', len(rows))
conn.close()
# 运行： spark-submit p3_hbase.py