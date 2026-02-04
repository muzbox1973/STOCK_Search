# Naver Finance Scraper 사용 가이드

## 개요

`naver_scraper_enhanced.py`는 네이버 금융 페이지에서 주식 정보를 추출하는 강화된 스크래퍼 모듈입니다.

## 주요 기능

### 1. 현재가 추출 (`extract_current_price`)

**추출 위치:**
- **방법 1**: 상단 시세 영역의 `div.no_today > span.blind`
- **방법 2**: 동종업종비교 테이블의 첫 번째 데이터 행

**예시:**
```python
scraper = NaverFinanceScraper()
soup = scraper.fetch_page("005930")
current_price = scraper.extract_current_price(soup)
# 결과: "52500"
```

### 2. 투자의견 추출 (`extract_investment_opinion`)

**추출 패턴:**
```
투자의견 l 목표주가 4.00매수 l214,125
```

**추출 데이터:**
- `opinion_score`: "4.00" (투자의견 점수)
- `opinion_text`: "매수" (투자의견 텍스트)
- `target_price`: "214,125" (목표주가)

**정규식 패턴:**
```python
r'투자의견\s*[l|]\s*목표주가\s*([\d.]+)\s*([가-힣]+)\s*[l|]\s*([\d,]+)'
```

**예시:**
```python
opinion_data = scraper.extract_investment_opinion(soup)
# 결과: {
#   'opinion_score': '4.00',
#   'opinion_text': '매수',
#   'target_price': '214,125'
# }
```

### 3. 목표주가 추출

목표주가는 투자의견 추출 함수에서 함께 반환됩니다.

```python
target_price = opinion_data['target_price']  # "214,125"
```

### 4. 52주 최고/최저가 추출 (`extract_52week_range`)

**추출 패턴:**
```
52주최고 l 최저 168,500l52,500
```

**정규식 패턴:**
```python
r'52주최고\s*[l|]\s*최저\s*([\d,]+)[l|]([\d,]+)'
```

**예시:**
```python
week_52_data = scraper.extract_52week_range(soup)
# 결과: {
#   'high_52w': '168,500',
#   'low_52w': '52,500'
# }
```

### 5. 업종 추출 (`extract_sector`)

**추출 위치:**
- **방법 1**: `<th>업종</th>` 다음의 `<td>` 태그
- **방법 2**: `<h4>업종명</h4>` 다음의 `<a>` 태그

**예시:**
```python
sector = scraper.extract_sector(soup)
# 결과: "전기전자"
```

## 사용 방법

### 기본 사용법

```python
from naver_scraper_enhanced import NaverFinanceScraper

# 스크래퍼 인스턴스 생성
scraper = NaverFinanceScraper()

# 종목 정보 한 번에 가져오기
info = scraper.get_stock_info("005930")  # 삼성전자

print(info)
# 출력:
# {
#     'current_price': '52500',
#     'opinion_score': '4.00',
#     'opinion': '매수',
#     'target_price': '214,125',
#     'high_52w': '168,500',
#     'low_52w': '52,500',
#     'sector': '전기전자'
# }
```

### 개별 함수 사용

```python
# 페이지 가져오기
soup = scraper.fetch_page("005930")

# 개별 정보 추출
current_price = scraper.extract_current_price(soup)
opinion_data = scraper.extract_investment_opinion(soup)
week_52_data = scraper.extract_52week_range(soup)
sector = scraper.extract_sector(soup)
```

### FastAPI 엔드포인트에 통합

```python
from fastapi import FastAPI
from naver_scraper_enhanced import NaverFinanceScraper

app = FastAPI()
scraper = NaverFinanceScraper()

@app.get("/api/analyze/{ticker}")
def analyze_stock(ticker: str):
    return scraper.get_stock_info(ticker)
```

## 기존 코드와의 비교

### 기존 코드 (main.py)
- `<em>` 태그 기반 파싱
- VB 스타일의 문자열 분할
- 특정 테이블 구조에 의존

### 새로운 코드 (naver_scraper_enhanced.py)
- 정규식 기반 패턴 매칭
- 여러 추출 방법 제공 (fallback 지원)
- 더 명확한 함수 분리
- 한글 주석 및 문서화

## 테스트

```bash
cd c:\Users\muzbo\Downloads\2026\0109\supertonic_app\stock_app\backend
python naver_scraper_enhanced.py
```

## 주의사항

1. **DOM 구조 변경**: 네이버 금융 페이지의 DOM 구조가 변경되면 스크래퍼가 작동하지 않을 수 있습니다.
2. **요청 제한**: 과도한 요청은 IP 차단을 유발할 수 있으므로 적절한 딜레이를 추가하세요.
3. **인코딩**: UTF-8과 EUC-KR 인코딩을 모두 지원하지만, 특수 문자가 깨질 수 있습니다.

## 개선 가능한 부분

1. **캐싱**: 동일한 종목에 대한 반복 요청 방지
2. **비동기 처리**: `aiohttp`를 사용한 비동기 요청
3. **에러 핸들링**: 더 세밀한 예외 처리 및 로깅
4. **Rate Limiting**: 요청 속도 제한 구현
5. **데이터 검증**: 추출된 데이터의 유효성 검증

## 라이선스

이 코드는 교육 및 개인 프로젝트 목적으로 사용할 수 있습니다.
