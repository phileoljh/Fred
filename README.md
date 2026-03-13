# FRED 總體經濟儀表板 (FRED Macroeconomic Dashboard)

這是一個自動化抓取美國聯準會 (FRED) 開放經濟指標，並產生**「視覺化互動式網頁」**與**「AI 專用精簡版網頁」**的輕量級 Python 專案。

👉 **🌐 線上展示 (Live Demo)：**
- 📊 視覺化儀表板：[https://fred.hihimonitor.win/](https://fred.hihimonitor.win/)
- 🤖 AI 餵食專用版：[https://fred.hihimonitor.win/ai_view.html](https://fred.hihimonitor.win/ai_view.html)
## 🌟 專案特色

- **自動化新數據標示 (NEW Badge)**：精準抓取官方發布時間 (`last_updated`)，當數值為 7 天內最新公布時，圖表會自動亮起專屬發光徽章。
- **支援 30+ 項關鍵指標**：包含利率利差、就業市場、通膨、消費信心與製造業指數等，並根據指標特性客製化呈現 (如 MoM 月增率、YoY 年增率)。
- **自動回溯與修正**：避免使用單日快照，確保指標發布後的「修正值 (Revision)」也能同步更新圖表，但不干擾 NEW 標籤的判定。
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

## 💡 常見問題與運作原理 (FAQ & Technical Details)

### 1. 圖表的時間跨度是怎麼決定的？
儀表板上的所有折線圖皆採用**滾動式的「最近 18 個月」**視角。這意味著隨著時間推進，系統永遠只會撈取當下最新的 18 個月歷史資料來繪圖與計算均線，確保視覺焦點始終維持在近期的經濟轉折上，而不會因為時間越久導致圖表擠壓變形。

### 2. 圖表中的「基準線 (Baseline)」是怎麼算的？
圖表中預設會有一條淡淡的虛線作為歷史基準，幫助判斷數值位階：
- **強制 0 軸**：針對 `SOFR_IORB_SPREAD`、`T10Y2Y`、`T10Y3M` 這三組代表衰退風險的「公債與殖利率利差」，系統會強制鎖定在 `0.0%` 畫出基準線。
- **18 個月動態平均**：除上述三者外的所有經濟數據（如失業金、消費者信心、通膨年增率等），系統會自動計算過去 18 個月內**實際發布過的所有數值的算術平均數**，作為動態歷史基準。

### 3. 如果資料庫壞掉或想重撈資料怎麼辦？
**直接把 `fred_data.db` 檔案刪除即可！**
本專案的 `generate_html.py` 具有防呆機制，如果它在產生網頁前發現資料庫被刪除了，會先跳出警告並阻擋執行。此時您只需要重新啟動 `python init_db.py`，系統就會聰明地根據 `config.py` 內定義的每個指標所需的發布頻率 (Daily/Weekly/Monthly)，全自動重新向 API 請求並精準重建滿滿 18 個月的歷史資料簿。

### 4. SQLite 資料庫檔案一直長大會影響效能嗎？
**完全不會！**
FRED 的純數字時間序列資料非常輕薄，我們在設計 SQLite 資料表時強制加入了 `PRIMARY KEY (series_id, date)` 索引與 `ON CONFLICT DO UPDATE` 機制。
- 就算資料累積數十年，查詢速度依然在毫秒級別內。
- 系統只會儲存與更新「真實有變動」的數值與官方發布時間。
- 您可以放心地讓其在每天的 Linux Cron 排程中自動增長與存放，無須定期清空資料庫。

### 5. 畫面上的「NEW」發光徽章是什麼機制？
系統在抓取數據時，會同步向 FRED 官方 API 詢問該指標的「精準最終發行時間 (last_updated)」。在產生網頁的當下，只要系統判斷這筆最新的數據距離官方發布時間**還在 7 天以內**（且該指標屬於月報或季報等較低頻率），該指標就會根據新鮮程度亮起三種不同等級的發光徽章：
- 🔥 **NEW (1d)**：發布 1 天內，橘紅色漸層與急促閃爍。
- 💥 **NEW (3d)**：發布 2~3 天內，紅紫色漸層與穩定的呼吸燈。
- ✨ **NEW**：發布 4~7 天內，科技藍漸層與緩慢的呼吸光暈。
超過 7 天後，徽章會自動隱藏，確保您的視覺焦點只在一週內最新鮮的市場動態上。
