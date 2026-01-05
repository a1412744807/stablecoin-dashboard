import streamlit as st
import pandas as pd

# 设置页面
st.set_page_config(page_title="稳定币理财实时看板", layout="wide")

st.title("💰 稳定币理财收益看板")

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
    
    # 使用全部数据
    filtered_df = df.copy()
    
    # 计算 APY 数值用于排序和高亮
    filtered_df['APY数值'] = filtered_df[COL_APY].str.rstrip('%').astype(float)
    max_apy = filtered_df['APY数值'].max()
    
    # 展示核心数据卡片 (最高收益)
    if not filtered_df.empty:
        max_apy_row = filtered_df.loc[filtered_df['APY数值'].idxmax()]
        st.metric(label=f"🔥 当前最高收益 ({max_apy_row[COL_PLATFORM]})", value=max_apy_row[COL_APY])

    # 准备显示的 DataFrame（不含辅助列）
    display_df = filtered_df.drop(columns=['APY数值']).reset_index(drop=True)

    # Alpha123 风格表格样式 CSS（浅色版）
    st.markdown("""
    <style>
    .alpha-table {
        width: 100%;
        border-collapse: collapse;
        background: #fff;
        font-size: 15px;
    }
    .alpha-table th {
        background: #fafafa;
        color: #888;
        font-weight: normal;
        padding: 14px 20px;
        text-align: center;
        border-bottom: 1px solid #e0e0e0;
        font-size: 14px;
    }
    .alpha-table td {
        color: #333;
        padding: 20px;
        border-bottom: 1px solid #eee;
        vertical-align: middle;
        text-align: center;
    }
    .alpha-table tr:last-child td {
        border-bottom: none;
    }
    .alpha-table tr:hover td {
        background: #e6f7ff;
    }
    .alpha-table .coin-cell {
        text-align: left;
        font-weight: 600;
        color: #222;
    }
    .alpha-table .sub-text {
        font-size: 13px;
        color: #999;
        margin-top: 4px;
        font-weight: normal;
    }
    .alpha-table .highlight {
        color: #d4a017;
        font-weight: 600;
    }
    .alpha-table .go-btn {
        color: #1890ff;
        text-decoration: none;
        font-size: 14px;
    }
    .alpha-table .go-btn:hover {
        text-decoration: underline;
    }
    .alpha-table .tag {
        display: inline-block;
        background: #f0f0f0;
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 12px;
        color: #666;
        margin: 2px;
    }
    .alpha-table .tag-limit {
        background: #fff1f0;
        color: #cf1322;
    }
    .alpha-table .tag-lock {
        background: #e6f7ff;
        color: #1890ff;
    }
    </style>
    """, unsafe_allow_html=True)

    # 定义表头顺序
    header_order = ['币种', '年化（APY）', '结束时间', '派息时间', '限额/锁仓', '投入1wu一个月收益']
    
    # 表头
    header_html = "<tr>" + "".join([f"<th>{col}</th>" for col in header_order]) + "<th></th></tr>"
    
    # 表体
    rows_html = ""
    for idx, row in display_df.iterrows():
        # 获取各字段值
        coin = row.get(COL_COIN, '')
        platform = row.get(COL_PLATFORM, '')
        apy = row.get(COL_APY, '')
        end_time = row.get('结束时间', '')
        pay_time = row.get('派息时间', '')
        limit = row.get('单个账户限额', '')
        is_locked = row.get('是否锁仓', '')
        income = row.get('投入1wu一个月收益', '')
        link = row.get(COL_LINK, '')
        
        # 构建限额+锁仓的气泡标签
        tags_html = ""
        if pd.notna(limit) and str(limit).strip():
            tags_html += f'<span class="tag tag-limit">{limit}</span>'
        if pd.notna(is_locked) and str(is_locked).strip():
            tags_html += f'<span class="tag tag-lock">{is_locked}</span>'
        if not tags_html:
            tags_html = "-"
        
        row_html = f"""<tr>
            <td class="coin-cell">{coin}<div class="sub-text">{platform}</div></td>
            <td class="highlight">{apy}</td>
            <td>{end_time if pd.notna(end_time) else '-'}</td>
            <td>{pay_time if pd.notna(pay_time) else '-'}</td>
            <td>{tags_html}</td>
            <td>{income if pd.notna(income) else '-'}</td>
            <td><a href="{link}" target="_blank" class="go-btn">前往 →</a></td>
        </tr>"""
        rows_html += row_html
    
    table_html = f"""
    <table class="alpha-table">
        <thead>{header_html}</thead>
        <tbody>{rows_html}</tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)

except Exception as e:
    st.error("数据加载失败，请确保 Google 表格已开启「知道链接的任何人可查看」权限。")
    st.write(e)
