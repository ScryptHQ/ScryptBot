#!/usr/bin/env python3
"""
ScryptBot: Ticker Extraction Utility
Extracts ticker symbols from text for ScryptBot analysis and posting.
(C) 2024-present ScryptBot Team
"""
import os
import re

# Load tickers from file (one per line)
TICKER_FILE = 'tickers.txt'

def load_ticker_set():
    tickers = set()
    if os.path.exists(TICKER_FILE):
        with open(TICKER_FILE, 'r') as f:
            for line in f:
                t = line.strip().upper()
                if t:
                    tickers.add(t)
    # Add major indices, ETFs, FX pairs, and cryptos
    tickers.update({
        'SPY', 'DIA', 'QQQ', 'IWM', 'VTI', 'VOO', 'IVV', 'S&P500', 'DJIA', 'NASDAQ',
        'EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD',
        'BTC', 'ETH', 'BTCUSD', 'ETHUSD', 'SOL', 'ADA', 'XRP', 'DOGE', 'BNB',
    })
    return tickers

TICKER_SET = load_ticker_set()

# Regex for $TICKER or plain TICKER
TICKER_PATTERN = re.compile(r'(\$?[A-Z]{2,6})')

# Also match index/ETF names in text
INDEX_NAMES = [
    'S&P 500', 'Dow', 'Nasdaq', 'Russell 2000', 'FTSE', 'DAX', 'Nikkei',
    'SPY', 'QQQ', 'DIA', 'IWM', 'VTI', 'VOO', 'IVV'
]

# Map index names to tickers
INDEX_MAP = {
    'S&P 500': 'SPY',
    'Dow': 'DIA',
    'Nasdaq': 'QQQ',
    'Russell 2000': 'IWM',
    'FTSE': 'FTSE',
    'DAX': 'DAX',
    'Nikkei': 'NIKKEI',
}

def extract_tickers_from_text(text):
    found = set()
    text_up = text.upper()
    # Find $TICKER or TICKER
    for match in TICKER_PATTERN.findall(text_up):
        t = match.replace('$', '')
        if t in TICKER_SET:
            found.add(f'${t}')
    # Find index/ETF names
    for name in INDEX_NAMES:
        if name.upper() in text_up:
            mapped = INDEX_MAP.get(name, name)
            found.add(f'${mapped}')
    return sorted(found) 