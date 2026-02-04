"""
AI 기반 종합 주식 분석 시스템

전체 종목 리스트를 가져와서 스크래핑하고,
AI 기반 투자 공략 정보를 제공합니다.
"""

from naver_scraper_trading import TradingStrategyScraper
from pykrx import stock
import pandas as pd
from datetime import datetime
from typing import List, Dict
import time


class StockAnalysisSystem:
    """AI 기반 종합 주식 분석 시스템"""
    
    def __init__(self):
        self.scraper = TradingStrategyScraper()
        self.stocks_data = []
    
    def get_all_stocks(self) -> List[Dict]:
        """
        KOSPI와 KOSDAQ의 모든 종목 리스트를 가져옵니다.
        
        Returns:
            [{'ticker': '005930', 'name': '삼성전자', 'market': 'KOSPI'}, ...]
        """
        print("\n[1/4] 전체 종목 리스트 가져오는 중...")
        
        stocks = []
        
        # KOSPI 종목
        kospi_tickers = stock.get_market_ticker_list(market="KOSPI")
        for ticker in kospi_tickers:
            stocks.append({
                'ticker': ticker,
                'name': stock.get_market_ticker_name(ticker),
                'market': 'KOSPI'
            })
        
        # KOSDAQ 종목
        kosdaq_tickers = stock.get_market_ticker_list(market="KOSDAQ")
        for ticker in kosdaq_tickers:
            stocks.append({
                'ticker': ticker,
                'name': stock.get_market_ticker_name(ticker),
                'market': 'KOSDAQ'
            })
        
        print(f"   총 {len(stocks)}개 종목 (KOSPI: {len(kospi_tickers)}, KOSDAQ: {len(kosdaq_tickers)})")
        
        return stocks
    
    def scrape_stock(self, ticker: str, name: str) -> Dict:
        """
        개별 종목 스크래핑
        
        Args:
            ticker: 종목 코드
            name: 종목명
            
        Returns:
            스크래핑된 데이터
        """
        try:
            data = self.scraper.get_complete_trading_info(ticker)
            data['ticker'] = ticker
            data['name'] = name
            data['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return data
        except Exception as e:
            print(f"   오류 ({ticker} {name}): {e}")
            return {
                'ticker': ticker,
                'name': name,
                'error': str(e),
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def scrape_all_stocks(self, stocks: List[Dict], limit: int = None) -> List[Dict]:
        """
        전체 종목 일괄 스크래핑
        
        Args:
            stocks: 종목 리스트
            limit: 제한 개수 (테스트용, None이면 전체)
            
        Returns:
            스크래핑된 데이터 리스트
        """
        print(f"\n[2/4] 종목 스크래핑 중...")
        
        if limit:
            stocks = stocks[:limit]
            print(f"   테스트 모드: {limit}개 종목만 스크래핑")
        
        results = []
        total = len(stocks)
        
        for i, stock_info in enumerate(stocks, 1):
            ticker = stock_info['ticker']
            name = stock_info['name']
            market = stock_info['market']
            
            print(f"   [{i}/{total}] {name} ({ticker}) - {market}")
            
            data = self.scrape_stock(ticker, name)
            data['market'] = market
            results.append(data)
            
            # 과도한 요청 방지 (1초 대기)
            if i < total:
                time.sleep(1)
        
        self.stocks_data = results
        return results
    
    def analyze_stock_ai(self, data: Dict) -> Dict:
        """
        AI 기반 투자 공략 분석
        
        Args:
            data: 종목 데이터
            
        Returns:
            {
                'score': 종합 점수 (0-100),
                'grade': 등급 (S/A/B/C/D),
                'signals': 투자 시그널 리스트,
                'recommendation': 투자 추천,
                'strategy': 추천 전략
            }
        """
        signals = []
        score = 50  # 기본 점수
        
        try:
            # 1. 가치투자 분석
            per = float(data.get('per', '999').replace(',', ''))
            pbr = float(data.get('pbr', '999').replace(',', ''))
            
            if per < 10:
                signals.append("✓ 매우 낮은 PER - 저평가")
                score += 15
            elif per < 15:
                signals.append("✓ 낮은 PER - 적정 가치")
                score += 10
            elif per > 30:
                signals.append("⚠ 높은 PER - 고평가 가능")
                score -= 10
            
            if pbr < 1:
                signals.append("✓ PBR < 1 - 청산가치 이하")
                score += 15
            elif pbr < 2:
                signals.append("✓ 낮은 PBR - 저평가")
                score += 10
            
            # 2. 재무 건전성 분석
            roe = float(data.get('roe', '0').replace(',', ''))
            debt_ratio = float(data.get('debt_ratio', '100').replace(',', ''))
            
            if roe > 15:
                signals.append("✓ 높은 ROE - 우수한 수익성")
                score += 15
            elif roe > 10:
                signals.append("✓ 양호한 ROE")
                score += 10
            elif roe < 5:
                signals.append("⚠ 낮은 ROE - 수익성 부족")
                score -= 10
            
            if debt_ratio < 50:
                signals.append("✓ 낮은 부채비율 - 재무 안정")
                score += 10
            elif debt_ratio > 100:
                signals.append("⚠ 높은 부채비율 - 재무 리스크")
                score -= 10
            
            # 3. 모멘텀 분석
            current = float(data.get('current_price', '0').replace(',', ''))
            high_52w = float(data.get('high_52w', '0').replace(',', ''))
            low_52w = float(data.get('low_52w', '0').replace(',', ''))
            
            if current > 0 and high_52w > 0:
                price_position = (current - low_52w) / (high_52w - low_52w) * 100
                
                if price_position > 80:
                    signals.append("⚠ 52주 고점 근처 - 조정 가능")
                    score -= 5
                elif price_position < 20:
                    signals.append("✓ 52주 저점 근처 - 반등 기대")
                    score += 10
            
            # 4. 투자의견 분석
            opinion = data.get('opinion', 'N/A')
            opinion_score_val = float(data.get('opinion_score', '3').replace(',', ''))
            
            if opinion_score_val <= 2:
                signals.append("✓ 증권사 강력 매수 의견")
                score += 10
            elif opinion_score_val <= 2.5:
                signals.append("✓ 증권사 매수 의견")
                score += 5
            
            # 5. 배당 분석
            dividend = float(data.get('dividend_yield', '0').replace(',', ''))
            if dividend > 3:
                signals.append("✓ 높은 배당수익률")
                score += 5
            
        except Exception as e:
            signals.append(f"분석 오류: {e}")
        
        # 점수 범위 제한 (0-100)
        score = max(0, min(100, score))
        
        # 등급 결정
        if score >= 80:
            grade = 'S'
            recommendation = '강력 매수'
            strategy = '적극적 매수 포지션 구축'
        elif score >= 70:
            grade = 'A'
            recommendation = '매수'
            strategy = '분할 매수 추천'
        elif score >= 60:
            grade = 'B'
            recommendation = '보유'
            strategy = '관망 또는 소량 매수'
        elif score >= 50:
            grade = 'C'
            recommendation = '중립'
            strategy = '추가 분석 필요'
        else:
            grade = 'D'
            recommendation = '매도 검토'
            strategy = '리스크 관리 필요'
        
        return {
            'score': score,
            'grade': grade,
            'signals': signals,
            'recommendation': recommendation,
            'strategy': strategy
        }
    
    def analyze_all_stocks(self) -> List[Dict]:
        """
        전체 종목 AI 분석
        
        Returns:
            분석 결과 리스트
        """
        print(f"\n[3/4] AI 투자 분석 중...")
        
        analyzed = []
        total = len(self.stocks_data)
        
        for i, data in enumerate(self.stocks_data, 1):
            if 'error' in data:
                continue
            
            ticker = data.get('ticker', 'N/A')
            name = data.get('name', 'N/A')
            
            print(f"   [{i}/{total}] {name} ({ticker}) 분석 중...")
            
            ai_analysis = self.analyze_stock_ai(data)
            
            # 데이터와 분석 결과 병합
            analyzed_data = {**data, **ai_analysis}
            analyzed.append(analyzed_data)
        
        # 점수 순으로 정렬
        analyzed.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return analyzed
    
    def save_to_excel(self, analyzed_data: List[Dict], filename: str = None):
        """
        분석 결과를 Excel 파일로 저장
        
        Args:
            analyzed_data: 분석된 데이터
            filename: 파일명 (None이면 자동 생성)
        """
        print(f"\n[4/4] Excel 파일로 저장 중...")
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'stock_analysis_{timestamp}.xlsx'
        
        # DataFrame 생성
        df = pd.DataFrame(analyzed_data)
        
        # 주요 컬럼 순서 정렬
        columns_order = [
            'grade', 'score', 'recommendation', 'ticker', 'name', 'market',
            'current_price', 'per', 'pbr', 'roe', 'debt_ratio',
            'opinion', 'opinion_score', 'target_price',
            'high_52w', 'low_52w', 'market_cap', 'volume',
            'dividend_yield', 'sector', 'strategy', 'signals'
        ]
        
        # 존재하는 컬럼만 선택
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        
        # Excel 저장
        df.to_excel(filename, index=False, sheet_name='AI Stock Analysis')
        
        print(f"   저장 완료: {filename}")
        print(f"   총 {len(df)}개 종목 분석 완료")
        
        return filename
    
    def run_full_analysis(self, limit: int = None):
        """
        전체 분석 프로세스 실행
        
        Args:
            limit: 종목 제한 개수 (테스트용)
        """
        print("\n" + "="*80)
        print("AI 기반 종합 주식 분석 시스템")
        print("="*80)
        
        # 1. 전체 종목 리스트 가져오기
        stocks = self.get_all_stocks()
        
        # 2. 전체 종목 스크래핑
        scraped = self.scrape_all_stocks(stocks, limit=limit)
        
        # 3. AI 분석
        analyzed = self.analyze_all_stocks()
        
        # 4. Excel 저장
        filename = self.save_to_excel(analyzed)
        
        # 5. 상위 10개 종목 출력
        print(f"\n{'='*80}")
        print("TOP 10 추천 종목")
        print(f"{'='*80}")
        
        for i, stock in enumerate(analyzed[:10], 1):
            print(f"\n{i}. [{stock['grade']}] {stock['name']} ({stock['ticker']}) - {stock['market']}")
            print(f"   점수: {stock['score']}/100")
            print(f"   추천: {stock['recommendation']} | 전략: {stock['strategy']}")
            print(f"   현재가: {stock.get('current_price', 'N/A')} | PER: {stock.get('per', 'N/A')} | PBR: {stock.get('pbr', 'N/A')}")
            print(f"   ROE: {stock.get('roe', 'N/A')}% | 목표가: {stock.get('target_price', 'N/A')}")
            if stock.get('signals'):
                print(f"   시그널: {', '.join(stock['signals'][:3])}")
        
        print(f"\n{'='*80}")
        print(f"분석 완료! 결과 파일: {filename}")
        print(f"{'='*80}\n")
        
        return analyzed, filename


if __name__ == "__main__":
    # 시스템 초기화
    system = StockAnalysisSystem()
    
    # 테스트: 10개 종목만 분석
    print("테스트 모드: 10개 종목만 분석합니다.")
    analyzed, filename = system.run_full_analysis(limit=10)
    
    # 전체 분석을 원하면:
    # analyzed, filename = system.run_full_analysis()
