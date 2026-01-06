# stablecoin-dashboard

这是一个使用 **Streamlit** 构建的「稳定币理财收益看板」，数据源来自公开的 Google 表格（CSV 导出）。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 线上部署（推荐：Streamlit Community Cloud，最简单）

1. 打开 Streamlit Cloud： https://share.streamlit.io/
2. 使用 GitHub 登录并授权
3. 选择仓库：`a1412744807/stablecoin-dashboard`
4. 选择分支：`main`
5. App file path：`app.py`
6. 点击 Deploy

部署完成后你会得到一个永久可访问的公网地址（形如 `https://xxxxx.streamlit.app`）。

### 注意事项

- Google 表格需要开启「知道链接的任何人可查看」，否则线上会提示无法读取数据。
- 你在 Google 表格修改数据后，前端会按缓存周期自动刷新（当前设置约 60 秒）。

## 数据源

数据读取地址由 `app.py` 中的 `SHEET_ID` / `SHEET_URL` 决定。
