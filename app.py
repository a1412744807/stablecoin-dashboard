import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# 设置页面
st.set_page_config(page_title="稳定币理财实时看板", layout="wide")

st.title("💰 稳定币理财收益看板")
st.caption("APY 下方展示「剩余时间」+ 进度条，点击计算器可预估收益")

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

    # 定义表头顺序（合并操作列）
    header_order = ['币种', '年化（APY）', '结束时间', '限额/锁仓', '收益计算器']
    
    # 计算剩余时间的辅助函数
    def parse_end_time(end_time_str):
        """解析结束时间，返回datetime对象"""
        if pd.isna(end_time_str) or not str(end_time_str).strip() or str(end_time_str).strip() in ['暂无', '无截止', '-', '无']:
            return None
        try:
            # 尝试解析格式如 "1月24日7点59" 或 "1月10日7:59"
            end_str = str(end_time_str).strip()
            # 提取月日时分
            import re
            match = re.search(r'(\d+)月(\d+)日(\d+)[点:]?(\d*)', end_str)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                hour = int(match.group(3))
                minute = int(match.group(4)) if match.group(4) else 0
                year = datetime.now().year
                # 如果月份小于当前月，说明是明年
                if month < datetime.now().month:
                    year += 1
                return datetime(year, month, day, hour, minute)
        except:
            pass
        return None
    
    def calc_remaining(end_time_str):
        """计算剩余时间，返回(剩余文本, 进度百分比)"""
        end_dt = parse_end_time(end_time_str)
        if not end_dt:
            return None, None
        
        now = datetime.now()
        if end_dt <= now:
            return "已结束", 100
        
        delta = end_dt - now
        days = delta.days
        hours = delta.seconds // 3600
        
        if days > 0:
            remaining_text = f"剩余 {days}天{hours}小时"
        else:
            remaining_text = f"剩余 {hours}小时"
        
        # 计算进度（假设活动总时长30天，实际可根据需要调整）
        total_days = 30
        elapsed_percent = max(0, min(100, (total_days - days) / total_days * 100))
        
        return remaining_text, elapsed_percent
    
    # 表头
    header_html = "<tr>" + "".join([f"<th>{col}</th>" for col in header_order]) + "</tr>"
    
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
        
        # 计算剩余时间和进度
        remaining_text, progress_percent = calc_remaining(end_time)
        
        # 构建限额+锁仓+派息时间的气泡标签
        tags_html = ""
        if pd.notna(limit) and str(limit).strip() and str(limit).strip() not in ['无', '-']:
            tags_html += f'<span class="tag tag-limit">{limit}</span>'
        if pd.notna(is_locked) and str(is_locked).strip() and str(is_locked).strip() not in ['无', '-']:
            tags_html += f'<span class="tag tag-lock">{is_locked}</span>'
        if pd.notna(pay_time) and str(pay_time).strip() and str(pay_time).strip() not in ['无', '-']:
            tags_html += f'<span class="tag tag-pay">{pay_time}</span>'
        
        # 币种单元格（手机端在下方显示气泡标签）
        coin_html = f'{coin}<div class="sub-text">{platform}</div>'
        if tags_html:
            coin_html += f'<div class="mobile-tags">{tags_html}</div>'
        
        # APY单元格（带剩余时间和进度条）
        apy_html = f'<span class="highlight">{apy}</span>'
        if remaining_text:
            apy_html += f'<div class="remaining-time">{remaining_text}</div>'
            if progress_percent is not None:
                apy_html += f'''<div class="progress-bar">
                    <div class="progress-fill" style="width: {100 - progress_percent}%"></div>
                </div>'''
        
        # 气泡标签（PC端显示）
        tags_display = tags_html if tags_html else "-"
        
        # 操作列：计算器图标 + 前往理财按钮（左右分布）
        action_html = f'''<td class="action-cell">
            <span class="calc-btn" onclick="openCalcModal('{coin}', '{platform}', '{apy}')" title="计算收益">🧮</span>
            <a href="{link}" target="_blank" class="go-btn">前往理财</a>
        </td>'''
        
        row_html = f"""<tr>
            <td class="coin-cell">{coin_html}</td>
            <td>{apy_html}</td>
            <td class="pc-only">{end_time if pd.notna(end_time) and str(end_time).strip() not in ['暂无', '无截止', '无'] else '-'}</td>
            <td class="pc-only">{tags_display}</td>
            {action_html}
        </tr>"""
        rows_html += row_html
    
    table_html = f"""
    <table class="alpha-table">
        <thead>{header_html}</thead>
        <tbody>{rows_html}</tbody>
    </table>
    """
    
    # 完整HTML（包含CSS + 表格 + 弹窗 + JS）
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    .alpha-table {{
        width: 100%;
        border-collapse: collapse;
        background: #fff;
        font-size: 15px;
    }}
    .alpha-table th {{
        background: #fafafa;
        color: #888;
        font-weight: normal;
        padding: 14px 20px;
        text-align: center;
        border-bottom: 1px solid #e0e0e0;
        font-size: 14px;
    }}
    .alpha-table td {{
        color: #333;
        padding: 20px;
        border-bottom: 1px solid #eee;
        vertical-align: middle;
        text-align: center;
    }}
    .alpha-table tr:hover td {{
        background: #f5f5f5;
    }}
    .alpha-table .coin-cell {{
        text-align: left;
        font-weight: 600;
        color: #222;
    }}
    .alpha-table .sub-text {{
        font-size: 13px;
        color: #999;
        margin-top: 4px;
        font-weight: normal;
    }}
    .alpha-table .highlight {{
        color: #d4a017;
        font-weight: 600;
        font-size: 16px;
    }}

    .alpha-table .tag {{
        display: inline-block;
        background: #f0f0f0;
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 12px;
        color: #666;
        margin: 2px;
    }}
    .alpha-table .tag-limit {{
        background: #fff1f0;
        color: #cf1322;
    }}
    .alpha-table .tag-lock {{
        background: #e6f7ff;
        color: #1890ff;
    }}
    .alpha-table .tag-pay {{
        background: #f6ffed;
        color: #52c41a;
    }}
    .alpha-table .remaining-time {{
        font-size: 13px;
        color: #d4a017;
        margin-top: 4px;
    }}
    .alpha-table .progress-bar {{
        width: 100%;
        height: 3px;
        background: #eee;
        border-radius: 2px;
        margin-top: 6px;
        overflow: hidden;
    }}
    .alpha-table .progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, #ffd666, #d4a017);
        border-radius: 2px;
    }}
    .alpha-table .action-cell {{
        text-align: center;
        white-space: nowrap;
    }}
    .alpha-table .calc-btn {{
        display: inline-block;
        background: #fff7e6;
        color: #d4a017;
        border: 1px solid #ffd666;
        border-radius: 6px;
        width: 36px;
        height: 36px;
        line-height: 34px;
        font-size: 20px;
        cursor: pointer;
        margin-right: 10px;
        transition: all 0.2s;
        vertical-align: middle;
        text-align: center;
    }}
    .alpha-table .calc-btn:hover {{
        background: #ffd666;
        border-color: #d4a017;
        transform: scale(1.1);
    }}
    .alpha-table .go-btn {{
        display: inline-block;
        background: #1890ff;
        color: #fff;
        text-decoration: none;
        font-size: 14px;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
        vertical-align: middle;
    }}
    .alpha-table .go-btn:hover {{
        background: #40a9ff;
        text-decoration: none;
    }}
    
    /* 弹窗样式 */
    .modal-overlay {{
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 1000;
        justify-content: center;
        align-items: center;
    }}
    .modal-box {{
        background: #fff;
        border-radius: 12px;
        padding: 24px;
        width: 320px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }}
    .modal-title {{
        font-size: 18px;
        font-weight: 600;
        color: #333;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .modal-close {{
        cursor: pointer;
        font-size: 24px;
        color: #999;
        line-height: 1;
    }}
    .modal-close:hover {{
        color: #333;
    }}
    .modal-info-row {{
        font-size: 14px;
        color: #666;
        margin-bottom: 16px;
        padding: 10px;
        background: #fafafa;
        border-radius: 8px;
    }}
    .modal-input {{
        width: 100%;
        padding: 12px;
        border: 1px solid #ddd;
        border-radius: 8px;
        font-size: 16px;
        margin-bottom: 16px;
    }}
    .modal-input:focus {{
        outline: none;
        border-color: #1890ff;
    }}
    .modal-result {{
        background: #f6ffed;
        border: 1px solid #b7eb8f;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }}
    .modal-result-item {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
        font-size: 14px;
        color: #666;
    }}
    .modal-result-item:last-child {{
        margin-bottom: 0;
    }}
    .modal-result-value {{
        font-weight: 600;
        color: #52c41a;
        font-size: 16px;
    }}
    .modal-note {{
        font-size: 12px;
        color: #999;
        text-align: center;
    }}
    
    /* 手机端专用元素（PC端隐藏） */
    .mobile-tags {{
        display: none;
        margin-top: 6px;
    }}
    .mobile-end-time {{
        display: none;
        font-size: 11px;
        color: #999;
        margin-top: 4px;
    }}
    
    /* ========== 移动端适配 ========== */
    @media screen and (max-width: 768px) {{
        .alpha-table {{
            font-size: 13px;
        }}
        .alpha-table th {{
            padding: 10px 8px;
            font-size: 12px;
        }}
        .alpha-table td {{
            padding: 12px 8px;
        }}
        .alpha-table .coin-cell {{
            min-width: 80px;
        }}
        .alpha-table .sub-text {{
            font-size: 11px;
        }}
        .alpha-table .highlight {{
            font-size: 14px;
        }}
        .alpha-table .remaining-time {{
            font-size: 11px;
        }}
        .alpha-table .tag {{
            padding: 2px 6px;
            font-size: 10px;
            margin: 1px;
        }}
        .alpha-table .calc-btn {{
            width: 30px;
            height: 30px;
            line-height: 28px;
            font-size: 16px;
            margin-right: 6px;
        }}
        .alpha-table .go-btn {{
            font-size: 12px;
            padding: 6px 10px;
        }}
        .alpha-table .action-cell {{
            min-width: 110px;
        }}
        /* 隐藏PC端专用列 */
        .alpha-table th:nth-child(3),
        .alpha-table td.pc-only:nth-of-type(1),
        .alpha-table th:nth-child(4),
        .alpha-table td.pc-only:nth-of-type(2) {{
            display: none;
        }}
        .pc-only {{
            display: none;
        }}
        /* 显示手机端专用元素 */
        .mobile-tags {{
            display: block;
        }}
        .mobile-end-time {{
            display: block;
        }}
        /* 弹窗适配 */
        .modal-box {{
            width: 90%;
            max-width: 320px;
            padding: 16px;
        }}
        .modal-title {{
            font-size: 16px;
        }}
        .modal-input {{
            padding: 10px;
            font-size: 16px;
        }}
    }}
    
    /* 超小屏幕（手机竖屏）*/
    @media screen and (max-width: 480px) {{
        .alpha-table th {{
            padding: 8px 6px;
            font-size: 11px;
        }}
        .alpha-table td {{
            padding: 10px 6px;
        }}
        .alpha-table .highlight {{
            font-size: 13px;
        }}
        .alpha-table .calc-btn {{
            width: 28px;
            height: 28px;
            line-height: 26px;
            font-size: 14px;
            margin-right: 4px;
        }}
        .alpha-table .go-btn {{
            font-size: 11px;
            padding: 5px 8px;
        }}
    }}
    </style>
    </head>
    <body>
    
    {table_html}
    
    <!-- 计算器弹窗 -->
    <div class="modal-overlay" id="calcModal">
        <div class="modal-box">
            <div class="modal-title">
                <span>💰 收益计算器</span>
                <span class="modal-close" onclick="closeCalcModal()">×</span>
            </div>
            <div class="modal-info-row">
                <strong id="modalCoin"></strong> · <span id="modalPlatform"></span><br>
                年化利率：<span id="modalApy" style="color:#d4a017;font-weight:600;"></span>
            </div>
            <input type="number" class="modal-input" id="calcAmount" placeholder="输入投入金额" oninput="calculateProfit()">
            <div class="modal-result">
                <div class="modal-result-item">
                    <span>📅 每日收益</span>
                    <span class="modal-result-value" id="dailyProfit">0.0000</span>
                </div>
                <div class="modal-result-item">
                    <span>📆 每月收益</span>
                    <span class="modal-result-value" id="monthlyProfit">0.00</span>
                </div>
                <div class="modal-result-item">
                    <span>📈 每年收益</span>
                    <span class="modal-result-value" id="yearlyProfit">0.00</span>
                </div>
            </div>
            <div class="modal-note">* 预估收益仅供参考，实际以平台结算为准</div>
        </div>
    </div>
    
    <script>
    var currentApy = 0;
    var currentCoin = '';
    
    function openCalcModal(coin, platform, apy) {{
        currentCoin = coin;
        document.getElementById('modalCoin').innerText = coin;
        document.getElementById('modalPlatform').innerText = platform;
        document.getElementById('modalApy').innerText = apy;
        document.getElementById('calcAmount').placeholder = '输入投入金额 (' + coin + ')';
        currentApy = parseFloat(apy.replace('%', '')) / 100;
        document.getElementById('calcAmount').value = '';
        document.getElementById('dailyProfit').innerText = '0.0000 ' + coin;
        document.getElementById('monthlyProfit').innerText = '0.00 ' + coin;
        document.getElementById('yearlyProfit').innerText = '0.00 ' + coin;
        document.getElementById('calcModal').style.display = 'flex';
    }}
    
    function closeCalcModal() {{
        document.getElementById('calcModal').style.display = 'none';
    }}
    
    function calculateProfit() {{
        var amount = parseFloat(document.getElementById('calcAmount').value) || 0;
        var yearly = amount * currentApy;
        var monthly = yearly / 12;
        var daily = yearly / 365;
        document.getElementById('dailyProfit').innerText = daily.toFixed(4) + ' ' + currentCoin;
        document.getElementById('monthlyProfit').innerText = monthly.toFixed(2) + ' ' + currentCoin;
        document.getElementById('yearlyProfit').innerText = yearly.toFixed(2) + ' ' + currentCoin;
    }}
    
    // 点击弹窗外部关闭
    document.getElementById('calcModal').onclick = function(e) {{
        if (e.target === this) closeCalcModal();
    }};
    </script>
    
    </body>
    </html>
    """
    
    # 使用 components.html 渲染（支持 JavaScript）
    components.html(full_html, height=600, scrolling=True)

except Exception as e:
    st.error("数据加载失败，请确保 Google 表格已开启「知道链接的任何人可查看」权限。")
    st.write(e)
