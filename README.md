# 📈 斐波那契計算器 & 股票訊號儀表板

一個基於 Flask Blueprints 的模組化網頁應用程式，整合了斐波那契支撐位/壓力位計算器和台股技術分析訊號查詢功能。此工具幫助投資者進行技術分析和價格目標預測。

## ✨ 功能特點

### 📊 斐波那契計算器
- 🎯 **斐波那契回撤水平**：計算 23.6%、38.2%、50.0%、61.8% 等支撐位
- 📈 **斐波那契擴展水平**：計算 1.382、1.5、1.618、1.786、2.0 等壓力位
- 🏷️ **台股 Tick Size 自動修正**：根據台股最小升降單位規則自動調整價格
  - < 10: 0.01
  - 10-50: 0.05
  - 50-100: 0.10
  - 100-500: 0.50
  - 500-1000: 1.00
  - >= 1000: 5.00
- ✅ **穩健的輸入驗證**：確保輸入數據的有效性和邏輯正確性

### 📈 股票訊號儀表板
- 🔍 **台股自動查詢**：只需輸入純數字代碼（如 2330），自動嘗試上市/上櫃
- 📊 **日線 KD 金叉訊號**：判斷日線 KDJ 指標是否出現金叉
- 📈 **週線 KD 金叉訊號**：判斷週線 KDJ 指標是否出現金叉
- 📉 **20MA 站上判斷**：判斷日線和週線價格是否站上 20 日均線/週均線
- 🎯 **完整技術指標**：顯示 K 值、D 值、當前價格、20MA 等完整資訊

### 🎨 使用者體驗
- 🎨 **現代化使用者介面**：美觀的漸層設計，響應式布局
- 📱 **響應式設計**：支援各種裝置和螢幕尺寸
- ⚠️ **友善的錯誤處理**：錯誤訊息在同一頁面顯示，無需跳轉
- 🎭 **動畫效果**：流暢的滑入動畫提升使用者體驗

## 🚀 快速開始

### 前置需求

- Python 3.7 或更高版本
- pip (Python 套件管理器)

### 安裝步驟

