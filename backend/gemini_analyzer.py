import google.generativeai as genai
import json

class GeminiAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def test_connection(self):
        """테스트를 위해 간단한 요청을 보냅니다."""
        try:
            response = self.model.generate_content("Hello")
            return True if response.text else False
        except Exception as e:
            print(f"[ERROR] Gemini API Test failed: {e}")
            return False

    def get_strategy(self, stock_info: dict):
        """종목 정보를 바탕으로 매매 전략과 솔루션을 제안합니다."""
        prompt = f"""
        당신은 전문 주식 분석가입니다. 다음 주식 데이터를 분석하여 투자자에게 도움이 되는 매매 전략과 솔루션을 제안해주세요.

        [주식 정보]
        종목명: {stock_info.get('name')} ({stock_info.get('ticker')})
        현재가: {stock_info.get('current_price')}
        PER: {stock_info.get('per')} (업종: {stock_info.get('per_industry')})
        PBR: {stock_info.get('pbr')}
        ROE: {stock_info.get('roe')}%
        부채비율: {stock_info.get('debt_ratio')}%
        투자의견: {stock_info.get('opinion')} (목표가: {stock_info.get('target_price')})
        52주 최고/최저: {stock_info.get('high_52w')} / {stock_info.get('low_52w')}
        시가총액: {stock_info.get('market_cap')}
        업종: {stock_info.get('sector')}

        위 데이터를 바탕으로 다음 형식의 JSON으로만 답변해주세요:
        {{
            "strategic_recommendation": "현재 상황에 대한 핵심 요약 및 매매 권고 (예: 분할 매수, 관망, 매도 등)",
            "strategic_solution": "구체적인 대응 전략 (예: 손절가, 익절가 제안 또는 리스크 관리 방법)"
        }}
        답변은 반드시 한국어로 작성해주세요.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # JSON만 추출하기 위해 간단한 파싱 시도
            content = response.text.strip()
            # 마크다운 블록 제거
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"[ERROR] Gemini Analysis failed: {e}")
            return {
                "strategic_recommendation": "분석 오류가 발생했습니다.",
                "strategic_solution": "API 키를 확인하거나 나중에 다시 시도해주세요."
            }
