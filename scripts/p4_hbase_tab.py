import happybase 
import streamlit as st
import pandas as pd
import plotly.express as px

# 设计模板
st.set_page_config(layout='wide', page_title='商品分析', page_icon=':bar_chart:')
st.title('商品榜单分析')

# 创建连接
conn = happybase.Connection(host='localhost', port=9090)

# 连接表
table = conn.table(b'product_stat')
# 获取所有行
rows = table.scan()

# === ③ 拆包 + 转换：bytes → 字符串 → 数字 ===
data = []
for row_key, row_data in rows:
    k = row_key.decode('utf-8')  # bytes → 字符串
    product_id = k.split('_')[1]  # 拆包
    price = row_data[b'stat:total_price'].decode('utf-8')
    qty = row_data[b'stat:total_quantity'].decode('utf-8')
    # 转换为数字
    data.append({
        'product_id': product_id,
        'total_price': float(price),
        'total_quantity': int(qty)
    })
# 打印结果
# st.write(data)
# 转换为DataFrame
df = pd.DataFrame(data)

tab1, tab2,tab3 = st.tabs(['销量榜','销售额榜','占比分析'])
with tab1:
    st.subheader('商品销量榜单')
    top_n = st.sidebar.slider('显示前 N 名', min_value=1, max_value=10, value=10)
    top10 = df.sort_values(by='total_quantity', ascending=False).head(top_n)
    # streamlit 画图
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric('商品总数', f'{len(df)}')
        
    with col2:
        st.metric('总销量', f'{df["total_quantity"].sum():.2f}')
    with col3:
        st.metric('总销售额',f'{df["total_price"].sum():.2f}')
    with col4:
        df_avg_qty = df['total_quantity'].mean()    
        st.metric('平均单商品销量',f'{df_avg_qty:.2f}')
    with col5:
        st.metric('销量top1',f'{df.iloc[0]["total_quantity"]:.2f}')
    qty_top10 = top10.rename(columns={'product_id':'商品ID','total_quantity':'销量','total_price':'销售额'})
    # 显示表格并取消索引

    st.dataframe(qty_top10, use_container_width=True, hide_index=True)

    fig = px.bar(qty_top10, x='销量', y='商品ID', title='商品销量榜单',orientation='h')
    st.plotly_chart(fig, use_container_width=True)
with tab2:
    st.subheader('商品销售额榜单')
    col1, col2, col3, col4, col5 = st.columns(5)
    sale_top10 = df.sort_values(by='total_price', ascending=False).head(top_n)
    with col1:
        st.metric('商品总数', f'{len(df)}')
    with col2:
        st.metric('总销量', f'{df["total_quantity"].sum():.2f}')
    with col3:
        df_avg_price = df['total_price'].mean()
        st.metric('平均单商品销售额',f'{df_avg_price:.2f}')
    with col4:
        st.metric('销售额top1',f'{df.iloc[0]["total_price"]:.0f}')
    with col5:
        st.metric('总销售额', f'{df["total_price"].sum():.2f}')
    sale_top10 = sale_top10.rename(columns={'product_id':'商品ID','total_quantity':'销量','total_price':'销售额'})
    st.dataframe(sale_top10, use_container_width=True)
    fig = px.bar(sale_top10, x='商品ID', y='销售额', title='商品销售额榜单')
    st.plotly_chart(fig, use_container_width=True)
with tab3:
    st.subheader('商品占比分析饼状图')
    col1, col2 = st.columns(2)
    df = df.rename(columns={'product_id':'商品ID','total_quantity':'销量','total_price':'销售额'})
    with col1:
        fig = px.pie(qty_top10, values='销量', names='商品ID', title='top10商品销量占比',hole=0.2)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.pie(sale_top10, values='销售额', names='商品ID', title='top10商品销售额占比',hole=0.2)
        st.plotly_chart(fig, use_container_width=True)
# 关闭连接
conn.close()

# 运行： streamlit run p4_hbase_tab.py
