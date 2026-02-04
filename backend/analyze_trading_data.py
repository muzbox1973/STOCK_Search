"""
매매 전략 수립을 위한 네이버 금융 데이터 분석 스크립트

이 스크립트는 네이버 금융 페이지에서 트레이딩 전략에 필요한 모든 데이터를 추출합니다.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional


def analyze_naver_finance_page(ticker: str = "005930"):
    """
    네이버 금융 페이지를 분석하여 사용 가능한 모든 데이터 포인트를 출력합니다.
    """
    url = f"https://finance.naver.com/item/main.naver?code={ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    
    try:
        content = response.content.decode('utf-8')
    except:
        content = response.content.decode('euc-kr', errors='replace')
    
    soup = BeautifulSoup(content, 'html.parser')
    
    print("=" * 80)
    print(f"네이버 금융 페이지 분석: {ticker}")
    print("=" * 80)
    
    # 1. 모든 테이블 찾기
    print("\n[1] 페이지 내 테이블 목록:")
    tables = soup.find_all('table')
    for i, table in enumerate(tables):
        summary = table.get('summary', 'no summary')
        class_name = table.get('class', ['no class'])
        print(f"  Table {i}: summary='{summary}', class='{class_name}'")
    
    # 2. 시세 정보 (today 영역)
    print("\n[2] 시세 정보 (today 영역):")
    today_div = soup.find('div', class_='today')
    if today_div:
        print(f"  Found: {today_div.get_text()[:200]}")
    
    # 3. 주요 시세 테이블
    print("\n[3] 주요 시세 테이블:")
    per_tables = soup.find_all('table', class_='per_table')
    for i, table in enumerate(per_tables):
        print(f"  per_table {i}:")
        rows = table.find_all('tr')
        for row in rows[:5]:  # 처음 5행만
            cells = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])]
            print(f"    {cells}")
    
    # 4. 투자정보 섹션
    print("\n[4] 투자정보 섹션:")
    sub_sections = soup.find_all('div', class_='sub_section')
    for i, section in enumerate(sub_sections):
        text = section.get_text(strip=True)[:200]
        print(f"  sub_section {i}: {text}")
    
    # 5. em 태그들 (주요 수치)
    print("\n[5] <em> 태그 내 주요 수치:")
    em_tags = soup.find_all('em')
    for i, em in enumerate(em_tags[:20]):  # 처음 20개만
        text = em.get_text(strip=True)
        if text and len(text) < 50:
            print(f"  em {i}: {text}")
    
    # 6. blind 클래스 (접근성 텍스트)
    print("\n[6] blind 클래스 (데이터 레이블):")
    blinds = soup.find_all(class_='blind')
    for i, blind in enumerate(blinds[:30]):
        text = blind.get_text(strip=True)
        if text and '종목' in text or '가격' in text or '거래' in text:
            print(f"  blind {i}: {text}")
    
    return soup


if __name__ == "__main__":
    # 삼성전자 페이지 분석
    soup = analyze_naver_finance_page("005930")
    
    print("\n" + "=" * 80)
    print("분석 완료!")
    print("=" * 80)
