from flask import Flask, render_template_string
from stock_signals_routes import signals_bp

app = Flask(__name__)

# 註冊藍圖
# 注意：fibo_bp 不註冊路由，只使用其函數邏輯（避免與主路由 '/' 衝突）
# signals_bp 註冊為 '/signals'
app.register_blueprint(signals_bp, url_prefix='/signals')

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>斐波那契計算器 & 股票訊號儀表板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            padding: 40px;
            max-width: 1200px;
            width: 100%;
        }
        
        .section {
            margin-bottom: 50px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 12px;
            border: 2px solid #e0e0e0;
        }
        
        .section:last-child {
            margin-bottom: 0;
        }
        
        .section h2 {
            color: #333;
            margin-bottom: 25px;
            font-size: 24px;
            font-weight: 600;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
            font-size: 14px;
        }
        
        input[type="number"],
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="number"]:focus,
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .error {
            color: #e74c3c;
            font-size: 14px;
            margin-top: 5px;
            display: none;
        }
        
        .error.show {
            display: block;
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .btn-signal {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .signal-card {
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-top: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .signal-group {
            margin-bottom: 25px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .signal-group:last-child {
            margin-bottom: 0;
        }
        
        .signal-group-title {
            color: #333;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .signal-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e8e8e8;
        }
        
        .signal-item:last-child {
            border-bottom: none;
        }
        
        .signal-label {
            font-weight: 600;
            color: #555;
        }
        
        .signal-value {
            font-weight: 600;
            font-size: 16px;
        }
        
        .signal-yes {
            color: #27ae60;
        }
        
        .signal-no {
            color: #e74c3c;
        }
        
        .stock-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .stock-info h3 {
            margin: 0;
            font-size: 20px;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .section {
                padding: 20px;
            }
            
            .signal-group {
                padding: 15px;
            }
        }
        
        .results {
            margin-top: 30px;
            display: none;
        }
        
        .results.show {
            display: block;
        }
        
        .results h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 22px;
            text-align: center;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
        }
        
        tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        tbody tr:last-child td {
            border-bottom: none;
        }
        
        .level {
            font-weight: 600;
            color: #667eea;
        }
        
        .price {
            font-weight: 600;
            font-size: 16px;
        }
        
        .support-price {
            color: #27ae60;
        }
        
        .resistance-price {
            color: #e74c3c;
        }
        
        .table-section {
            margin-bottom: 30px;
        }
        
        .table-section h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
            font-weight: 600;
        }
        
        .support-table thead {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
        }
        
        .resistance-table thead {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        }
        
        .info-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-top: 20px;
            border-radius: 4px;
        }
        
        .info-box p {
            margin: 5px 0;
            color: #555;
            font-size: 14px;
        }
        
        .info-box strong {
            color: #333;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .error-message {
            animation: slideIn 0.3s ease-out;
        }
        
        .success-message {
            animation: slideIn 0.3s ease-out;
            margin-top: 15px;
            padding: 15px;
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border-radius: 8px;
            border-left: 4px solid #27ae60;
            box-shadow: 0 2px 8px rgba(39, 174, 96, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 斐波那契計算器 & 股票訊號儀表板</h1>
        
        <!-- 斐波那契計算器區塊 -->
        <div class="section">
            <h2>📊 斐波那契支撐位與壓力位計算器</h2>
            
            <form method="POST" action="/">
                <input type="hidden" name="form_type" value="fibonacci">
                <div class="form-group">
                    <label for="high_price">高點價格 (High Price):</label>
                    <input type="number" 
                           id="high_price" 
                           name="high_price" 
                           step="0.01" 
                           min="0" 
                           required
                           value="{{ request.form.get('high_price', '') if request.form else '' }}">
                    <div class="error" id="high_error"></div>
                </div>
                
                <div class="form-group">
                    <label for="low_price">低點價格 (Low Price):</label>
                    <input type="number" 
                           id="low_price" 
                           name="low_price" 
                           step="0.01" 
                           min="0" 
                           required
                           value="{{ request.form.get('low_price', '') if request.form else '' }}">
                    <div class="error" id="low_error"></div>
                </div>
                
                <button type="submit">計算斐波那契支撐位與壓力位</button>
            </form>
            
            {% if fibonacci_error %}
            <div class="error-message" style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #fee 0%, #fdd 100%); border-radius: 8px; border-left: 4px solid #e74c3c; box-shadow: 0 2px 8px rgba(231, 76, 60, 0.2); animation: slideIn 0.3s ease-out;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">⚠️</span>
                    <div>
                        <strong style="color: #c0392b; font-size: 16px;">計算錯誤</strong>
                        <p style="margin: 5px 0 0 0; color: #555; font-size: 14px;">{{ fibonacci_error }}</p>
                    </div>
                </div>
            </div>
            {% endif %}
            
            {% if support_levels or resistance_levels %}
            <div class="results show">
                <h3 style="margin-top: 20px; margin-bottom: 15px;">計算結果</h3>
                
                {% if support_levels %}
                <div class="table-section">
                    <h3>🛡️ 潛在支撐位 (斐波那契回撤)</h3>
                    <table class="support-table">
                        <thead>
                            <tr>
                                <th>回撤水平</th>
                                <th>支撐價格</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for level, price in support_levels %}
                            <tr>
                                <td class="level">{{ "%.3f"|format(level) }}</td>
                                <td class="price support-price">{{ "%.2f"|format(price) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}
                
                {% if resistance_levels %}
                <div class="table-section">
                    <h3>📊 潛在壓力位 (斐波那契擴展)</h3>
                    <table class="resistance-table">
                        <thead>
                            <tr>
                                <th>擴展水平</th>
                                <th>壓力價格</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for level, price in resistance_levels %}
                            <tr>
                                <td class="level">{{ "%.3f"|format(level) }}</td>
                                <td class="price resistance-price">{{ "%.2f"|format(price) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}
                
                <div class="info-box">
                    <p><strong>高點價格:</strong> {{ "%.2f"|format(high_price) }}</p>
                    <p><strong>低點價格:</strong> {{ "%.2f"|format(low_price) }}</p>
                    <p><strong>價格區間:</strong> {{ "%.2f"|format(range_value) }}</p>
                </div>
            </div>
            {% endif %}
        </div>
        
        <!-- 股票訊號儀表板區塊 -->
        <div class="section">
            <h2>📈 股票訊號儀表板</h2>
            
            <form method="POST" action="/">
                <input type="hidden" name="form_type" value="signal">
                <div class="form-group">
                    <label for="ticker">台股代碼:</label>
                    <input type="text" 
                           id="ticker" 
                           name="ticker" 
                           placeholder="例如: 2330, 2317, 2454 (無需輸入.TW)"
                           required
                           value="{{ request.form.get('ticker', '') if request.form and request.form.get('form_type') == 'signal' else '' }}">
                    <div class="error" id="ticker_error"></div>
                </div>
                
                <button type="submit" class="btn-signal">查詢股票訊號</button>
            </form>
            
            {% if signal_error %}
            <div class="error-message" style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #fee 0%, #fdd 100%); border-radius: 8px; border-left: 4px solid #e74c3c; box-shadow: 0 2px 8px rgba(231, 76, 60, 0.2);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">⚠️</span>
                    <div>
                        <strong style="color: #c0392b; font-size: 16px;">查詢失敗</strong>
                        <p style="margin: 5px 0 0 0; color: #555; font-size: 14px;">{{ signal_error }}</p>
                    </div>
                </div>
            </div>
            {% endif %}
            
            {% if stock_signals %}
            <div class="signal-card">
                {% if stock_signals.stock_name %}
                <div class="stock-info">
                    <h3>{{ stock_signals.stock_name }} ({{ stock_signals.ticker_display }})</h3>
                </div>
                {% endif %}
                
                <!-- 日線訊號區塊 -->
                <div class="signal-group">
                    <h4 class="signal-group-title">📊 日線訊號</h4>
                    <div class="signal-item">
                        <span class="signal-label">日 KD 金叉:</span>
                        <span class="signal-value {% if stock_signals.daily_kd_golden_cross %}signal-yes{% else %}signal-no{% endif %}">
                            {% if stock_signals.daily_kd_golden_cross %}✓ 是{% else %}✗ 否{% endif %}
                        </span>
                    </div>
                    {% if stock_signals.daily_k is not none %}
                    <div class="signal-item">
                        <span class="signal-label">日 K 值:</span>
                        <span class="signal-value">{{ "%.2f"|format(stock_signals.daily_k) }}</span>
                    </div>
                    <div class="signal-item">
                        <span class="signal-label">日 D 值:</span>
                        <span class="signal-value">{{ "%.2f"|format(stock_signals.daily_d) }}</span>
                    </div>
                    {% endif %}
                    <div class="signal-item">
                        <span class="signal-label">日線價格站上 20MA:</span>
                        <span class="signal-value {% if stock_signals.daily_price_above_ma20 %}signal-yes{% else %}signal-no{% endif %}">
                            {% if stock_signals.daily_price_above_ma20 %}✓ 是{% else %}✗ 否{% endif %}
                        </span>
                    </div>
                    {% if stock_signals.current_price is not none %}
                    <div class="signal-item">
                        <span class="signal-label">日線當前價格:</span>
                        <span class="signal-value">{{ "%.2f"|format(stock_signals.current_price) }}</span>
                    </div>
                    {% endif %}
                    {% if stock_signals.daily_ma20 is not none %}
                    <div class="signal-item">
                        <span class="signal-label">日線 20 日均線:</span>
                        <span class="signal-value">{{ "%.2f"|format(stock_signals.daily_ma20) }}</span>
                    </div>
                    {% endif %}
                </div>
                
                <!-- 週線訊號區塊 -->
                <div class="signal-group">
                    <h4 class="signal-group-title">📈 週線訊號</h4>
                    <div class="signal-item">
                        <span class="signal-label">週 KD 金叉:</span>
                        <span class="signal-value {% if stock_signals.weekly_kd_golden_cross %}signal-yes{% else %}signal-no{% endif %}">
                            {% if stock_signals.weekly_kd_golden_cross %}✓ 是{% else %}✗ 否{% endif %}
                        </span>
                    </div>
                    {% if stock_signals.weekly_k is not none %}
                    <div class="signal-item">
                        <span class="signal-label">週 K 值:</span>
                        <span class="signal-value">{{ "%.2f"|format(stock_signals.weekly_k) }}</span>
                    </div>
                    <div class="signal-item">
                        <span class="signal-label">週 D 值:</span>
                        <span class="signal-value">{{ "%.2f"|format(stock_signals.weekly_d) }}</span>
                    </div>
                    {% endif %}
                    <div class="signal-item">
                        <span class="signal-label">週線價格站上 20MA:</span>
                        <span class="signal-value {% if stock_signals.weekly_price_above_ma20 %}signal-yes{% else %}signal-no{% endif %}">
                            {% if stock_signals.weekly_price_above_ma20 %}✓ 是{% else %}✗ 否{% endif %}
                        </span>
                    </div>
                    {% if stock_signals.weekly_price is not none %}
                    <div class="signal-item">
                        <span class="signal-label">週線當前價格:</span>
                        <span class="signal-value">{{ "%.2f"|format(stock_signals.weekly_price) }}</span>
                    </div>
                    {% endif %}
                    {% if stock_signals.weekly_ma20 is not none %}
                    <div class="signal-item">
                        <span class="signal-label">週線 20 週均線:</span>
                        <span class="signal-value">{{ "%.2f"|format(stock_signals.weekly_ma20) }}</span>
                    </div>
                    {% endif %}
                </div>
                
                <!-- 多重關鍵支撐與壓力位區塊 -->
                {% if stock_signals.r1 is not none or stock_signals.r2 is not none or stock_signals.r3 is not none or stock_signals.s1 is not none or stock_signals.s2 is not none or stock_signals.s3 is not none %}
                <div class="signal-group" style="margin-top: 25px;">
                    <h4 class="signal-group-title">🎯 多重關鍵支撐與壓力位（分形指標）</h4>
                    
                    {% if stock_signals.support_resistance_error %}
                    <div class="error-message" style="margin-top: 10px; padding: 10px; background: linear-gradient(135deg, #fee 0%, #fdd 100%); border-radius: 8px; border-left: 4px solid #e74c3c;">
                        <p style="margin: 0; color: #555; font-size: 14px;">{{ stock_signals.support_resistance_error }}</p>
                    </div>
                    {% endif %}
                    
                    <div style="margin-top: 15px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                                    <th style="padding: 12px; text-align: left; font-weight: 600; font-size: 14px;">價位類型</th>
                                    <th style="padding: 12px; text-align: right; font-weight: 600; font-size: 14px;">價格</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% if stock_signals.r3 is not none %}
                                <tr style="border-bottom: 1px solid #f0f0f0; background-color: #fff5f5;">
                                    <td style="padding: 12px; font-weight: 600; color: #555;">壓力位 R3（最遠）</td>
                                    <td style="padding: 12px; text-align: right; font-weight: 700; font-size: 16px; color: #c0392b;">{{ "%.2f"|format(stock_signals.r3) }}</td>
                                </tr>
                                {% endif %}
                                {% if stock_signals.r2 is not none %}
                                <tr style="border-bottom: 1px solid #f0f0f0; background-color: #fff5f5;">
                                    <td style="padding: 12px; font-weight: 600; color: #555;">壓力位 R2</td>
                                    <td style="padding: 12px; text-align: right; font-weight: 700; font-size: 16px; color: #e74c3c;">{{ "%.2f"|format(stock_signals.r2) }}</td>
                                </tr>
                                {% endif %}
                                {% if stock_signals.r1 is not none %}
                                <tr style="border-bottom: 2px solid #667eea; background-color: #fff5f5;">
                                    <td style="padding: 12px; font-weight: 600; color: #555;">壓力位 R1（最近）</td>
                                    <td style="padding: 12px; text-align: right; font-weight: 700; font-size: 16px; color: #e74c3c;">{{ "%.2f"|format(stock_signals.r1) }}</td>
                                </tr>
                                {% endif %}
                                
                                <!-- 當前價格分隔線 -->
                                {% if stock_signals.current_price is not none %}
                                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-top: 2px solid #667eea; border-bottom: 2px solid #667eea;">
                                    <td style="padding: 14px; text-align: center; font-weight: 700; font-size: 16px; color: white;" colspan="2">
                                        ═══ 當前價格：{{ "%.2f"|format(stock_signals.current_price) }} ═══
                                    </td>
                                </tr>
                                {% endif %}
                                
                                {% if stock_signals.s1 is not none %}
                                <tr style="border-top: 2px solid #27ae60; background-color: #f0fff4;">
                                    <td style="padding: 12px; font-weight: 600; color: #555;">支撐位 S1（最近）</td>
                                    <td style="padding: 12px; text-align: right; font-weight: 700; font-size: 16px; color: #27ae60;">{{ "%.2f"|format(stock_signals.s1) }}</td>
                                </tr>
                                {% endif %}
                                {% if stock_signals.s2 is not none %}
                                <tr style="border-bottom: 1px solid #f0f0f0; background-color: #f0fff4;">
                                    <td style="padding: 12px; font-weight: 600; color: #555;">支撐位 S2</td>
                                    <td style="padding: 12px; text-align: right; font-weight: 700; font-size: 16px; color: #27ae60;">{{ "%.2f"|format(stock_signals.s2) }}</td>
                                </tr>
                                {% endif %}
                                {% if stock_signals.s3 is not none %}
                                <tr style="background-color: #f0fff4;">
                                    <td style="padding: 12px; font-weight: 600; color: #555;">支撐位 S3（最遠）</td>
                                    <td style="padding: 12px; text-align: right; font-weight: 700; font-size: 16px; color: #2ecc71;">{{ "%.2f"|format(stock_signals.s3) }}</td>
                                </tr>
                                {% endif %}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="info-box" style="margin-top: 15px;">
                        <p style="margin: 5px 0; color: #555; font-size: 13px;"><strong>說明：</strong></p>
                        <p style="margin: 5px 0; color: #555; font-size: 12px;">• <strong>分形指標 (Fractals)</strong>：參考 TradingView 的分形指標，識別高於/低於左右各5根K棒的關鍵價位</p>
                        <p style="margin: 5px 0; color: #555; font-size: 12px;">• <strong>多重壓力位 (R1-R3)</strong>：從過去2年數據中找出 > 當前價格的分形高點，由近到遠排序，取前3個</p>
                        <p style="margin: 5px 0; color: #555; font-size: 12px;">• <strong>多重支撐位 (S1-S3)</strong>：從過去2年數據中找出 < 當前價格的分形低點，由近到遠排序，取前3個</p>
                        <p style="margin: 5px 0; color: #555; font-size: 12px;">• <strong>價格修正</strong>：所有價格已根據台股升降單位 (Tick Size) 進行修正（壓力位向下取整，支撐位向上取整）</p>
                        <p style="margin: 5px 0; color: #555; font-size: 12px;">• <strong>過濾重複</strong>：自動過濾重複的價格值，確保每個價位都是唯一的</p>
                    </div>
                </div>
                {% endif %}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    """主頁面，渲染包含兩個功能區塊的模板"""
    from flask import request
    
    # 初始化變數
    fibonacci_error = None
    support_levels = None
    resistance_levels = None
    high_price = None
    low_price = None
    range_value = None
    signal_error = None
    stock_signals = None
    
    # 處理斐波那契計算表單
    if request.method == 'POST' and (request.form.get('form_type') == 'fibonacci' or (request.form.get('high_price') and request.form.get('low_price'))):
        try:
            from fibonacci_routes import fibonacci_calculator
            fibo_result = fibonacci_calculator()
        except Exception as e:
            fibo_result = {'fibonacci_error': f'導入錯誤: {str(e)}'}
        fibonacci_error = fibo_result.get('fibonacci_error')
        support_levels = fibo_result.get('support_levels')
        resistance_levels = fibo_result.get('resistance_levels')
        high_price = fibo_result.get('high_price')
        low_price = fibo_result.get('low_price')
        range_value = fibo_result.get('range_value')
    
    # 處理股票訊號表單
    if request.method == 'POST' and request.form.get('form_type') == 'signal':
        try:
            from stock_signals_routes import stock_signals
            signals_result = stock_signals()
        except Exception as e:
            signals_result = {'signal_error': f'導入錯誤: {str(e)}'}
        signal_error = signals_result.get('signal_error')
        stock_signals = signals_result.get('stock_signals')
    
    return render_template_string(
        HTML_TEMPLATE,
        fibonacci_error=fibonacci_error,
        support_levels=support_levels,
        resistance_levels=resistance_levels,
        high_price=high_price,
        low_price=low_price,
        range_value=range_value,
        signal_error=signal_error,
        stock_signals=stock_signals
    )


if __name__ == '__main__':
    app.run(debug=False)
