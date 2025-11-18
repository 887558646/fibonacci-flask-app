from flask import Flask, request, render_template_string

app = Flask(__name__)

# 斐波那契擴展水平
FIBONACCI_LEVELS = [1.382, 1.5, 1.618, 1.786, 2.0]

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>斐波那契擴展目標價計算器</title>
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
            max-width: 700px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
            font-weight: 600;
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
        
        input[type="number"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="number"]:focus {
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
        
        .results {
            margin-top: 30px;
            display: none;
        }
        
        .results.show {
            display: block;
        }
        
        .results h2 {
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
            color: #27ae60;
            font-size: 16px;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 斐波那契擴展目標價計算器</h1>
        
        <form method="POST" id="fibonacciForm">
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
            
            <button type="submit">計算斐波那契擴展目標價</button>
        </form>
        
        {% if error %}
        <div class="error show" style="margin-top: 15px; padding: 12px; background: #fee; border-radius: 8px; border-left: 4px solid #e74c3c;">
            {{ error }}
        </div>
        {% endif %}
        
        {% if results %}
        <div class="results show">
            <h2>計算結果</h2>
            <table>
                <thead>
                    <tr>
                        <th>擴展水平</th>
                        <th>目標價格</th>
                    </tr>
                </thead>
                <tbody>
                    {% for level, price in results %}
                    <tr>
                        <td class="level">{{ level }}</td>
                        <td class="price">{{ "%.2f"|format(price) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <div class="info-box">
                <p><strong>高點價格:</strong> {{ "%.2f"|format(high_price) }}</p>
                <p><strong>低點價格:</strong> {{ "%.2f"|format(low_price) }}</p>
                <p><strong>價格區間:</strong> {{ "%.2f"|format(range_value) }}</p>
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    results = None
    high_price = None
    low_price = None
    range_value = None
    
    if request.method == 'POST':
        try:
            # 獲取並驗證輸入
            high_price_str = request.form.get('high_price', '').strip()
            low_price_str = request.form.get('low_price', '').strip()
            
            # 檢查是否為空
            if not high_price_str or not low_price_str:
                error = "請輸入高點價格和低點價格"
            else:
                # 嘗試轉換為浮點數
                try:
                    high_price = float(high_price_str)
                    low_price = float(low_price_str)
                except ValueError:
                    error = "請輸入有效的數字"
                
                # 驗證價格範圍
                if error is None:
                    if high_price <= 0 or low_price <= 0:
                        error = "價格必須大於 0"
                    elif high_price <= low_price:
                        error = "高點價格必須大於低點價格"
                    else:
                        # 計算價格區間
                        range_value = high_price - low_price
                        
                        # 計算各斐波那契擴展水平
                        results = []
                        for level in FIBONACCI_LEVELS:
                            # 公式: Level Price = High Price + (Range * (Extension - 1))
                            target_price = high_price + (range_value * (level - 1))
                            results.append((level, target_price))
        
        except Exception as e:
            error = f"計算過程中發生錯誤: {str(e)}"
    
    return render_template_string(
        HTML_TEMPLATE,
        error=error,
        results=results,
        high_price=high_price,
        low_price=low_price,
        range_value=range_value
    )


if __name__ == '__main__':
    app.run(debug=False)

