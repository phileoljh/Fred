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

## ⏱️ 自動化部署與排程 (Cloudflare Pages + GitHub Actions)

**文件目的：** 規範 `phileoljh/Fred` 專案於 Cloudflare Pages (靜態網站代管服務) 的部署流程，並整合 GitHub Actions (自動化工作流程工具) 實現每日自動更新。

### 階段一：專案準備 (Repository Setup)
1. 確保專案已 Fork (複製分支) 或 Push (推送) 至個人 GitHub 帳號下。
2. 確認專案根目錄包含核心執行檔：`fetch_data.py`、`generate_html.py`、`init_db.py` 及 `requirements.txt`。

### 階段二：Cloudflare Pages 部署 (Deployment)

#### 1. 建立專案 (避開 Worker 陷阱)
* **正確路徑：** 登入 Cloudflare -> 左側選單選擇 **Workers & Pages** -> 點擊右上角 **Create (建立)** -> **務必選擇「Pages (頁面)」頁籤** -> **Connect to Git (連接到 Git)**。
* **⚠️ 常見錯誤 (Troubleshooting)：** 若畫面出現要求選擇「Worker (邊緣運算程式)」的樣板，或部署命令出現 `npx wrangler deploy`，代表選錯服務類型。必須退回上一層，點擊「Looking to deploy Pages? Get started」重新進入靜態網頁流程。

#### 2. 組建設定 (Build Settings)
請嚴格設定以下參數，確保每次部署都在乾淨的虛擬環境中重建資料庫與網頁：
* **Framework preset (框架預設)：** `None`
* **Build command (組建命令)：**
  ```bash
  pip install -r requirements.txt && python init_db.py && python generate_html.py && mkdir -p dist && mv *.html dist/
  ```
* **Build output directory (組建輸出目錄)：** `dist`
  * **⚠️ 常見錯誤：** 結尾嚴禁加上斜線 (不可寫成 `dist/`)，否則系統會報錯。
* **Root directory (根目錄)：** 保持空白。
  * **⚠️ 常見錯誤：** 若填入 `dist`，系統會直接在空目錄執行組建命令，導致找不到 Python 腳本與 `requirements.txt` 而崩潰。

#### 3. 環境變數設定 (Environment Variables)

* `FRED_API_KEY`：填入官方申請的 API 金鑰。
* `TZ`：填入 `Asia/Taipei`。
  * **設定說明：** Linux 伺服器預設為 UTC (世界協調時間)。設定 TZ (Time Zone, 時區) 可強制 Python 的 `datetime.now()` 抓取台灣時間，解決網頁更新時間顯示異常的問題。
* `PYTHON_VERSION`：(選擇性設定)
  * **可不設定**：系統使用預設版本 (如 `3.13.3`)，部署速度最快。

### 階段三：自訂網域綁定 (Custom Domain)

為避免手動設定 DNS (Domain Name System, 網域名稱系統) 導致缺少 SSL (安全通訊協定) 憑證：

1. 進入 Cloudflare Pages 專案面板 -> **Custom domains (自訂網域)**。
2. 點擊 **Set up a custom domain**，輸入目標網域（例如：`fred.hihimonitor.win`）。
3. 系統將自動配置 CNAME (標準名稱紀錄) 並簽發憑證，通常於 1 分鐘內生效。

### 階段四：自動化排程 (Automation & CI/CD)

#### 1. 取得部署觸發網址 (Deploy Hook)

1. 進入 CF Pages 專案 -> **Settings (設定)** -> **Builds & deployments (組建與部署)**。
2. 新增 Deploy Hook，命名為 `Daily-Update`，綁定 `main` 分支。
3. 複製系統生成的 API 網址。

#### 2. 設定 GitHub 機密變數 (Secrets)

1. 進入 GitHub 專案 -> **Settings (設定)** -> **Secrets and variables** -> **Actions**。
2. 新增 Repository secret，命名為 `CF_DEPLOY_HOOK`，貼上剛剛複製的網址。此舉為基礎安全防護，避免具有控制權的網址外洩。

#### 3. 建立 GitHub Actions 工作流程 (Workflow)

1. 在 GitHub 專案根目錄新增檔案：`.github/workflows/daily-update.yml`。
2. 寫入以下配置 (設定為台灣時間每日早上 08:00 執行)：
```yaml
name: Daily FRED Update
on:
  schedule:
    - cron: '0 0 * * *' # UTC 00:00 = 台灣時間 08:00
  workflow_dispatch: # 允許手動點擊執行
jobs:
  trigger-cloudflare:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Cloudflare Pages Build
        run: curl -X POST "${{ secrets.CF_DEPLOY_HOOK }}"
```
3. 儲存並 Commit (提交) 變更。至此，全自動化更新管線已建置完成。建議首次設定後，透過 GitHub 介面的 `Run workflow` 手動觸發一次以驗證連線。

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
