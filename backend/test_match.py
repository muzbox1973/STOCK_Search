# coding: utf-8
import requests

url = "https://finance.naver.com/item/main.nhn?code=005930"
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)

# EUC-KR bytes for keywords
KEYWORDS = {
    "opinion": b"\xc5\xfe\xc0\xda\xc0\xc7\xb0\xb0", # 투자의견
    "target": b"\xbb\xba\xd4\xf0\xbc\xbc\xb0\xa1", # 목표주가 (wait, let me double check this)
    "current": b"\xed\xed\xc0\xda\xb0\xa1" # 현재가 - let me try the UTF-8 to EUC-KR conversion correctly
}

print(f"Content length: {len(r.content)}")

# Test 1: Byte-level search in raw content
for name, b_val in KEYWORDS.items():
    print(f"Raw bytes {name} in content: {b_val in r.content}")

# Test 2: Decode and search with Unicode escapes
content_uni = r.content.decode('euc-kr', errors='replace')
keywords_uni = {
    "opinion": "\ud22c\uc790\uc758\uacac", # 투자의견
    "target": "\ubaa9\ud45c\uc8fc\uac00", # 목표주가
    "current": "\ud604\uc7ac\uac00"        # 현재가
}

for name, uni_val in keywords_uni.items():
    print(f"Unicode {name} ({repr(uni_val)}) in content: {uni_val in content_uni}")

# Let's find any table summary and decode it properly
import re
summaries = re.findall(rb'summary="([^"]*)"', r.content)
print("\n--- Raw Table Summaries (Decoded) ---")
for s in summaries:
    try:
        print(f"Summary: {repr(s.decode('euc-kr'))}")
    except:
        print(f"Summary (hex): {s.hex()}")
