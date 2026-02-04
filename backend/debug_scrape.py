import requests
from bs4 import BeautifulSoup
import re

def test_scrape(ticker):
    print(f"Testing scraper for ticker: {ticker}")
    url = f"https://finance.naver.com/item/main.nhn?code={ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        content = response.content.decode('euc-kr', errors='replace')
        print(f"Content length: {len(content)}")
        
        with open("debug_naver.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Raw HTML saved to debug_naver.html")

        soup = BeautifulSoup(content, 'html.parser')
        
        # 1. Flexible Invest Table Search
        print("\n--- Searching for Invest Table ---")
        all_tables = soup.find_all('table')
        print(f"Total tables found: {len(all_tables)}")
        for i, table in enumerate(all_tables):
            summary = table.get('summary', '')
            if '투자의견' in summary:
                print(f"Table index {i} matches summary: {summary}")
                em_tags = table.find_all('em')
                print(f"EM tags values: {[em.get_text(strip=True) for em in em_tags]}")

        # 2. Flexible Price Search
        print("\n--- Searching for Current Price ---")
        today_div = soup.find('div', class_='no_today')
        if today_div:
            print(f"Found no_today div. Text: {today_div.get_text(strip=True)}")
        
        price_text = re.search(r'현재가.*?([0-9,]+)', content)
        if price_text:
            print(f"Regex '현재가' match: {price_text.group(0)}")

        # 3. Sector
        print("\n--- Searching for Sector ---")
        sector_th = soup.find('th', string=re.compile(r'업종'))
        if sector_th:
             print(f"Found '업종' th. TD: {sector_th.find_next('td').get_text(strip=True)}")

    except Exception as e:
        print(f"Scrape error: {e}")

if __name__ == "__main__":
    test_scrape("005930")
