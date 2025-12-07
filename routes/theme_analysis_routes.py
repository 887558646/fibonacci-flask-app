"""
族群熱度分析路由
提供族群熱度分析、注意股分析等功能
"""

from flask import Blueprint, request, jsonify
import sys
import os
import pandas as pd
from datetime import datetime

# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入模組
from modules.data_loader import (
    load_supply_chain_json, 
    load_today_topN, 
    load_attention_stocks_from_web
)
from modules.theme_engine import map_stock_to_themes, calc_theme_heat
from modules.report_builder import build_theme_report, get_theme_detail_for_display

theme_analysis_bp = Blueprint('theme_analysis', __name__)


@theme_analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    """分析族群熱度"""
    try:
        data = request.get_json()
        top_n = data.get('top_n', None)
        
        if top_n:
            try:
                top_n = int(top_n)
                if top_n < 1:
                    return jsonify({'error': 'top_n 必須大於 0'}), 400
            except ValueError:
                return jsonify({'error': 'top_n 必須是有效的數字'}), 400
        
        # 載入週轉率資料
        stocks_df = load_today_topN(top_n=top_n, source="api")
        if stocks_df.empty:
            return jsonify({'error': '無法載入週轉率資料'}), 500
        
        # 載入族群定義
        themes_data = load_supply_chain_json()
        
        # 如果指定了 top_n，限制資料
        if top_n and top_n > 0:
            stocks_df = stocks_df.head(top_n).copy()
        
        # 計算族群對應與熱度
        stock_to_themes = map_stock_to_themes(stocks_df, themes_data)
        theme_heat_df = calc_theme_heat(stocks_df, stock_to_themes)
        
        # 建立報告
        turnover_report_data = build_theme_report(
            stocks_df, theme_heat_df, stock_to_themes, themes_data
        )
        
        # 嘗試載入注意股
        focus_df = pd.DataFrame()
        focus_report_data = None
        focus_stock_to_themes = {}
        
        try:
            focus_df = load_attention_stocks_from_web()
            if not focus_df.empty:
                # 標準化代碼格式
                focus_df['code'] = focus_df['code'].astype(str).str.strip()
                
                # 為注意股建立標準化代碼欄位（用於族群映射）
                # 只對 4 位代碼的注意股進行族群映射（6 位代碼是權證，不在族群定義中）
                focus_df['code_normalized'] = focus_df['code'].apply(
                    lambda x: x.zfill(4) if len(x) <= 4 else ''
                )
                
                # 建立一個用於族群分析的 DataFrame（只包含一般股票，排除權證）
                focus_for_theme = focus_df[focus_df['code_normalized'] != ''].copy()
                focus_for_theme['code'] = focus_for_theme['code_normalized']
                
                if not focus_for_theme.empty:
                    # 獨立對所有注意股進行族群映射（不需要週轉率資料）
                    focus_stock_to_themes = map_stock_to_themes(focus_for_theme, themes_data)
                    focus_theme_heat_df = calc_theme_heat(focus_for_theme, focus_stock_to_themes)
                    focus_report_data = build_theme_report(
                        focus_for_theme, focus_theme_heat_df, focus_stock_to_themes, themes_data
                    )
                
                # 移除臨時欄位
                if 'code_normalized' in focus_df.columns:
                    focus_df = focus_df.drop(columns=['code_normalized'])
        except Exception as e:
            # 注意股載入失敗不影響主流程，但記錄錯誤以便調試
            import traceback
            print(f"注意股載入失敗: {str(e)}")
            print(traceback.format_exc())
        
        # 計算平均週轉率
        avg_turnover = float(stocks_df['turnover'].mean()) if not stocks_df.empty else 0.0
        
        # 準備週轉率前N名清單
        turnover_stocks_list = []
        for _, row in stocks_df.iterrows():
            stock_code = str(row["code"]).zfill(4)
            turnover_stocks_list.append({
                'code': stock_code,
                'name': row.get('name', ''),
                'turnover': float(row.get('turnover', 0)) if pd.notna(row.get('turnover')) else None,
                'chg_pct': float(row.get('chg_pct', 0)) if pd.notna(row.get('chg_pct')) else None,
            })
        
        # 為每個族群準備個股清單
        theme_stocks_map = {}
        for theme_name in turnover_report_data['theme_heat_ranking']['theme_name'].tolist():
            # 取得該族群在 Top N 中實際出現的股票
            from modules.theme_engine import get_stocks_in_theme
            theme_stocks = get_stocks_in_theme(stocks_df, stock_to_themes, theme_name)
            if not theme_stocks.empty:
                theme_stocks_map[theme_name] = []
                for _, stock_row in theme_stocks.iterrows():
                    stock_code = str(stock_row["code"]).zfill(4)
                    theme_stocks_map[theme_name].append({
                        'code': stock_code,
                        'name': stock_row.get('name', ''),
                        'turnover': float(stock_row.get('turnover', 0)) if pd.notna(stock_row.get('turnover')) else None,
                        'chg_pct': float(stock_row.get('chg_pct', 0)) if pd.notna(stock_row.get('chg_pct')) else None,
                    })
        
        # 準備返回資料
        result = {
            'turnover_report': {
                'summary': {
                    'total_stocks': turnover_report_data['summary']['total_stocks'],
                    'total_themes': turnover_report_data['summary']['total_themes'],
                    'avg_turnover': avg_turnover
                },
                'theme_heat_ranking': turnover_report_data['theme_heat_ranking'].to_dict('records'),
                'theme_stocks': theme_stocks_map,  # 每個族群的個股清單
                'turnover_stocks_list': turnover_stocks_list,  # 週轉率前N名清單
                'unclassified_stocks': []
            }
        }
        
        # 找出未分類股票
        for _, row in stocks_df.iterrows():
            stock_code = str(row["code"]).zfill(4)
            themes = stock_to_themes.get(stock_code, [])
            if not themes:
                result['turnover_report']['unclassified_stocks'].append({
                    'code': stock_code,
                    'name': row.get('name', ''),
                    'turnover': float(row.get('turnover', 0)) if pd.notna(row.get('turnover')) else None,
                    'chg_pct': float(row.get('chg_pct', 0)) if pd.notna(row.get('chg_pct')) else None,
                })
        
        # 如果有注意股資料，獨立分析族群熱度
        if not focus_df.empty:
            # 準備注意股清單（直接使用爬取的資料）
            focus_stocks_list = []
            
            # 遍歷 focus_df，使用爬取的資料
            for _, row in focus_df.iterrows():
                # 保持原始代碼格式，不強制補零（因為代碼不一定是4碼）
                stock_code = str(row["code"]).strip()
                stock_name = row.get('name', '')
                # 直接使用爬取的事項描述
                detail = row.get('detail', '') if 'detail' in row.index else ''
                
                focus_stocks_list.append({
                    'code': stock_code,  # 使用原始代碼格式
                    'name': stock_name,
                    'detail': detail,  # 事項描述（從爬取的資料中取得）
                })
            
            # 計算一般股票（非權證）的注意股數量
            normal_stock_count = len([s for s in focus_stocks_list if len(s['code']) <= 4])
            
            # 為每個注意股族群準備個股清單
            focus_theme_stocks_map = {}
            theme_heat_ranking = []
            unclassified_stocks = []
            
            if focus_report_data:
                theme_heat_ranking = focus_report_data['theme_heat_ranking'].to_dict('records')
                
                # 建立一個用於查詢的 DataFrame
                focus_for_theme = focus_df.copy()
                focus_for_theme['code_normalized'] = focus_for_theme['code'].apply(
                    lambda x: x.zfill(4) if len(x) <= 4 else ''
                )
                focus_for_theme = focus_for_theme[focus_for_theme['code_normalized'] != '']
                focus_for_theme['code'] = focus_for_theme['code_normalized']
                
                for theme_name in focus_report_data['theme_heat_ranking']['theme_name'].tolist():
                    from modules.theme_engine import get_stocks_in_theme
                    theme_stocks = get_stocks_in_theme(focus_for_theme, focus_stock_to_themes, theme_name)
                    if not theme_stocks.empty:
                        focus_theme_stocks_map[theme_name] = []
                        for _, stock_row in theme_stocks.iterrows():
                            stock_code = str(stock_row["code"]).zfill(4)
                            # 從原始 focus_df 中查找名稱
                            orig_row = focus_df[focus_df['code'].str.zfill(4) == stock_code]
                            stock_name = orig_row.iloc[0].get('name', '') if not orig_row.empty else stock_row.get('name', '')
                            focus_theme_stocks_map[theme_name].append({
                                'code': stock_code,
                                'name': stock_name,
                            })
                
                # 找出未分類注意股（一般股票中不屬於任何族群的）
                for _, row in focus_for_theme.iterrows():
                    stock_code = str(row["code"]).zfill(4)
                    themes = focus_stock_to_themes.get(stock_code, [])
                    if not themes:
                        # 從原始 focus_df 中查找名稱
                        orig_row = focus_df[focus_df['code'].str.zfill(4) == stock_code]
                        stock_name = orig_row.iloc[0].get('name', '') if not orig_row.empty else row.get('name', '')
                        unclassified_stocks.append({
                            'code': stock_code,
                            'name': stock_name,
                        })
            
            result['focus_report'] = {
                'summary': {
                    'total_focus_stocks': len(focus_df),
                    'normal_stock_count': normal_stock_count,  # 一般股票（非權證）數量
                    'classified_themes': len(theme_heat_ranking)  # 涉及的族群數
                },
                'theme_heat_ranking': theme_heat_ranking,
                'theme_stocks': focus_theme_stocks_map,  # 每個族群的個股清單
                'focus_stocks_list': focus_stocks_list,  # 注意股清單
                'unclassified_stocks': unclassified_stocks  # 未分類注意股
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'分析失敗: {str(e)}'}), 500


