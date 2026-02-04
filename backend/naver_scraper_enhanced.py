"""
Enhanced Naver Finance Scraper
네이버 금융 페이지에서 주식 정보를 추출하는 모듈

Based on DOM structure analysis from finance.naver.com/item/main.naver
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional


class NaverFinanceScraper:
    """네이버 금융 데이터 스크래퍼"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
    
    def fetch_page(self, ticker: str) -> Optional[BeautifulSoup]:
        """
        종목 코드로 네이버 금융 페이지를 가져옵니다.
        
        Args:
            ticker: 종목 코드 (예: "005930")
            
        Returns:
            BeautifulSoup 객체 또는 None
        """
        try:
            url = f"https://finance.naver.com/item/main.naver?code={ticker}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            # Try UTF-8 first, fallback to EUC-KR
            try:
                content = response.content.decode('utf-8')
            except:
                content = response.content.decode('euc-kr', errors='replace')
            
            return BeautifulSoup(content, 'html.parser')
        except Exception as e:
            print(f"[ERROR] Failed to fetch page for {ticker}: {e}")
            return None
    
    def extract_current_price(self, soup: BeautifulSoup) -> str:
        """
        현재가 추출
        
        방법 1: 상단 시세 영역의 no_today 클래스
        방법 2: 동종업종비교 테이블
        """
        try:
            # 방법 1: 상단 시세 박스
            today_div = soup.find('div', class_='no_today')
            if today_div:
                blind = today_div.find('span', class_='blind')
                if blind:
                    price = blind.get_text(strip=True)
                    return price.replace(',', '')
            
            # 방법 2: 동종업종비교 테이블에서 현재가 추출
            compare_table = soup.find('table', summary=re.compile(r'동종업종'))
            if compare_table:
                rows = compare_table.find_all('tr')
                if len(rows) >= 3:  # 헤더 + 제목 + 데이터
                    first_data_row = rows[2]
                    cells = first_data_row.find_all('td')
                    if len(cells) >= 2:
                        price_text = cells[1].get_text(strip=True)
                        return price_text.replace(',', '')
        except Exception as e:
            print(f"[ERROR] Failed to extract current price: {e}")
        
        return "N/A"
    
    def extract_investment_opinion(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        투자의견 및 목표주가 추출
        
        텍스트 패턴: "투자의견 l 목표주가 4.00매수 l214,125"
        
        Returns:
            {
                'opinion_score': '4.00',
                'opinion_text': '매수',
                'target_price': '214,125'
            }
        """
        result = {
            'opinion_score': 'N/A',
            'opinion_text': 'N/A',
            'target_price': 'N/A'
        }
        
        try:
            # 투자정보 섹션 찾기
            all_elements = soup.find_all(['div', 'td', 'p', 'em'])
            
            for elem in all_elements:
                text = elem.get_text(strip=True)
                
                # "투자의견" 과 "목표주가" 가 모두 포함된 텍스트 찾기
                if '투자의견' in text and '목표주가' in text:
                    # 공백 정규화
                    normalized = re.sub(r'\s+', ' ', text)
                    
                    # 패턴 매칭: "투자의견 l 목표주가 4.00매수 l214,125"
                    # 또는 "투자의견 목표주가 4.00 매수 214,125" 등 다양한 형태
                    match = re.search(
                        r'투자의견\s*[l|]\s*목표주가\s*([\d.]+)\s*([가-힣]+)\s*[l|]\s*([\d,]+)',
                        normalized
                    )
                    
                    if match:
                        result['opinion_score'] = match.group(1)  # "4.00"
                        result['opinion_text'] = match.group(2)   # "매수"
                        result['target_price'] = match.group(3)   # "214,125"
                        break
                    
                    # 대체 패턴: 숫자와 한글이 분리된 경우
                    alt_match = re.search(
                        r'([\d.]+)\s*([가-힣]+).*?([\d,]+)',
                        normalized
                    )
                    if alt_match and any(word in alt_match.group(2) for word in ['매수', '매도', '중립', '보유']):
                        result['opinion_score'] = alt_match.group(1)
                        result['opinion_text'] = alt_match.group(2)
                        result['target_price'] = alt_match.group(3)
                        break
        
        except Exception as e:
            print(f"[ERROR] Failed to extract investment opinion: {e}")
        
        return result
    
    def extract_52week_range(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        52주 최고/최저가 추출
        
        텍스트 패턴: "52주최고 l 최저 168,500l52,500"
        
        Returns:
            {
                'high_52w': '168,500',
                'low_52w': '52,500'
            }
        """
        result = {
            'high_52w': 'N/A',
            'low_52w': 'N/A'
        }
        
        try:
            all_elements = soup.find_all(['div', 'td', 'p', 'em'])
            
            for elem in all_elements:
                text = elem.get_text(strip=True)
                
                # "52주최고" 와 "최저" 가 모두 포함된 텍스트 찾기
                if '52주최고' in text and '최저' in text:
                    # 공백 정규화
                    normalized = re.sub(r'\s+', ' ', text)
                    
                    # 패턴 매칭: "52주최고 l 최저 168,500l52,500"
                    match = re.search(
                        r'52주최고\s*[l|]\s*최저\s*([\d,]+)[l|]([\d,]+)',
                        normalized
                    )
                    
                    if match:
                        result['high_52w'] = match.group(1)  # "168,500"
                        result['low_52w'] = match.group(2)   # "52,500"
                        break
                    
                    # 대체 패턴: 공백으로 분리된 경우
                    alt_match = re.search(
                        r'52주.*?([\d,]+).*?([\d,]+)',
                        normalized
                    )
                    if alt_match:
                        result['high_52w'] = alt_match.group(1)
                        result['low_52w'] = alt_match.group(2)
                        break
        
        except Exception as e:
            print(f"[ERROR] Failed to extract 52-week range: {e}")
        
        return result
    
    def extract_sector(self, soup: BeautifulSoup) -> str:
        """
        업종 정보 추출
        
        방법 1: <th>업종</th> 다음의 <td>
        방법 2: <h4>업종명</h4> 다음의 <a>
        """
        try:
            # 방법 1: 테이블에서 "업종" th 찾기
            sector_th = soup.find('th', string=re.compile(r'업종'))
            if sector_th:
                sector_td = sector_th.find_next('td')
                if sector_td:
                    return sector_td.get_text(strip=True)
            
            # 방법 2: h4 태그에서 "업종명" 찾기
            sector_h4 = soup.find('h4', string=re.compile(r'업종명'))
            if sector_h4:
                sector_a = sector_h4.find_next('a')
                if sector_a:
                    return sector_a.get_text(strip=True)
        
        except Exception as e:
            print(f"[ERROR] Failed to extract sector: {e}")
        
        return "N/A"
    
    def get_stock_info(self, ticker: str) -> Dict[str, str]:
        """
        종목의 모든 정보를 한 번에 추출합니다.
        
        Args:
            ticker: 종목 코드
            
        Returns:
            {
                'current_price': 현재가,
                'opinion_score': 투자의견 점수,
                'opinion': 투자의견 텍스트,
                'target_price': 목표주가,
                'high_52w': 52주 최고가,
                'low_52w': 52주 최저가,
                'sector': 업종
            }
        """
        soup = self.fetch_page(ticker)
        
        if not soup:
            return {
                'current_price': 'N/A',
                'opinion_score': 'N/A',
                'opinion': 'N/A',
                'target_price': 'N/A',
                'high_52w': 'N/A',
                'low_52w': 'N/A',
                'sector': 'N/A'
            }
        
        # 각 정보 추출
        current_price = self.extract_current_price(soup)
        opinion_data = self.extract_investment_opinion(soup)
        week_52_data = self.extract_52week_range(soup)
        sector = self.extract_sector(soup)
        
        return {
            'current_price': current_price,
            'opinion_score': opinion_data['opinion_score'],
            'opinion': opinion_data['opinion_text'],
            'target_price': opinion_data['target_price'],
            'high_52w': week_52_data['high_52w'],
            'low_52w': week_52_data['low_52w'],
            'sector': sector
        }


# 헬퍼 함수 (기존 코드와의 호환성을 위해)
def parse_invest_info(soup: BeautifulSoup) -> Dict[str, str]:
    """
    투자정보 블록 전체를 파싱하는 헬퍼 함수
    
    사용 예시:
    ```python
    from bs4 import BeautifulSoup
    import requests
    
    response = requests.get('https://finance.naver.com/item/main.naver?code=005930')
    soup = BeautifulSoup(response.content, 'html.parser')
    info = parse_invest_info(soup)
    print(info)
    ```
    """
    scraper = NaverFinanceScraper()
    
    current_price = scraper.extract_current_price(soup)
    opinion_data = scraper.extract_investment_opinion(soup)
    week_52_data = scraper.extract_52week_range(soup)
    sector = scraper.extract_sector(soup)
    
    return {
        'currentPrice': current_price,
        'opinionScore': opinion_data['opinion_score'],
        'opinionText': opinion_data['opinion_text'],
        'targetPrice': opinion_data['target_price'],
        'high52': week_52_data['high_52w'],
        'low52': week_52_data['low_52w'],
        'sector': sector
    }


# 테스트 코드
if __name__ == "__main__":
    scraper = NaverFinanceScraper()
    
    # 삼성전자 테스트
    print("=" * 60)
    print("삼성전자 (005930) 정보 추출 테스트")
    print("=" * 60)
    
    info = scraper.get_stock_info("005930")
    
    for key, value in info.items():
        print(f"{key:20s}: {value}")
    
    print("\n" + "=" * 60)