1. **克隆倉庫**
   ```bash
   git clone https://github.com/887558646/fibonacci-flask-app.git
   cd fibonacci-flask-app
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
4. 查看計算結果表格：
   - **支撐位表格**：顯示各回撤水平對應的支撐價格（已應用 Tick Size 向上取整）
   - **壓力位表格**：顯示各擴展水平對應的壓力價格（已應用 Tick Size 向下取整）

### 股票訊號儀表板

1. 在表單中輸入**台股代碼**（只需輸入數字，如 `2330`、`2317`）
2. 點擊「查詢股票訊號」按鈕
3. 系統會自動嘗試：
   - 優先嘗試上市股票（`.TW`）
   - 若失敗，自動嘗試上櫃股票（`.TWO`）
4. 查看訊號結果：
   - **日線訊號**：日 KD 金叉、日 K/D 值、日線價格站上 20MA
   - **週線訊號**：週 KD 金叉、週 K/D 值、週線價格站上 20MA

## 🧮 計算公式

### 斐波那契計算

**支撐位（回撤）**：
```
價格區間 (Range) = 高點價格 - 低點價格
支撐價格 = 高點價格 - (價格區間 × 回撤百分比)
```

**壓力位（擴展）**：
```
價格區間 (Range) = 高點價格 - 低點價格
壓力價格 = 高點價格 + (價格區間 × (擴展水平 - 1))
```

**台股 Tick Size 修正**：
- 支撐位：向上取整（ceil），取最接近且大於或等於計算價格的 Tick 價格
- 壓力位：向下取整（floor），取最接近且小於或等於計算價格的 Tick 價格

### 技術指標計算

**KDJ 指標**（參數：9, 3, 3）：
- RSV = (收盤價 - 最低價) / (最高價 - 最低價) × 100
- K 值 = RSV 的 EMA（平滑係數 1/3）
- D 值 = K 值的 EMA（平滑係數 1/3）

**KD 金叉判斷**：
- 前一天/前一週：K < D
- 今天/本週：K > D

**20MA 判斷**：
- 日線：當前價格 > 20 日均線
- 週線：當前價格 > 20 週均線

## 🏗️ 專案結構

```
fibonacci-flask-app/
│
├── app.py                    # 主應用程式，註冊藍圖和定義 HTML 模板
├── fibonacci_routes.py        # 斐波那契計算藍圖（fibo_bp）
├── stock_signals_routes.py   # 股票訊號查詢藍圖（signals_bp）
├── requirements.txt          # Python 依賴套件清單
├── Procfile                  # Heroku 部署配置
├── render.yaml               # Render 部署配置
├── runtime.txt              # Python 版本指定
└── README.md                # 專案說明文件
```

## 🔧 技術棧

- **後端框架**：Flask 3.0.0（使用 Blueprints 模組化架構）
- **數據獲取**：yfinance 0.2.28
- **數據處理**：pandas 2.0.3, numpy 1.24.3
- **前端技術**：HTML5, CSS3（內嵌於應用程式）
- **模板引擎**：Jinja2（Flask 內建）
- **部署伺服器**：gunicorn 21.2.0

## 📝 輸入驗證

### 斐波那契計算器
- ✅ 輸入必須為有效的浮點數
- ✅ 價格必須大於 0
- ✅ 高點價格必須大於低點價格

### 股票訊號查詢
- ✅ 自動清理輸入（移除空格、轉換為大寫）
- ✅ 自動移除可能的 `.TW` 或 `.TWO` 後綴
- ✅ 實現「嘗試-回退」邏輯（先嘗試 `.TW`，失敗則嘗試 `.TWO`）
- ✅ 提供清晰的錯誤訊息

## 🌐 部署

### Render 部署（推薦）

1. 登入 [Render](https://render.com) 並連接您的 GitHub 帳號
2. 點擊「New +」→「Web Service」
3. 選擇您的 GitHub 倉庫 `fibonacci-flask-app`
4. 配置以下設置：
   - **Name**: `fibonacci-flask-app`（或您喜歡的名稱）
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: 選擇免費或付費方案
5. 點擊「Create Web Service」
6. Render 會自動從 `render.yaml` 讀取配置（如果存在）

**重要提示**：
- 確保 Start Command 設置為：`gunicorn app:app`
- 如果使用 `render.yaml`，Render 會自動使用其中的配置
- 部署完成後，您會獲得一個 `*.onrender.com` 的網址

### Heroku 部署

1. 確保已安裝 [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. 登入 Heroku
   ```bash
   heroku login
   ```
3. 創建 Heroku 應用程式
   ```bash
   heroku create your-app-name
   ```
4. 推送程式碼
   ```bash
   git push heroku main
   ```

### 其他平台

此應用程式可以部署到任何支援 Python 的雲端平台，如：
- AWS Elastic Beanstalk
- Google App Engine
- Azure App Service
- DigitalOcean App Platform
- Railway

## 🔍 模組化架構說明

本專案採用 Flask Blueprints 實現模組化分工：

- **app.py**：主應用程式，負責初始化 Flask、註冊藍圖、定義 HTML 模板
- **fibonacci_routes.py**：定義 `fibo_bp` 藍圖，包含斐波那契計算邏輯和台股 Tick Size 修正
- **stock_signals_routes.py**：定義 `signals_bp` 藍圖，包含股票訊號查詢邏輯（KDJ/MA 計算）

## 📄 授權

此專案為開源專案，可自由使用和修改。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📧 聯絡方式

如有任何問題或建議，請透過 GitHub Issues 聯繫。

---

**免責聲明**：此工具僅供參考，不構成投資建議。投資有風險，請謹慎決策。所有計算結果和技術指標僅供分析參考，實際投資決策請諮詢專業投資顧問。
