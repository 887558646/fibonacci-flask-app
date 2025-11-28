from flask import Blueprint
import math
import sys
import os

# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

fibonacci_bp = Blueprint('fibonacci', __name__)

# 斐波那契回撤水平（支撐位）
FIBONACCI_RETRACEMENT_LEVELS = [0.236, 0.382, 0.500, 0.618]

# 斐波那契擴展水平（壓力位）
FIBONACCI_EXTENSION_LEVELS = [1.382, 1.5, 1.618, 1.786, 2.0]


def get_tick_size(price):
    """
    根據價格獲取台股 Tick Size
    規則：
    - < 10: 0.01
    - 10-50: 0.05
    - 50-100: 0.10
    - 100-500: 0.50
    - 500-1000: 1.00
    - >= 1000: 5.00
    """
    if price < 10:
        return 0.01
    elif price < 50:
        return 0.05
    elif price < 100:
        return 0.10
    elif price < 500:
        return 0.50
    elif price < 1000:
        return 1.00
    else:
        return 5.00


def adjust_to_tick(price, direction):
    """
    將價格調整到符合台股 Tick Size 規則的核心修正函數
    
    參數:
        price: 原始價格
        direction: 'resistance' (壓力/擴展) 或 'support' (支撐/回撤)
    
    規則:
        - direction='resistance' (壓力/擴展): 向下取整 (floor)，取最接近且小於或等於 price 的 Tick 價格
        - direction='support' (支撐/回撤): 向上取整 (ceil)，取最接近且大於或等於 price 的 Tick 價格
    
    返回:
        調整後的價格（符合台股 Tick Size 規則）
    """
    tick_size = get_tick_size(price)
    
    if direction == 'resistance':
        # 壓力/擴展：向下取整 (floor)，取最接近且小於或等於 price 的 Tick 價格
        adjusted_price = math.floor(price / tick_size) * tick_size
    elif direction == 'support':
        # 支撐/回撤：向上取整 (ceil)，取最接近且大於或等於 price 的 Tick 價格
        adjusted_price = math.ceil(price / tick_size) * tick_size
    else:
        # 預設行為：不調整
        adjusted_price = price
    
    return round(adjusted_price, 2)


def fibonacci_calculator():
    """斐波那契計算器邏輯（返回數據字典）"""
    from flask import request
    
    error = None
    support_levels = None
    resistance_levels = None
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
                        
                        # 計算潛在支撐位（斐波那契回撤）
                        # 公式: Level Price = High Price - (Range * Retracement Percentage)
                        support_levels = []
                        for level in FIBONACCI_RETRACEMENT_LEVELS:
                            support_price = high_price - (range_value * level)
                            # 應用 Tick Size 修正（支撐位向上取整）
                            adjusted_price = adjust_to_tick(support_price, direction='support')
                            support_levels.append((level, adjusted_price))
                        
                        # 計算潛在壓力位（斐波那契擴展）
                        # 公式: Level Price = High Price + (Range * (Extension - 1))
                        resistance_levels = []
                        for level in FIBONACCI_EXTENSION_LEVELS:
                            resistance_price = high_price + (range_value * (level - 1))
                            # 應用 Tick Size 修正（壓力位向下取整）
                            adjusted_price = adjust_to_tick(resistance_price, direction='resistance')
                            resistance_levels.append((level, adjusted_price))
        
        except Exception as e:
            error = f"計算過程中發生錯誤: {str(e)}"
    
    return {
        'fibonacci_error': error,
        'support_levels': support_levels,
        'resistance_levels': resistance_levels,
        'high_price': high_price,
        'low_price': low_price,
        'range_value': range_value
    }

