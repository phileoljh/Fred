import os
import sys
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
import requests
from dotenv import load_dotenv

from config import AI_HTML_PATH

# Resend 官方寄信 API 端點與請求逾時設定
RESEND_API_URL = "https://api.resend.com/emails"
REQUEST_TIMEOUT_SECONDS = 15
DEFAULT_RESEND_FROM = "FRED Dashboard <onboarding@resend.dev>"

# 預設佔位字串清單：若環境變數仍為範例範本值，視為未完成設定
PLACEHOLDER_VALUES = {
    "re_your_resend_api_key_here",
    "your_email@gmail.com",
}


class _AiTableParser(HTMLParser):
    """解析 ai_view.html 內的摘要段落與數據表格，轉換為結構化資料。"""

    def __init__(self):
        super().__init__()
        self.meta_lines = []
        self.rows = []
        self._in_p = False
        self._in_tr = False
        self._in_cell = False
        self._current_p = []
        self._current_row = []
        self._current_cell = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower == "p":
            self._in_p = True
            self._current_p = []
        elif tag_lower == "tr":
            self._in_tr = True
            self._current_row = []
        elif tag_lower in ("th", "td") and self._in_tr:
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower == "p" and self._in_p:
            text = " ".join("".join(self._current_p).split())
            if text:
                self.meta_lines.append(text)
            self._in_p = False
        elif tag_lower in ("th", "td") and self._in_cell:
            cell_text = " ".join("".join(self._current_cell).split())
            self._current_row.append(cell_text)
            self._in_cell = False
        elif tag_lower == "tr" and self._in_tr:
            if self._current_row:
                self.rows.append(self._current_row)
            self._in_tr = False

    def handle_data(self, data):
        if self._in_p:
            self._current_p.append(data)
        elif self._in_cell:
            self._current_cell.append(data)


def _load_email_config():
    """
    從環境變數讀取選填的 Resend 寄信設定。
    真實的 RESEND_API_KEY 與收件信箱僅應填寫於不進 Git 的 .env 檔或 Cloudflare Pages 後台環境變數，切勿寫死於程式碼中。
    """
    load_dotenv()
    resend_api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    resend_to = (os.getenv("RESEND_TO") or "").strip()
    resend_from = (os.getenv("RESEND_FROM") or "").strip() or DEFAULT_RESEND_FROM
    return resend_api_key, resend_to, resend_from


def _is_email_config_ready(api_key, to_addr):
    """
    第一層軟失敗檢查：確認 Resend API Key 與收件者信箱是否齊備且非預設佔位字串。
    """
    if not api_key or not to_addr:
        return False
    if api_key in PLACEHOLDER_VALUES or to_addr in PLACEHOLDER_VALUES:
        return False
    return True


def _resolve_ai_html_path():
    """
    取得 ai_view.html 路徑。若當前工作目錄找不到，則回退至腳本所在目錄尋找。
    """
    if os.path.exists(AI_HTML_PATH):
        return AI_HTML_PATH
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, AI_HTML_PATH)


def _html_to_markdown(html_content):
    """
    將 ai_view.html 解析並轉換為純文字 Markdown 表格格式，
    讓 Gemini 的 @Gmail 擴充功能在純文字模式與 HTML 模式下皆能精準讀取數據。
    """
    parser = _AiTableParser()
    parser.feed(html_content)
    parser.close()

    lines = ["# FRED 總體經濟數據 (每日 AI 分析專用)", ""]

    if parser.meta_lines:
        lines.extend(parser.meta_lines)
        lines.append("")

    if parser.rows:
        header = [cell.replace("|", "\\|") for cell in parser.rows[0]]
        col_count = len(header)
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * col_count) + " |")

        for row in parser.rows[1:]:
            padded_row = [cell.replace("|", "\\|") for cell in row[:col_count]]
            if len(padded_row) < col_count:
                padded_row.extend([""] * (col_count - len(padded_row)))
            lines.append("| " + " | ".join(padded_row) + " |")
    else:
        lines.append("（無法解析 HTML 表格內容，請參閱郵件 HTML 原文。）")

    return "\n".join(lines)


def send_daily_email():
    """
    讀取 ai_view.html 並透過 Resend HTTP API 寄出包含純文字與 HTML 雙格式的信件。
    內建三層軟失敗（Soft-Fail）保護：任何條件不符或 API 異常皆僅輸出提示並回傳 False，
    絕不拋出未處理例外，確保不影響網頁生成與 Cloudflare Pages 部署流程。
    """
    api_key, recipient, sender = _load_email_config()

    # 第一層保護：環境變數完整性檢查
    if not _is_email_config_ready(api_key, recipient):
        print("[提示] 未偵測到完整的 Resend 環境變數設定（RESEND_API_KEY / RESEND_TO），略過每日郵件寄送功能。")
        return False

    # 第二層保護：目標 HTML 檔案存在與內容檢查
    target_path = _resolve_ai_html_path()
    if not os.path.exists(target_path):
        print(f"[提示] 找不到 AI 專用網頁檔案（{target_path}），略過每日郵件寄送功能。")
        return False

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            html_content = f.read().strip()
    except Exception as e:
        print(f"[警告] 讀取 {target_path} 時發生錯誤（不影響網頁正常建置與部署）：{e}")
        return False

    if not html_content:
        print(f"[提示] AI 專用網頁檔案內容為空（{target_path}），略過每日郵件寄送功能。")
        return False

    # 第三層保護：封裝雙格式 Payload 並透過 Resend HTTPS API 寄出（含逾時與全例外攔截）
    try:
        now_tw = datetime.now(timezone(timedelta(hours=8)))
        subject = f"[FRED每日總經數據] {now_tw.strftime('%Y-%m-%d')}"
        plain_text = _html_to_markdown(html_content)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": sender,
            "to": [recipient],
            "subject": subject,
            "text": plain_text,
            "html": html_content,
        }

        response = requests.post(
            RESEND_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.ok:
            print(f"[成功] 已透過 Resend 寄出每日 FRED AI 數據信件至 {recipient}（主旨：{subject}）。")
            return True

        print(
            f"[警告] Resend API 回傳非成功狀態碼 {response.status_code}"
            f"（不影響網頁正常建置與部署）：{response.text}"
        )
        return False
    except Exception as e:
        print(f"[警告] 郵件寄送失敗（不影響網頁正常建置與部署）：{e}")
        return False


if __name__ == "__main__":
    send_daily_email()
    # 無論寄信成功、略過或失敗，強制回傳狀態碼 0 確保部署管線正常完成
    sys.exit(0)
