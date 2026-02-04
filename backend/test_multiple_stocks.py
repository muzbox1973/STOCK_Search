"""
여러 종목 테스트 스크립트
"""

from naver_scraper_trading import TradingStrategyScraper
import time


def test_multiple_stocks():
    scraper = TradingStrategyScraper()
    
    # 테스트할 종목들
    stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
    ]
    
    print("\n" + "=" * 80)
    print("매매 전략용 스크래퍼 - 여러 종목 테스트")
    print("=" * 80)
    
    for ticker, name in stocks:
        print(f"\n{'='*80}")
        print(f"{name} ({ticker})")
        print(f"{'='*80}")
        
        info = scraper.get_complete_trading_info(ticker)
        
        if 'error' in info:
            print(f"❌ 오류: {info['error']}")
            continue
        
        # 핵심 지표만 출력
        print(f"\n[가격] 현재가: {info.get('current_price', 'N/A')}")
        print(f"[거래] 시가총액: {info.get('market_cap', 'N/A')}")
        print(f"[지표] PER: {info.get('per', 'N/A')} | PBR: {info.get('pbr', 'N/A')}")
        print(f"[재무] ROE: {info.get('roe', 'N/A')}% | 부채비율: {info.get('debt_ratio', 'N/A')}%")
        print(f"[의견] 투자의견: {info.get('opinion', 'N/A')} ({info.get('opinion_score', 'N/A')})")
        print(f"[목표] 목표주가: {info.get('target_price', 'N/A')}")
        print(f"[범위] 52주: {info.get('low_52w', 'N/A')} ~ {info.get('high_52w', 'N/A')}")
        
        # 간단한 투자 시그널
        try:
            per = float(info.get('per', '999').replace(',', ''))
            pbr = float(info.get('pbr', '999').replace(',', ''))
            roe = float(info.get('roe', '0').replace(',', ''))
            
            print(f"\n[시그널] 투자 시그널:")
            if per < 15:
                print(f"  OK 낮은 PER ({per}) - 저평가 가능성")
            if pbr < 2:
                print(f"  OK 낮은 PBR ({pbr}) - 저평가 가능성")
            if roe > 10:
                print(f"  OK 높은 ROE ({roe}%) - 수익성 양호")
        except:
            pass
    
    print(f"\n{'='*80}")
    print("[완료] 모든 종목 테스트 완료!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_multiple_stocks()
