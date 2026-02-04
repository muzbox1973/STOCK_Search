import re
from bs4 import BeautifulSoup

with open("debug_naver.html", "r", encoding="utf-8") as f:
    content = f.read()

with open("find_results.txt", "w", encoding="utf-8") as out:
    out.write(f"File length: {len(content)}\n")

    soup = BeautifulSoup(content, 'html.parser')

    # Search for tables
    out.write("\n--- All Tables Analysis ---\n")
    all_tables = soup.find_all('table')
    for i, table in enumerate(all_tables):
        summary = table.get('summary', 'NO SUMMARY')
        text = table.get_text(strip=True)[:100]
        out.write(f"Table {i} | Summary: {repr(summary)} | Text: {repr(text)}\n")
        em_tags = table.find_all('em')
        if em_tags:
            out.write(f"  EM Tags: {[em.get_text(strip=True) for em in em_tags]}\n")

    # Find total em tags
    out.write(f"\nTotal EM tags found: {len(soup.find_all('em'))}\n")

print("Results written to find_results.txt")
