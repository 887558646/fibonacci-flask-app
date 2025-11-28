"""
整合版台股投資工具
整合斐波那契計算器、股票訊號儀表板和族群熱度分析功能
"""

from flask import Flask, render_template_string, request, jsonify
import sys
import os

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 導入模組
from routes.fibonacci_routes import fibonacci_bp
from routes.stock_signals_routes import signals_bp
from routes.theme_analysis_routes import theme_analysis_bp

app = Flask(__name__)

# 註冊藍圖
app.register_blueprint(fibonacci_bp, url_prefix='/fibonacci')
app.register_blueprint(signals_bp, url_prefix='/signals')
app.register_blueprint(theme_analysis_bp, url_prefix='/theme-analysis')

# 載入主頁面模板
import os
template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'index.html')
with open(template_path, 'r', encoding='utf-8') as f:
    HTML_TEMPLATE = f.read()


@app.route('/', methods=['GET', 'POST'])
def index():
    """主頁面"""
    # 初始化變數
    context = {
        'fibonacci_error': None,
        'support_levels': None,
        'resistance_levels': None,
        'high_price': None,
        'low_price': None,
        'range_value': None,
        'signal_error': None,
        'stock_signals': None,
        'active_tab': 'fibonacci',  # 預設標籤頁
    }
    
    # 處理斐波那契計算表單
    if request.method == 'POST' and request.form.get('form_type') == 'fibonacci':
        context['active_tab'] = 'fibonacci'
        try:
            from routes.fibonacci_routes import fibonacci_calculator
            fibo_result = fibonacci_calculator()
            context.update({
                'fibonacci_error': fibo_result.get('fibonacci_error'),
                'support_levels': fibo_result.get('support_levels'),
                'resistance_levels': fibo_result.get('resistance_levels'),
                'high_price': fibo_result.get('high_price'),
                'low_price': fibo_result.get('low_price'),
                'range_value': fibo_result.get('range_value'),
            })
        except Exception as e:
            context['fibonacci_error'] = f'計算錯誤: {str(e)}'
    
    # 處理股票訊號表單
    if request.method == 'POST' and request.form.get('form_type') == 'signal':
        context['active_tab'] = 'signals'
        try:
            from routes.stock_signals_routes import stock_signals
            signals_result = stock_signals()
            context.update({
                'signal_error': signals_result.get('signal_error'),
                'stock_signals': signals_result.get('stock_signals'),
            })
        except Exception as e:
            context['signal_error'] = f'查詢錯誤: {str(e)}'
    
    return render_template_string(HTML_TEMPLATE, **context)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

