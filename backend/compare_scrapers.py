"""
네이버 금융 스크래퍼 비교 테스트

기존 main.py의 analyze_stock 함수와 
새로운 naver_scraper_enhanced.py의 NaverFinanceScraper를 비교합니다.
"""

from naver_scraper_enhanced import NaverFinanceScraper
import requests
from bs4 import BeautifulSoup
import re


def clean_vb_text(text):
    """기존 main.py의 clean_vb_text 함수"""
    text = re.sub(r'<[^>]+>', '', text)
    text = "".join(ch for ch in text if ch.isprintable())
    return text.strip()


def old_method(ticker: str):
    """기존 main.py의 analyze_stock 로직"""
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        try:
            content = response.content.decode('utf-8')
        except:
            content = response.content.decode('euc-kr', errors='replace')
        
        soup = BeautifulSoup(content, 'html.parser')
        
        result = {
            "opinion": "N/A",
            "opinion_score": "N/A",
            "target_price": "N/S",
            "high_52w": "N/A",
            "low_52w": "N/A",
            "current_price": "N/A",
            "sector": "N/A"
        }
        
        # 투자의견 테이블 찾기
        invest_table = None
        all_tables = soup.find_all('table')
        for table in all_tables:
            summary = table.get('summary', '')
            if "투자의견" in summary or "목표주가" in table.get_text():
                invest_table = table
                break
        
        if invest_table:
            table_html = str(invest_table)
            chunks = table_html.split("<em>")[1:] 
            cleaned_vals = [clean_vb_text(chunk[:30]).replace(',', '') for chunk in chunks]
            
            if len(cleaned_vals) >= 4:
                result["opinion_score"] = cleaned_vals[0]
                full_val0 = clean_vb_text(chunks[0][:20])
                opinion_match = re.search(r'([가-힣]+)', full_val0)
                if opinion_match: 
                    result["opinion"] = opinion_match.group(1)
                
                if len(cleaned_vals) >= 2: 
                    result["target_price"] = f"{int(cleaned_vals[1]):,}" if cleaned_vals[1].isdigit() else cleaned_vals[1]
                if len(cleaned_vals) >= 3: 
                    result["high_52w"] = f"{int(cleaned_vals[2]):,}" if cleaned_vals[2].isdigit() else cleaned_vals[2]
                if len(cleaned_vals) >= 4: 
                    result["low_52w"] = f"{int(cleaned_vals[3]):,}" if cleaned_vals[3].isdigit() else cleaned_vals[3]
        
        # 현재가
        today_div = soup.find('div', class_='no_today')
        if today_div:
            blind = today_div.find('span', class_='blind')
            if blind:
                result["current_price"] = blind.get_text(strip=True)
        
        # 업종
        sector_th = soup.find('th', string=re.compile(r'업종'))
        if sector_th:
            result["sector"] = sector_th.find_next('td').get_text(strip=True)
        
        return result
    except Exception as e:
        return {"error": str(e)}


def new_method(ticker: str):
    """새로운 naver_scraper_enhanced.py 방식"""
    scraper = NaverFinanceScraper()
    return scraper.get_stock_info(ticker)


def compare_methods(ticker: str):
    """두 방법을 비교"""
    print(f"\n{'='*70}")
    print(f"종목 코드: {ticker}")
    print(f"{'='*70}\n")
    
    print("🔵 기존 방법 (main.py - VB 스타일)")
    print("-" * 70)
    old_result = old_method(ticker)
    for key, value in old_result.items():
        print(f"  {key:20s}: {value}")
    
    print("\n🟢 새로운 방법 (naver_scraper_enhanced.py)")
    print("-" * 70)
    new_result = new_method(ticker)
    for key, value in new_result.items():
        print(f"  {key:20s}: {value}")
    
    print("\n📊 비교 결과")
    print("-" * 70)
    
    # 매핑: old -> new 키 이름
    key_mapping = {
        'current_price': 'current_price',
        'opinion_score': 'opinion_score',
        'opinion': 'opinion',
        'target_price': 'target_price',
        'high_52w': 'high_52w',
        'low_52w': 'low_52w',
        'sector': 'sector'
    }
    
    differences = []
    for old_key, new_key in key_mapping.items():
        old_val = old_result.get(old_key, 'N/A')
        new_val = new_result.get(new_key, 'N/A')
        
        # 값 정규화 (쉼표 제거 등)
        old_normalized = str(old_val).replace(',', '').strip()
        new_normalized = str(new_val).replace(',', '').strip()
        
        match = "✅" if old_normalized == new_normalized else "❌"
        print(f"  {match} {old_key:20s}: {old_val} vs {new_val}")
        
        if old_normalized != new_normalized:
            differences.append((old_key, old_val, new_val))
    
    if differences:
        print("\n⚠️  차이점:")
        for key, old_val, new_val in differences:
            print(f"  - {key}: '{old_val}' → '{new_val}'")
    else:
        print("\n✨ 모든 값이 일치합니다!")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    # 테스트할 종목들
    test_tickers = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
    ]
    
    print("\n" + "="*70)
    print("네이버 금융 스크래퍼 비교 테스트")
    print("="*70)
    
    for ticker, name in test_tickers:
        print(f"\n테스트 중: {name} ({ticker})")
        compare_methods(ticker)
        print("\n" + "-"*70)
        input("다음 종목으로 계속하려면 Enter를 누르세요...")
