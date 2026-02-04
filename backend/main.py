from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pykrx import stock
import pandas as pd
import io
import requests
from bs4 import BeautifulSoup
import re
from naver_scraper_trading import TradingStrategyScraper
from gemini_analyzer import GeminiAnalyzer
from fastapi import Header
from typing import Optional

app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/stocks")
def get_stocks():
    """
    Fetches the latest tickers and names for KOSPI and KOSDAQ.
    """
    try:
        kospi_tickers = stock.get_market_ticker_list(market="KOSPI")
        kosdaq_tickers = stock.get_market_ticker_list(market="KOSDAQ")
        
        data = []
        for ticker in kospi_tickers:
            data.append({
                "ticker": ticker,
                "name": stock.get_market_ticker_name(ticker),
                "market": "KOSPI"
            })
        for ticker in kosdaq_tickers:
            data.append({
                "ticker": ticker,
                "name": stock.get_market_ticker_name(ticker),
                "market": "KOSDAQ"
            })
        
        return data
    except Exception as e:
        return {"error": str(e)}

def clean_vb_text(text):
    """
    Equivalent to VB's getEMtext/Clean/Replace logic.
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # VBA Clean: removes non-printable characters
    text = "".join(ch for ch in text if ch.isprintable())
    # Remove commas from numbers
    return text.strip()

@app.get("/api/analyze/{ticker}")
def analyze_stock(ticker: str):
    """
    Scrapes detailed stock info from Naver Finance using the exact string-splitting logic from VB.
    """
    print(f"\n[DEBUG] Starting analysis for: {ticker}", flush=True)
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        print(f"[DEBUG] Fetching URL: {url}", flush=True)
        response = requests.get(url, headers=headers, timeout=10)
        
        # Naver seems to be returning UTF-8 now in many cases
        try:
            content = response.content.decode('utf-8')
            print("[DEBUG] Decoded using UTF-8")
        except:
            content = response.content.decode('euc-kr', errors='replace')
            print("[DEBUG] Decoded using EUC-KR (fallback)")

        print(f"[DEBUG] Content length: {len(content)}")
        # print(f"[DEBUG] Content snippet: {repr(content[:500])}")
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Initialize result with defaults
        result = {
            "opinion": "N/A",
            "opinion_score": "N/A",
            "target_price": "N/S",
            "high_52w": "N/A",
            "low_52w": "N/A",
            "current_price": "N/A",
            "sector": "N/A"
        }

        # 1. VB Logic: Find table by summary="투자의견"
        invest_table = None
        all_tables = soup.find_all('table')
        print(f"[DEBUG] Found {len(all_tables)} tables total.")
        for table in all_tables:
            summary = table.get('summary', '')
            # Match "투자의견", "목표주가", or the specific summary from our findings
            if "투자의견" in summary or "목표주가" in table.get_text():
                invest_table = table
                break
        
        if invest_table:
            print(f"[DEBUG] Found Invest Table with summary: {repr(invest_table.get('summary'))}")
            table_html = str(invest_table)
            chunks = table_html.split("<em>")[1:] 
            
            cleaned_vals = [clean_vb_text(chunk[:30]).replace(',', '') for chunk in chunks]
            print(f"[DEBUG] VB-style cleaned values: {cleaned_vals}")

            if len(cleaned_vals) >= 4:
                result["opinion_score"] = cleaned_vals[0]
                full_val0 = clean_vb_text(chunks[0][:20])
                opinion_match = re.search(r'([가-힣]+)', full_val0)
                if opinion_match: result["opinion"] = opinion_match.group(1)
                
                if len(cleaned_vals) >= 2: result["target_price"] = f"{int(cleaned_vals[1]):,}" if cleaned_vals[1].isdigit() else cleaned_vals[1]
                if len(cleaned_vals) >= 3: result["high_52w"] = f"{int(cleaned_vals[2]):,}" if cleaned_vals[2].isdigit() else cleaned_vals[2]
                if len(cleaned_vals) >= 4: result["low_52w"] = f"{int(cleaned_vals[3]):,}" if cleaned_vals[3].isdigit() else cleaned_vals[3]
            elif len(cleaned_vals) >= 2:
                result.update({
                    "high_52w": f"{int(cleaned_vals[0]):,}" if cleaned_vals[0].isdigit() else cleaned_vals[0],
                    "low_52w": f"{int(cleaned_vals[1]):,}" if cleaned_vals[1].isdigit() else cleaned_vals[1]
                })

        # 2. Extract Current Price
        today_div = soup.find('div', class_='no_today')
        if today_div:
            blind = today_div.find('span', class_='blind')
            if blind:
                result["current_price"] = blind.get_text(strip=True)
                print(f"[DEBUG] Found current price: {result['current_price']}")

        # 3. Sector
        sector_th = soup.find('th', string=re.compile(r'업종'))
        if sector_th:
            result["sector"] = sector_th.find_next('td').get_text(strip=True)
            print(f"[DEBUG] Found sector: {result['sector']}")
        else:
            sector_h4 = soup.find('h4', string=re.compile(r'업종명'))
            if sector_h4:
                result["sector"] = sector_h4.find_next('a').get_text(strip=True)
                print(f"[DEBUG] Found sector (h4): {result['sector']}")

        print(f"[DEBUG] Final Result for {ticker}: {result}\n", flush=True)
        return result
    except Exception as e:
        print(f"[DEBUG] Error for {ticker}: {e}")
        return {"error": str(e)}

# 매매 전략용 스크래퍼 인스턴스
trading_scraper = TradingStrategyScraper()

@app.get("/api/trading-analysis/{ticker}")
def trading_analysis(ticker: str):
    """
    매매 전략 수립을 위한 종합 분석 정보를 제공합니다.
    가격, 거래, 투자지표, 수급, 재무 정보를 모두 포함합니다.
    """
    print(f"\n[DEBUG] Trading analysis for: {ticker}", flush=True)
    try:
        result = trading_scraper.get_complete_trading_info(ticker)
        print(f"[DEBUG] Trading analysis result: {result}\n", flush=True)
        return result
    except Exception as e:
        print(f"[DEBUG] Error in trading analysis for {ticker}: {e}")
        return {"error": str(e)}

@app.get("/api/gemini-test")
def test_gemini_connection(x_gemini_api_key: Optional[str] = Header(None)):
    """Gemini API 키 연결 테스트"""
    if not x_gemini_api_key:
        return {"error": "API Key is missing"}
    
    analyzer = GeminiAnalyzer(x_gemini_api_key)
    success = analyzer.test_connection()
    return {"success": success}

@app.post("/api/gemini-analyze/{ticker}")
def gemini_analyze(ticker: str, stock_data: dict, x_gemini_api_key: Optional[str] = Header(None)):
    """Gemini AI를 이용한 종목 전략 분석"""
    if not x_gemini_api_key:
        return {"error": "API Key is missing"}
    
    analyzer = GeminiAnalyzer(x_gemini_api_key)
    analysis = analyzer.get_strategy(stock_data)
    return analysis

from pydantic import BaseModel
from typing import List, Dict, Optional

class StockItem(BaseModel):
    ticker: str
    name: str
    market: str

class AnalysisData(BaseModel):
    opinion: Optional[str] = "N/A"
    opinion_score: Optional[str] = "N/A"
    target_price: Optional[str] = "N/S"
    high_52w: Optional[str] = "N/A"
    low_52w: Optional[str] = "N/A"
    current_price: Optional[str] = "N/A"
    sector: Optional[str] = "N/A"

class ExportRequest(BaseModel):
    stocks: List[StockItem]
    analysis: Dict[str, AnalysisData]

@app.post("/api/export")
def export_stocks(request: ExportRequest):
    """
    Generates and returns an Excel file of stocks including analysis data.
    """
    try:
        rows = []
        for s in request.stocks:
            a = request.analysis.get(s.ticker)
            row = {
                "종목코드": s.ticker,
                "종목명": s.name,
                "현재가": a.current_price if a else "-",
                "투자의견": f"{a.opinion} ({a.opinion_score})" if a and a.opinion != "N/A" else "-",
                "목표주가": a.target_price if a else "-",
                "52주 최고": a.high_52w if a else "-",
                "52주 최저": a.low_52w if a else "-",
                "업종": a.sector if a else "-",
                "시장": s.market
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Stock Analysis')
        
        headers = {
            'Content-Disposition': 'attachment; filename="stock_analysis.xlsx"'
        }
        return Response(
            content=output.getvalue(), 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            headers=headers
        )
    except Exception as e:
        print(f"Export error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
