# FRED 總體經濟儀表板 (FRED Macroeconomic Dashboard)

這是一個自動化抓取美國聯準會 (FRED) 開放經濟指標，並產生**「視覺化互動式網頁」**與**「AI 專用精簡版網頁」**的輕量級 Python 專案。

## 🌟 專案特色

- **全自動化資料抓取**：透過 FRED API 自動獲取最新的總體經濟數據與歷史資料。
- **支援 25 項關鍵指標**：包含利率利差、就業市場、通膨、消費信心與製造業指數等。
- **自動回溯與修正**：避免使用單日快照，確保指標發布後的「修正值」也能同步。
- **雙版本輸出**：
  - `index.html`：以深色玻璃擬物風 (Glassmorphism) 設計的精美圖表儀表板，內建歷史趨勢迷你圖 (Chart.js)。
  - `ai_view.html`：僅有表格與純文字的極簡 HTML，適合直接複製貼上給 ChatGPT / Claude 等 LLM 進行分析以節省 Token。
- **輕量級儲存**：無需部署大型資料庫，採用本地 SQLite (`fred_data.db`) 即可運行。

## 📁 專案架構

```text
FRED/
├── config.py           # 系統參數與指標名單 (API Key、25 個指標的定義)
├── fetch_data.py       # 負責呼叫 FRED API 並將資料存入 SQLite 資料庫
├── generate_html.py    # 讀取資料庫，並負責產生網頁 (index.html, ai_view.html)
├── .env.example        # 環境變數範例檔
├── requirements.txt    # Python 依賴包列表
└── .gitignore          # 避免將敏感資料與產生的靜態網頁上傳到 Git
```

## 🚀 快速開始

### 1. 前置作業與安裝

請確保您的環境安裝了 Python 3.x，接著安裝所需的依賴：
```bash
pip install -r requirements.txt
```

*(依賴套件包含：`requests`, `python-dotenv`)*

### 2. 設定 API Key

您需要前往 [FRED 官方網站](https://fred.stlouisfed.org/docs/api/api_key.html) 申請免費的 API Key。
申請完畢後，在專案根目錄建立 `.env` 檔案，並填入您的 Key：

```env
FRED_API_KEY=your_fred_api_key_here
```

### 3. 執行程式

本系統將工作邏輯拆分為「抓取資料」與「產生網頁」兩部分，請依序執行：

```bash
# 第一步：連線到 FRED 抓取歷史與最新資料 (會自動建立 fred_data.db)
python fetch_data.py

# 第二步：根據資料庫的內容產生儀表板
python generate_html.py
```
執行完畢後，資料夾內會產生：
- 開啟 `index.html` 用瀏覽器觀看漂亮的視覺化圖表。
- 開啟 `ai_view.html` 給 AI 分析使用。

## ⏱️ 自動化排程建議 (Linux Cron)

為了讓您的儀表板永遠保持最新狀態，建議您將這個專案部署在 Linux 伺服器上，並設定 Cron 排程。FRED 的免費額度為每分鐘 120 次，本程式預設只需呼叫 25 次，負載極低。

您可以建立一個簡單的 `run_fred.sh`：
```bash
#!/bin/bash
cd /path/to/your/FRED
python fetch_data.py
python generate_html.py
```

並在 `crontab -e` 加入每日自動更新排程（例如每天早上 8 點）：
```text
0 8 * * * /path/to/your/FRED/run_fred.sh >> /path/to/your/FRED/cron.log 2>&1
```

## 📝 自訂指標

如果您想要監控更多或其他的 FRED 經濟資料，只需打開 `config.py`，在 `INDICATORS` 列表中按照相同的格式加入 FRED 的系列 ID (Series ID) 即可無痛擴充。
