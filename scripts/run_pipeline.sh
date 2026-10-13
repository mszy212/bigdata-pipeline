# 生成新的订单
python scripts/gen_orders.py
# 上传数据到hdfs并覆盖原有数据
hdfs dfs -put -f data/orders_raw.csv data/ods/orders.csv
# spark 清洗数据
spark-submit scripts/p2_clean.py
# hbase 生成表并存入数据到hbase中
spark-submit scripts/p3_hbase.py
#  streamlit 运行分析页面
streamlit run scripts/p4_hbase_tab.py
# 运行
# bash run_pipeline.sh