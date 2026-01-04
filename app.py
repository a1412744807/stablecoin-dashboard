import streamlit as st
import pandas as pd

# 设置页面
st.set_page_config(page_title="稳定币理财实时看板", layout="wide")

st.title("💰 稳定币理财收益看板")
st.write("数据源自 Google Sheets，人工实时维护")

# 你的表格 ID (从你提供的链接中提取)
SHEET_ID = "1UnFhhgjKTTKI0j4TbmyxyfAlE-DuAwICM-J9NrAmHD4"
# 构造 CSV 导出链接（这样无需 API Key 即可读取公开分享的表格）
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# 读取数据
@st.cache_data(ttl=300)  # 缓存5分钟，防止频繁读取
def load_data():
    df = pd.read_csv(SHEET_URL)
    return df

try:
    df = load_data()
    
    # 侧边栏：筛选功能
    st.sidebar.header("筛选设置")
    coin_filter = st.sidebar.multiselect("选择币种", options=df['币种'].unique(), default=df['币种'].unique())
    
    # 过滤数据
    filtered_df = df[df['币种'].isin(coin_filter)]
    
    # 展示核心数据卡片 (最高收益)
    if not filtered_df.empty:
        max_apy_row = filtered_df.loc[filtered_df['活期年化 (APY)'].str.rstrip('%').astype(float).idxmax()]
        st.metric(label=f"🔥 当前最高收益 ({max_apy_row['交易所']})", value=max_apy_row['活期年化 (APY)'])

    # 展示主表格（带链接按钮）
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config={
            "理财链接": st.column_config.LinkColumn(
                "🚀 去理财",
                display_text="前往理财",
                help="点击跳转到对应交易所理财页面"
            )
        }
    )
    
    st.info("💡 提示：在 Google Sheets 修改数据后，刷新此页面即可看到更新。")

except Exception as e:
    st.error("数据加载失败，请确保 Google 表格已开启「知道链接的任何人可查看」权限。")
    st.write(e)