@theme_analysis_bp.route('/theme-detail', methods=['POST'])
def theme_detail():
    """取得族群詳細資訊"""
    try:
        data = request.get_json()
        theme_name = data.get('theme_name')
        stocks_df = data.get('stocks_df')  # 應該是 JSON 格式的 DataFrame
        
        if not theme_name:
            return jsonify({'error': '請提供 theme_name'}), 400
        
        # 載入族群定義
        themes_data = load_supply_chain_json()
        
        # 如果有 stocks_df，轉換為 DataFrame
        today_df = pd.DataFrame(stocks_df) if stocks_df else pd.DataFrame()
        
        # 計算股票對應
        stock_to_themes = {}
        if not today_df.empty:
            stock_to_themes = map_stock_to_themes(today_df, themes_data)
        
        # 取得族群詳細資訊
        theme_detail_data = get_theme_detail_for_display(
            theme_name, today_df, themes_data, stock_to_themes
        )
        
        if not theme_detail_data:
            return jsonify({'error': f'找不到族群: {theme_name}'}), 404
        
        return jsonify(theme_detail_data)
        
    except Exception as e:
        return jsonify({'error': f'取得族群詳細資訊失敗: {str(e)}'}), 500


@theme_analysis_bp.route('/theme-list', methods=['GET'])
def theme_list():
    """取得所有族群清單"""
    try:
        themes_data = load_supply_chain_json()
        
        # 判斷格式
        themes_list = []
        if isinstance(themes_data, list):
            themes_list = themes_data
        elif "themes" in themes_data:
            themes_list = themes_data.get("themes", [])
        elif "popular_sectors" in themes_data:
            themes_list = themes_data.get("popular_sectors", [])
        else:
            themes_list = themes_data.get("族群清單", [])
        
        # 格式化返回資料
        result = []
        for theme_info in themes_list:
            if isinstance(theme_info, dict):
                theme_name = theme_info.get("theme") or theme_info.get("sector_name") or theme_info.get("族群名稱", "")
                description = theme_info.get("description", "")
                stocks = theme_info.get("stocks", [])
                
                result.append({
                    'theme_name': theme_name,
                    'description': description,
                    'stock_count': len(stocks) if isinstance(stocks, list) else 0
                })
        
        return jsonify({'themes': result})
        
    except Exception as e:
        return jsonify({'error': f'取得族群清單失敗: {str(e)}'}), 500

