# 📈 斐波那契擴展目標價計算器

一個基於 Flask 的網頁應用程式，用於計算股票的斐波那契擴展目標價。此工具幫助投資者根據歷史價格高點和低點，計算出潛在的價格目標水平。

## ✨ 功能特點

- 🎯 **五個斐波那契擴展水平**：計算 1.382、1.5、1.618、1.786、2.0 等關鍵擴展水平
- ✅ **穩健的輸入驗證**：確保輸入數據的有效性和邏輯正確性
- 🎨 **現代化使用者介面**：美觀的漸層設計，響應式布局
- 📊 **清晰的結果展示**：以表格形式呈現所有擴展水平及其對應的目標價格
- 📱 **響應式設計**：支援各種裝置和螢幕尺寸

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

1. 在表單中輸入股票的**高點價格**（High Price）
2. 輸入股票的**低點價格**（Low Price）
3. 點擊「計算斐波那契擴展目標價」按鈕
4. 查看計算結果表格，其中顯示各個擴展水平對應的目標價格

## 🧮 計算公式

應用程式使用以下公式計算斐波那契擴展目標價：

```
價格區間 (Range) = 高點價格 - 低點價格
目標價格 (Level Price) = 高點價格 + (價格區間 × (擴展水平 - 1))
```

### 擴展水平說明

- **1.382**：第一個重要的斐波那契擴展水平
- **1.5**：中間擴展水平
- **1.618**：黃金比例擴展水平（最常用）
- **1.786**：強勢擴展水平
- **2.0**：雙倍擴展水平

## 🏗️ 專案結構

```
fibonacci-flask-app/
│
├── app.py              # 主應用程式檔案
├── requirements.txt    # Python 依賴套件清單
├── Procfile           # Heroku 部署配置
└── README.md          # 專案說明文件
```

## 🔧 技術棧

- **後端框架**：Flask 3.0.0
- **前端技術**：HTML5, CSS3 (內嵌於應用程式)
- **模板引擎**：Jinja2 (Flask 內建)

## 📝 輸入驗證

應用程式會自動驗證以下條件：

- ✅ 輸入必須為有效的浮點數
- ✅ 價格必須大於 0
- ✅ 高點價格必須大於低點價格

## 🌐 部署

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

### Render 部署

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

### 其他平台

此應用程式可以部署到任何支援 Python 的雲端平台，如：
- AWS Elastic Beanstalk
- Google App Engine
- Azure App Service
- DigitalOcean App Platform
- Railway

## 📄 授權

此專案為開源專案，可自由使用和修改。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📧 聯絡方式

如有任何問題或建議，請透過 GitHub Issues 聯繫。

---

**注意**：此工具僅供參考，不構成投資建議。投資有風險，請謹慎決策。

