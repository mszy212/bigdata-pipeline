# bigdata-pipeline 电商订单全链路数据管道

> 一条命令，从模拟订单生成到在线可查的商品销售榜单：**Python 造数 → HDFS 落地 → Spark 清洗分层 → HBase 榜单存储 → Streamlit 实时看板**。
>
> `bash run_pipeline.sh` 即可一键复现全流程。

## 1. 业务问题

模拟一家电商平台的日常数据处理场景：

- 每天产生约 **1000 条订单**，其中混杂着空用户、毒价格、重复上报等脏数据
- 运营需要随时知道：**哪些商品卖得最好？销售额集中在哪些品类？**
- 要求数据从产生到看板可查，**全程无人工干预**

## 2. 整体架构

```
gen_orders.py          hdfs dfs -put         spark-submit            spark-submit           streamlit run
(模拟下单+埋脏数据) ──► /data/ods 落地 ──► p2_clean.py 清洗分层 ──► p3_hbase.py 聚合榜单 ──► dashboard 在线查询
                          (HDFS)            /data/dwd (Parquet)      HBase product_stat     localhost:8501
```

| 环节 | 组件 | 说明 |
|------|------|------|
| 数据生成 | Python + random | 1000 条订单，按概率埋入三类脏数据 |
| 数据落地 | Hadoop 3.3.6 HDFS | ODS 层 `/data/ods`，保留原始数据不动 |
| 清洗分层 | Spark 3.5.9 (PySpark) | ODS → DWD：去脏 + 派生 `order_total` 列，Parquet 存储 |
| 榜单计算 | Spark + HBase 2.5.15 | 聚合商品维度销量/销售额，写 HBase（Thrift + happybase） |
| 在线查询 | Streamlit + Plotly | 指标卡 / TOP N 榜单 / 品类占比，毫秒级读 HBase |

## 3. 数据说明与指标口径

**原始数据**（每次运行重新生成，数字会有小幅波动）：

| 脏数据类型 | 埋入概率 | 最近一次体检结果 |
|-----------|---------|----------------|
| 空用户（user_id 为空） | ~2% | 19 条 |
| 毒价格（-888 元） | ~0.5% | 7 条 |
| 整行重复 | ~0.3% | 3 条 |

**清洗规则（口径表）**：

| 指标 | 口径 |
|------|------|
| 有效订单 | `user_id IS NOT NULL` 且 `order_price >= 0` 且去重后 |
| 订单金额 order_total | `quantity × order_price`，清洗后派生 |
| 商品销量 sales_qty | 有效订单按 product_id 求和 |
| 商品销售额 sales_amount | 有效订单的 order_total 按 product_id 求和 |
| HBase RowKey | `md5(product_id) 前 4 位 + "_" + product_id`（打散写入热点） |

## 4. 快速开始

```bash
# 前置：HDFS / HBase / Thrift 已启动（jps 应见 7 个进程）
start-dfs.sh
start-hbase.sh
hbase-daemon.sh start thrift

# 一键跑通全链路
bash run_pipeline.sh

# 打开看板
# http://localhost:8501
```

## 5. 业务结论（最近一次运行）

> 以下数字每次运行会随模拟数据波动，看板右上角为实时值。

- 清洗后有效订单 **974 条**（原始 1003 条，脏数据占比约 2.9%，与埋雷概率吻合）
- 全站 **50 个商品**，总销量 **2931 件**，总销售额 **¥489,739**
- **TOP1 商品（27 号）** 单品销量 97 件、销售额 ¥11,975，约为全站平均值的 1.6 倍
- 销售额呈明显**头部集中**：TOP10 商品贡献了全站约 1/4 的销量

**运营建议**：头部商品可申请首页坑位与备货优先级；长尾商品建议按周期复盘汰换，减少库存占用。

## 6. 踩坑记录（节选）

| 坑 | 现象 | 根因 | 修复 |
|----|------|------|------|
| HBase WAL 与 Hadoop 握手卡死 | HMaster 起不来 | asyncfs WAL 与 Hadoop 3.3.6 不兼容 | `hbase-site.xml` 设 `wal.provider=filesystem` |
| Zookeeper GET timeout | happybase 连不上 | Thrift 攥着过期会话 | 重启 thrift：`hbase-daemon.sh stop/start thrift` |
| happybase 装了却 import 不到 | ModuleNotFoundError | 装进了 base 环境，spark-submit 用的是 envs/pyspark | `python -m pip install happybase`（对应环境） |
| 管道"假成功" | 前面步骤全炸，看板照常启动 | 脚本无 `set -e`，HBase 里还是旧数据 | 脚本开头加 `set -e`，失败立即停 |
| HBase 写热点 | RowKey 递增导致集中写入 | 顺序 RowKey 落在同一 Region | md5 前缀打散 + 保留原 id 可解析 |

## 7. 项目结构

```
bigdata-pipeline/
├── run_pipeline.sh        # 一键串联全链路
├── scripts/
│   ├── gen_orders.py      # 模拟订单生成（埋三类脏数据）
│   ├── p2_clean.py        # ODS → DWD 清洗（Spark）
│   └── p3_hbase.py        # DWD → HBase 商品榜单（Spark + happybase）
├── dashboard/
│   └── app.py             # Streamlit 看板（读 HBase）
├── data/                  # 本地中转目录（.gitignore）
└── README.md
```

## 技术栈

Hadoop 3.3.6 · Spark 3.5.9 (PySpark) · HBase 2.5.15 · Python 3.12 · happybase · Streamlit · Plotly · WSL2 Ubuntu
