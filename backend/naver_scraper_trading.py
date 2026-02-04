"""
매매 전략 수립을 위한 네이버 금융 스크래퍼

이 모듈은 네이버 금융 페이지에서 매수/매도 전략 수립에 필요한
모든 핵심 지표를 추출합니다.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional


class TradingStrategyScraper:
    """매매 전략 수립을 위한 확장된 스크래퍼"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
    
    def fetch_page(self, ticker: str) -> Optional[BeautifulSoup]:
        """종목 코드로 네이버 금융 페이지를 가져옵니다."""
        try:
            url = f"https://finance.naver.com/item/main.naver?code={ticker}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            try:
                content = response.content.decode('utf-8')
            except:
                content = response.content.decode('euc-kr', errors='replace')
            
            return BeautifulSoup(content, 'html.parser')
        except Exception as e:
            print(f"[ERROR] Failed to fetch page for {ticker}: {e}")
            return None
    
    def _clean_number(self, text: str) -> str:
        """숫자 텍스트를 정리합니다 (쉼표 제거 등)."""
        if not text:
            return "N/A"
        # 숫자와 소수점, 마이너스만 남기기
        cleaned = re.sub(r'[^\d.\-]', '', text)
        return cleaned if cleaned else "N/A"
    
    def _format_number(self, text: str) -> str:
        """숫자에 쉼표를 추가합니다."""
        try:
            num = int(float(self._clean_number(text)))
            return f"{num:,}"
        except:
            return text
    
    def extract_price_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        가격 정보 추출
        
        Returns:
            {
                'current_price': 현재가,
                'opening_price': 시가,
                'high_price': 고가,
                'low_price': 저가,
                'prev_close': 전일종가,
                'upper_limit': 상한가,
                'lower_limit': 하한가,
                'high_52w': 52주 최고,
                'low_52w': 52주 최저
            }
        """
        result = {
            'current_price': 'N/A',
            'opening_price': 'N/A',
            'high_price': 'N/A',
            'low_price': 'N/A',
            'prev_close': 'N/A',
            'upper_limit': 'N/A',
            'lower_limit': 'N/A',
            'high_52w': 'N/A',
            'low_52w': 'N/A'
        }
        
        try:
            # 현재가 (today 또는 no_today 클래스 모두 확인)
            price_container = soup.find('div', class_=re.compile(r'(today|no_today)'))
            if price_container:
                blind = price_container.find('span', class_='blind')
                if blind:
                    result['current_price'] = blind.get_text(strip=True)
                else:
                    # blind가 없는 경우 직접 텍스트 추출 (드문 경우)
                    emp = price_container.find('em', class_='no_up') or price_container.find('em', class_='no_down')
                    if emp:
                        result['current_price'] = emp.get_text(strip=True)
            
            # blind 클래스에서 가격 정보 추출
            blind_dd = soup.find('dd', class_='blind')
            if blind_dd:
                text = blind_dd.get_text()
                
                # 전일종가
                prev_match = re.search(r'전일가\s*([\d,]+)', text)
                if prev_match:
                    result['prev_close'] = prev_match.group(1)
                
                # 시가
                open_match = re.search(r'시가\s*([\d,]+)', text)
                if open_match:
                    result['opening_price'] = open_match.group(1)
                
                # 고가
                high_match = re.search(r'고가\s*([\d,]+)', text)
                if high_match:
                    result['high_price'] = high_match.group(1)
                
                # 저가
                low_match = re.search(r'저가\s*([\d,]+)', text)
                if low_match:
                    result['low_price'] = low_match.group(1)
                
                # 상한가
                upper_match = re.search(r'상한가\s*([\d,]+)', text)
                if upper_match:
                    result['upper_limit'] = upper_match.group(1)
                
                # 하한가
                lower_match = re.search(r'하한가\s*([\d,]+)', text)
                if lower_match:
                    result['lower_limit'] = lower_match.group(1)
            
            # 52주 최고/최저
            all_elements = soup.find_all(['div', 'td', 'p', 'em'])
            for elem in all_elements:
                text = elem.get_text(strip=True)
                if '52주최고' in text and '최저' in text:
                    normalized = re.sub(r'\s+', ' ', text)
                    match = re.search(r'52주최고\s*[l|]\s*최저\s*([\d,]+)[l|]([\d,]+)', normalized)
                    if match:
                        result['high_52w'] = match.group(1)
                        result['low_52w'] = match.group(2)
                        break
        
        except Exception as e:
            print(f"[ERROR] Failed to extract price data: {e}")
        
        return result
    
    def extract_trading_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        거래 정보 추출
        
        Returns:
            {
                'volume': 거래량,
                'trading_value': 거래대금,
                'market_cap': 시가총액
            }
        """
        result = {
            'volume': 'N/A',
            'trading_value': 'N/A',
            'market_cap': 'N/A'
        }
        
        try:
            # blind 클래스에서 거래 정보 추출
            blind_dd = soup.find('dd', class_='blind')
            if blind_dd:
                text = blind_dd.get_text()
                
                # 거래량
                volume_match = re.search(r'거래량\s*([\d,]+)', text)
                if volume_match:
                    result['volume'] = volume_match.group(1)
                
                # 거래대금
                value_match = re.search(r'거래대금\s*([\d,]+)', text)
                if value_match:
                    result['trading_value'] = value_match.group(1)
            
            # 시가총액 (테이블에서 찾기)
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    if th and '시가총액' in th.get_text():
                        td = row.find('td')
                        if td:
                            # "123조" 또는 "1,234억" 형태로 추출
                            result['market_cap'] = td.get_text(strip=True)
                            break
        
        except Exception as e:
            print(f"[ERROR] Failed to extract trading data: {e}")
        
        return result
    
    def extract_valuation_metrics(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        투자 지표 추출
        
        Returns:
            {
                'per': PER (현재),
                'per_industry': PER (업종),
                'pbr': PBR (현재),
                'pbr_industry': PBR (업종),
                'eps': EPS,
                'bps': BPS,
                'dividend_yield': 배당수익률,
                'opinion_score': 투자의견 점수,
                'opinion': 투자의견,
                'target_price': 목표주가
            }
        """
        result = {
            'per': 'N/A',
            'per_industry': 'N/A',
            'pbr': 'N/A',
            'pbr_industry': 'N/A',
            'eps': 'N/A',
            'bps': 'N/A',
            'dividend_yield': 'N/A',
            'opinion_score': 'N/A',
            'opinion': 'N/A',
            'target_price': 'N/A'
        }
        
        try:
            # PER/PBR 테이블 찾기
            per_table = soup.find('table', summary=re.compile(r'PER.*EPS'))
            if per_table:
                rows = per_table.find_all('tr')
                for row in rows:
                    text = row.get_text(strip=True)
                    
                    # PER
                    if 'PER' in text and 'EPS' in text and '업종PER' not in text:
                        cells = row.find_all('td')
                        if cells:
                            per_text = cells[0].get_text(strip=True)
                            # "34.84배4,816원" 형태에서 분리
                            per_match = re.search(r'([\d.]+)배', per_text)
                            eps_match = re.search(r'([\d,]+)원', per_text)
                            if per_match:
                                result['per'] = per_match.group(1)
                            if eps_match:
                                result['eps'] = eps_match.group(1)
                    
                    # 업종 PER
                    if '업종PER' in text:
                        cells = row.find_all('td')
                        if cells:
                            per_text = cells[0].get_text(strip=True)
                            per_match = re.search(r'([\d.]+)배', per_text)
                            if per_match:
                                result['per_industry'] = per_match.group(1)
                    
                    # PBR
                    if 'PBR' in text and 'BPS' in text:
                        cells = row.find_all('td')
                        if cells:
                            pbr_text = cells[0].get_text(strip=True)
                            pbr_match = re.search(r'([\d.]+)배', pbr_text)
                            bps_match = re.search(r'([\d,]+)원', pbr_text)
                            if pbr_match:
                                result['pbr'] = pbr_match.group(1)
                            if bps_match:
                                result['bps'] = bps_match.group(1)
                    
                    # 배당수익률
                    if '배당' in text or '수익률' in text:
                        cells = row.find_all('td')
                        if cells:
                            div_text = cells[0].get_text(strip=True)
                            div_match = re.search(r'([\d.]+)%', div_text)
                            if div_match:
                                result['dividend_yield'] = div_match.group(1)
            
            # 투자의견 및 목표주가
            all_elements = soup.find_all(['div', 'td', 'p', 'em'])
            for elem in all_elements:
                text = elem.get_text(strip=True)
                if '투자의견' in text and '목표주가' in text:
                    normalized = re.sub(r'\s+', ' ', text)
                    #目标的正则优化: 쉼표 포함 숫자만 정확히 캡처하고 무의미한 텍스트 배제
                    match = re.search(
                        r'투자의견\s*[\d.가-힣]*\s*목표주가\s*([\d,]+)원?',
                        normalized
                    )
                    if match:
                        result['target_price'] = match.group(1)
                        # 점수와 의견은 별도로 재추출하여 정확도 향상
                        score_match = re.search(r'([\d.]+)\s*([가-힣]+)', normalized)
                        if score_match:
                            result['opinion_score'] = score_match.group(1)
                            result['opinion'] = score_match.group(2)
                        break
                    if match:
                        result['opinion_score'] = match.group(1)
                        result['opinion'] = match.group(2)
                        result['target_price'] = match.group(3)
                        break
        
        except Exception as e:
            print(f"[ERROR] Failed to extract valuation metrics: {e}")
        
        return result
    
    def extract_supply_demand(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        수급 정보 추출 (외국인/기관/개인 순매수)
        
        Returns:
            {
                'foreign_ownership': 외국인 보유비율,
                'foreign_net_buy': 외국인 순매수,
                'institutional_net_buy': 기관 순매수,
                'individual_net_buy': 개인 순매수
            }
        """
        result = {
            'foreign_ownership': 'N/A',
            'foreign_net_buy': 'N/A',
            'institutional_net_buy': 'N/A',
            'individual_net_buy': 'N/A'
        }
        
        try:
            # 외국인 보유비율 (테이블에서 찾기)
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    if th and '외국인' in th.get_text() and '보유' in th.get_text():
                        td = row.find('td')
                        if td:
                            result['foreign_ownership'] = td.get_text(strip=True)
                            break
            
            # 순매수 정보 (sub_section에서 찾기)
            sub_sections = soup.find_all('div', class_='sub_section')
            for section in sub_sections:
                text = section.get_text()
                
                # "외국인" 또는 "기관" 또는 "개인" 키워드가 있는 섹션 찾기
                if '외국인' in text or '기관' in text or '개인' in text:
                    # 테이블 형태로 되어 있을 가능성
                    table = section.find('table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            if len(cells) >= 2:
                                label = cells[0].get_text(strip=True)
                                value = cells[1].get_text(strip=True)
                                
                                if '외국인' in label:
                                    result['foreign_net_buy'] = value
                                elif '기관' in label:
                                    result['institutional_net_buy'] = value
                                elif '개인' in label:
                                    result['individual_net_buy'] = value
        
        except Exception as e:
            print(f"[ERROR] Failed to extract supply/demand data: {e}")
        
        return result
    
    def extract_financial_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        재무 정보 추출
        
        Returns:
            {
                'roe': ROE (자기자본이익률),
                'debt_ratio': 부채비율,
                'operating_margin': 영업이익률
            }
        """
        result = {
            'roe': 'N/A',
            'debt_ratio': 'N/A',
            'operating_margin': 'N/A'
        }
        
        try:
            # 재무 정보 테이블 찾기
            tables = soup.find_all('table')
            for table in tables:
                summary = table.get('summary', '')
                if '재무' in summary or '분석' in summary:
                    rows = table.find_all('tr')
                    for row in rows:
                        th = row.find('th')
                        if not th:
                            continue
                        
                        label = th.get_text(strip=True)
                        td = row.find('td')
                        
                        if td:
                            value = td.get_text(strip=True)
                            
                            if 'ROE' in label or '자기자본이익률' in label:
                                result['roe'] = value
                            elif '부채비율' in label:
                                result['debt_ratio'] = value
                            elif '영업이익률' in label:
                                result['operating_margin'] = value
        
        except Exception as e:
            print(f"[ERROR] Failed to extract financial data: {e}")
        
        return result
    
    def extract_sector(self, soup: BeautifulSoup) -> str:
        """업종 정보 추출"""
        try:
            sector_th = soup.find('th', string=re.compile(r'업종'))
            if sector_th:
                sector_td = sector_th.find_next('td')
                if sector_td:
                    return sector_td.get_text(strip=True)
            
            sector_h4 = soup.find('h4', string=re.compile(r'업종명'))
            if sector_h4:
                sector_a = sector_h4.find_next('a')
                if sector_a:
                    return sector_a.get_text(strip=True)
        except Exception as e:
            print(f"[ERROR] Failed to extract sector: {e}")
        
        return "N/A"
    
    def get_complete_trading_info(self, ticker: str) -> Dict[str, str]:
        """
        종목의 모든 트레이딩 정보를 한 번에 추출합니다.
        
        Args:
            ticker: 종목 코드
            
        Returns:
            모든 트레이딩 지표를 포함한 딕셔너리
        """
        soup = self.fetch_page(ticker)
        
        if not soup:
            return {'error': 'Failed to fetch page'}
        
        # 모든 정보 추출
        price_data = self.extract_price_data(soup)
        trading_data = self.extract_trading_data(soup)
        valuation_data = self.extract_valuation_metrics(soup)
        supply_demand_data = self.extract_supply_demand(soup)
        financial_data = self.extract_financial_data(soup)
        sector = self.extract_sector(soup)
        
        # 모든 데이터 병합
        complete_info = {
            **price_data,
            **trading_data,
            **valuation_data,
            **supply_demand_data,
            **financial_data,
            'sector': sector
        }
        
        return complete_info


# 테스트 코드
if __name__ == "__main__":
    scraper = TradingStrategyScraper()
    
    print("=" * 80)
    print("매매 전략용 스크래퍼 테스트: 삼성전자 (005930)")
    print("=" * 80)
    
    info = scraper.get_complete_trading_info("005930")
    
    print("\n[가격 정보]")
    print(f"  현재가: {info.get('current_price', 'N/A')}")
    print(f"  시가: {info.get('opening_price', 'N/A')}")
    print(f"  고가: {info.get('high_price', 'N/A')}")
    print(f"  저가: {info.get('low_price', 'N/A')}")
    print(f"  전일종가: {info.get('prev_close', 'N/A')}")
    print(f"  52주 최고/최저: {info.get('high_52w', 'N/A')} / {info.get('low_52w', 'N/A')}")
    
    print("\n[거래 정보]")
    print(f"  거래량: {info.get('volume', 'N/A')}")
    print(f"  거래대금: {info.get('trading_value', 'N/A')}")
    print(f"  시가총액: {info.get('market_cap', 'N/A')}")
    
    print("\n[투자 지표]")
    print(f"  PER: {info.get('per', 'N/A')} (업종: {info.get('per_industry', 'N/A')})")
    print(f"  PBR: {info.get('pbr', 'N/A')}")
    print(f"  EPS: {info.get('eps', 'N/A')}")
    print(f"  BPS: {info.get('bps', 'N/A')}")
    print(f"  배당수익률: {info.get('dividend_yield', 'N/A')}%")
    print(f"  투자의견: {info.get('opinion', 'N/A')} ({info.get('opinion_score', 'N/A')})")
    print(f"  목표주가: {info.get('target_price', 'N/A')}")
    
    print("\n[수급 정보]")
    print(f"  외국인 보유비율: {info.get('foreign_ownership', 'N/A')}")
    print(f"  외국인 순매수: {info.get('foreign_net_buy', 'N/A')}")
    print(f"  기관 순매수: {info.get('institutional_net_buy', 'N/A')}")
    print(f"  개인 순매수: {info.get('individual_net_buy', 'N/A')}")
    
    print("\n[재무 정보]")
    print(f"  ROE: {info.get('roe', 'N/A')}")
    print(f"  부채비율: {info.get('debt_ratio', 'N/A')}")
    print(f"  영업이익률: {info.get('operating_margin', 'N/A')}")
    
    print("\n[기타]")
    print(f"  업종: {info.get('sector', 'N/A')}")
    
    print("\n" + "=" * 80)
