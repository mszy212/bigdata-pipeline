import random as rd
import datetime as dt
import csv

# ① 循环外：开一次门、造一支笔、写表头
f = open('data/orders_raw.csv', 'w', newline='', encoding='utf-8')
writer = csv.writer(f)
writer.writerow(['order_id','user_id','product_id','quantity','order_price','order_date','status'])

for order_id in range(10001, 10001+1000):
    user_id = rd.randint(1,200)
    product_id = rd.randint(1,50)
    quantity = rd.randint(1,5)
    order_price = rd.randint(10,999)
    order_date = (dt.datetime.now() - dt.timedelta(days=rd.randint(0,29))).strftime("%Y-%m-%d")
    status = rd.choice(['paid','completed','shipped','cancelled'])
                
    # 埋雷①②
    if rd.random() < 0.02:
        user_id = ''
    if rd.random() < 0.005:
        order_price = -888

    # ② 循环内：只写行
    row = [order_id, user_id, product_id, quantity, order_price, order_date, status]
    writer.writerow(row)
    if rd.random() < 0.005:          # 雷③：整行重复
        writer.writerow(row)

# ③ 循环外最后：关门
f.close()

# 运行： python scripts/gen_orders.py