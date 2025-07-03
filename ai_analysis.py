#!/usr/bin/env python3
"""
ScryptBot: AI Analysis Module
Performs headline analysis for ScryptBot using GPT.
(C) 2024-present ScryptBot Team
"""
import os
import openai
from dotenv import load_dotenv
import json

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

MODEL = "gpt-3.5-turbo"

PROMPT_TEMPLATE = '''
You are a financial news analyst AI. Given the following news headline, analyze it and provide:
- A one-sentence summary
- The overall sentiment (positive, negative, or neutral)
- The most relevant financial instrument (provide the actual ticker symbol, e.g., TSLA, AAPL, SPY, not just 'stock' or 'equity')
- A suggested action (buy, sell, hold, ignore)
- A brief rationale for your suggestion (keep it to a single, concise sentence, max 100 characters)
- Estimate the expected price impact as a percentage (e.g., +2%, -1%, 0%) and include it in your JSON output as expected_impact.

Headline: "{headline}"

Respond in JSON with keys: summary, sentiment, instrument, action, rationale, expected_impact.
'''

def analyze_financial_news(headline: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(headline=headline)
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )
        content = response.choices[0].message.content
        if not content:
            return {"error": "No content returned from AI"}
        # Try to parse the response as JSON
        try:
            result = json.loads(content)
            return result
        except Exception:
            # If not valid JSON, return as text
            return {"error": "Invalid JSON from AI", "raw": content}
    except Exception as e:
        return {"error": str(e)} 