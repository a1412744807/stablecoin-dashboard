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

# 列名常量（从表格获取）
COL_PLATFORM = '平台'
COL_COIN = '币种'
COL_APY = '年化（APY）'
COL_LINK = '理财链接'

try:
    df = load_data()
    
    # 展示核心数据卡片 (最高收益) 和 筛选器 并排
    col1, col2 = st.columns([3, 1])
    
    with col2:
        coin_filter = st.multiselect("🔍 筛选币种", options=df[COL_COIN].unique(), default=df[COL_COIN].unique())
    
    # 过滤数据
    filtered_df = df[df[COL_COIN].isin(coin_filter)].copy()
    
    # 计算 APY 数值用于排序和高亮
    filtered_df['APY数值'] = filtered_df[COL_APY].str.rstrip('%').astype(float)
    max_apy = filtered_df['APY数值'].max()
    
    # 展示核心数据卡片 (最高收益)
    with col1:
        if not filtered_df.empty:
            max_apy_row = filtered_df.loc[filtered_df['APY数值'].idxmax()]
            st.metric(label=f"🔥 当前最高收益 ({max_apy_row[COL_PLATFORM]})", value=max_apy_row[COL_APY])

    # 准备显示的 DataFrame（不含辅助列，重置索引去掉左边索引列）
    display_df = filtered_df.drop(columns=['APY数值']).reset_index(drop=True)
    
    # 高亮样式函数 - 根据APY值判断是否是最高APY行
    def highlight_max_apy(row):
        # 获取当前行的APY值
        apy_val = float(row[COL_APY].rstrip('%'))
        if apy_val == max_apy:
            return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
        return [''] * len(row)
    
    # 应用样式：字体加大 + 标题加粗 + 高亮最高APY行
    styled_df = display_df.style.apply(highlight_max_apy, axis=1).set_properties(**{
        'font-size': '16px'
    }).set_table_styles([
        {'selector': 'th', 'props': [('font-weight', 'bold'), ('font-size', '16px')]}
    ])

    # 展示主表格（带链接按钮和高亮，隐藏索引列）
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            COL_LINK: st.column_config.LinkColumn(
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
