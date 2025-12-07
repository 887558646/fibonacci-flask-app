# 📈 台股投資工具整合平台

一個整合了斐波那契計算器、股票訊號儀表板和族群熱度分析的完整投資工具平台。

## ✨ 功能特點

### 📊 斐波那契計算器
- 🎯 **斐波那契回撤水平**：計算 23.6%、38.2%、50.0%、61.8% 等支撐位
- 📈 **斐波那契擴展水平**：計算 1.382、1.5、1.618、1.786、2.0 等壓力位
- 🏷️ **台股 Tick Size 自動修正**：根據台股最小升降單位規則自動調整價格

### 📈 股票訊號儀表板
- 🔍 **台股自動查詢**：只需輸入純數字代碼（如 2330），自動嘗試上市/上櫃
- 📊 **日線 KD 金叉訊號**：判斷日線 KDJ 指標是否出現金叉
- 📈 **週線 KD 金叉訊號**：判斷週線 KDJ 指標是否出現金叉
- 📉 **20MA 站上判斷**：判斷日線和週線價格是否站上 20 日均線/週均線
- 🎯 **多重支撐壓力位**：基於分形指標計算 R1-R3 和 S1-S3

### 🔥 族群熱度分析

#### 📊 週轉率分析報告
- 🔄 **高週轉率分析**：自動從 TWSE 和 TPEx API 載入週轉率資料
- 📈 **族群熱度排行**：計算各族群的出現檔數和平均週轉率
- 🔍 **查看個股**：點擊可展開查看該族群內的個股（含週轉率）
- 📋 **週轉率前 N 名清單**：完整的高週轉率股票清單
- ❓ **未分類股票**：識別不屬於任何定義族群的股票

#### ⚠️ 注意股分析報告
- 📥 **自動抓取**：從 MoneyDJ 網站即時抓取注意股資料
- 🔥 **獨立族群熱度排行**：直接對所有注意股進行族群分析（與週轉率分析獨立）
- 🔍 **查看個股**：點擊可展開查看該族群內的注意股
- 📋 **注意股清單**：顯示「股票名稱」與「事項」（與 MoneyDJ 格式一致）
- 🏷️ **支援多種代碼格式**：包含一般股票（4位）和權證（6位）
- ❓ **未分類注意股**：識別不屬於任何定義族群的注意股

## 🚀 快速開始

### 前置需求

- Python 3.7 或更高版本
- pip (Python 套件管理器)

### 安裝步驟

1. **進入專案目錄**
   ```bash
   cd final
   ```

2. **安裝依賴套件**
   ```bash
   pip install -r requirements.txt
   ```

3. **執行應用程式**
   ```bash
   python app.py
   ```

4. **開啟瀏覽器**
   訪問 `http://127.0.0.1:5000/`

## 📖 使用方法

### 斐波那契計算器

1. 在表單中輸入股票的**高點價格**（High Price）
2. 輸入股票的**低點價格**（Low Price）
3. 點擊「計算斐波那契支撐位與壓力位」按鈕
4. 查看計算結果表格

### 股票訊號儀表板

1. 在表單中輸入**台股代碼**（只需輸入數字，如 `2330`、`2317`）
2. 點擊「查詢股票訊號」按鈕
3. 查看訊號結果：日線訊號、週線訊號、多重支撐壓力位

### 族群熱度分析

1. 在「前 N 名」欄位輸入數字（例如：50），或留空分析所有資料
2. 點擊「📊 開始分析」按鈕
3. 系統會自動：
   - 從 TWSE 和 TPEx 官方 API 載入當日週轉率資料
   - 從 MoneyDJ 網站即時抓取注意股資料
   - 分別進行週轉率族群熱度分析與注意股族群熱度分析
4. 查看分析結果：
   - **週轉率分析報告**：依週轉率前 N 名股票進行族群分析
   - **注意股分析報告**：獨立對所有注意股進行族群分析（與 `themes_new.json` 比較）
5. 點擊「查看個股」可展開/收合該族群內的股票清單

## 🏗️ 專案結構

```
final/
│
├── app.py                    # 主應用程式
├── requirements.txt          # Python 依賴套件清單
├── themes_new.json           # 族群定義檔（26 個族群）
├── Procfile                  # Heroku/Railway 啟動配置
├── railway.json              # Railway 專用配置
├── runtime.txt               # Python 版本指定
├── routes/                   # 路由模組
│   ├── __init__.py
│   ├── fibonacci_routes.py   # 斐波那契計算路由
│   ├── stock_signals_routes.py  # 股票訊號查詢路由
│   └── theme_analysis_routes.py # 族群分析路由
├── modules/                   # 功能模組
│   ├── __init__.py
│   ├── data_loader.py        # 資料載入模組（TWSE/TPEx/MoneyDJ）
│   ├── theme_engine.py       # 族群判斷與熱度計算
│   ├── report_builder.py     # 報告資料整理
│   └── scraper.py            # 網頁資料抓取模組
├── templates/                # HTML 模板
│   └── index.html            # 主頁面模板（整合式 UI）
└── static/                   # 靜態資源（CSS、JS、圖片等）
```

## 🔧 技術棧

- **後端框架**：Flask 3.0.0（使用 Blueprints 模組化架構）
- **數據獲取**：yfinance 0.2.28、TWSE/TPEx API、MoneyDJ
- **數據處理**：pandas 2.0.3, numpy 1.24.3
- **網頁抓取**：BeautifulSoup4, lxml
- **前端技術**：HTML5, CSS3, JavaScript（Fetch API）
- **模板引擎**：Jinja2（Flask 內建）
- **部署伺服器**：gunicorn 21.2.0

## ☁️ 雲端部署

本專案支援部署到 Render 和 Railway 平台：

### 部署到 Render
1. 在 Render 建立新的 Web Service
2. 連接 GitHub 儲存庫
3. 設定：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. 部署完成後即可使用

### 部署到 Railway
1. 在 Railway 建立新專案
2. 連接 GitHub 儲存庫
3. 專案會自動偵測 `Procfile` 並啟動
4. 部署完成後即可使用

### 部署相關檔案
- `Procfile` - Heroku/Railway 啟動配置
- `railway.json` - Railway 專用配置
- `runtime.txt` - Python 版本指定

## 📝 API 端點

### 族群分析 API

- `POST /theme-analysis/analyze` - 分析族群熱度
  - 請求體：`{"top_n": 50}` 或 `{"top_n": null}`
  - 返回：分析結果 JSON

- `POST /theme-analysis/theme-detail` - 取得族群詳細資訊
  - 請求體：`{"theme_name": "族群名稱", "stocks_df": [...]}`
  - 返回：族群詳細資訊 JSON

- `GET /theme-analysis/theme-list` - 取得所有族群清單
  - 返回：族群清單 JSON

## ⚠️ 注意事項

- **本工具僅供盤後研究參考，不構成投資建議**
- 資料來源為 TWSE、TPEx 和 MoneyDJ 官方網站，請確保網路連線正常
- 族群定義需要定期更新以反映市場變化
- 建議在收盤後使用，避免盤中資料變動影響分析
- API 資料在非交易日可能無法取得

## 📄 授權

此專案為開源專案，可自由使用和修改。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

**免責聲明**：此工具僅供參考，不構成投資建議。投資有風險，請謹慎決策。所有計算結果和技術指標僅供分析參考，實際投資決策請諮詢專業投資顧問。


