#!/usr/bin/env python3
"""
ScryptBot: AI-Powered FinancialJuice RSS Monitor
Fetches headlines from FinancialJuice RSS, analyzes with GPT, and posts to your X profile with chart screenshots.
(C) 2024-present ScryptBot Team
"""
import os
import sys
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import feedparser
import tweepy
from ai_analysis import analyze_financial_news
import difflib
import subprocess
import re
import yfinance as yf
import pandas as pd
from extract_tickers import extract_tickers_from_text, load_ticker_set
from tradingview_chart_screenshot import is_valid_tradingview_symbol
import string
import hashlib

# --- CONFIG ---
RSS_URL = "https://www.financialjuice.com/feed.ashx?xy=rss"
PROCESSED_FILE = "financialjuice_rss_processed.json"
POLL_INTERVAL = 120  # seconds

TRADINGVIEW_PREFIXES = ['NASDAQ', 'NYSE', 'AMEX', 'NYSEARCA']
SYMBOL_CACHE_FILE = 'tradingview_symbol_cache.json'

MACRO_TICKERS = {'OIL', 'USO', 'GLD', 'SLV', 'DBC', 'UUP', 'TLT', 'TIP'}

RECENT_SUMMARIES_FILE = "recent_summaries.json"
RECENT_HEADLINES_FILE = "recent_headlines.json"
HEADLINE_HASHES_FILE = "headline_hashes.json"

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scryptbot_ai_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ScryptBot')

# --- ENV & TWITTER SETUP ---
load_dotenv()
api_key = os.getenv('TWITTER_API_KEY')
api_secret = os.getenv('TWITTER_API_SECRET')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

if not all([api_key, api_secret, access_token, access_token_secret]):
    logger.error("Twitter API credentials not found in .env file.")
    sys.exit(1)

posting_client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

# --- TWEEPY API v1.1 for media upload ---
api_v1 = tweepy.API(
    tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
)

# --- PROCESSED TRACKING ---
def load_processed():
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_processed(processed):
    try:
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(list(processed), f)
    except Exception as e:
        logger.error(f"Failed to save processed file: {e}")

# --- RECENT SUMMARIES TRACKING ---
def load_recent_summaries():
    if os.path.exists(RECENT_SUMMARIES_FILE):
        try:
            with open(RECENT_SUMMARIES_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_recent_summaries(recent_summaries):
    try:
        with open(RECENT_SUMMARIES_FILE, 'w') as f:
            json.dump(list(recent_summaries), f)
    except Exception as e:
        logger.error(f"Failed to save recent summaries file: {e}")

# --- RECENT HEADLINES TRACKING ---
def load_recent_headlines():
    if os.path.exists(RECENT_HEADLINES_FILE):
        try:
            with open(RECENT_HEADLINES_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_recent_headlines(recent_headlines):
    try:
        with open(RECENT_HEADLINES_FILE, 'w') as f:
            json.dump(list(recent_headlines), f)
    except Exception as e:
        logger.error(f"Failed to save recent headlines file: {e}")

# --- POSTING ---
def get_sentiment_emoji(sentiment):
    return {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(sentiment.lower(), "⚪")

def get_action_emoji(action):
    return {"buy": "💰", "sell": "🛑", "hold": "🤷"}.get(action.lower(), "❓")

def extract_tickers(instrument, rationale):
    tickers = []
    # If instrument is a known ticker (simple heuristic: all caps, <=5 chars)
    if instrument and instrument.isupper() and 1 < len(instrument) <= 5:
        tickers.append(f"${instrument}")
    elif instrument.lower() in ["stock", "equities", "index", "commodity"] or not instrument:
        # Try to infer from rationale or use $SPY, $DIA for general equities
        if any(x in rationale.lower() for x in ["s&p", "equities", "stock", "index", "market"]):
            tickers.extend(["$SPY", "$DIA"])
    # Add more logic as needed
    return " ".join(tickers)

def generate_chart(ticker, period='5d', interval='30m'):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib not installed. Cannot generate chart.")
        return None
    if yf is None:
        logger.error("yfinance not installed. Cannot generate chart.")
        return None
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data is None or data.empty:
            logger.warning(f"No data for {ticker}")
            return None
        plt.figure(figsize=(6, 3))
        plt.plot(data.index, data['Close'], label=f'{ticker} Close')
        plt.title(f'{ticker} Price Chart')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.tight_layout()
        filename = f'chart_{ticker}.png'
        plt.savefig(filename)
        plt.close()
        return filename
    except Exception as e:
        logger.error(f"Chart generation failed for {ticker}: {e}")
        return None

def load_symbol_cache():
    if os.path.exists(SYMBOL_CACHE_FILE):
        with open(SYMBOL_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_symbol_cache(cache):
    with open(SYMBOL_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def find_valid_tradingview_symbol(ticker):
    cache = load_symbol_cache()
    if ticker in cache:
        return cache[ticker]
    for prefix in TRADINGVIEW_PREFIXES:
        symbol = f"{prefix}:{ticker}"
        try:
            if is_valid_tradingview_symbol(symbol):
                cache[ticker] = symbol
                save_symbol_cache(cache)
                return symbol
        except Exception as e:
            logger.warning(f"Error checking TradingView symbol {symbol}: {e}")
    logger.warning(f"No valid TradingView symbol found for {ticker}")
    return None

def get_tradingview_chart(ticker, timeframe='1H'):
    ticker = re.sub(r'^[A-Z]+:', '', ticker)
    logger.info(f'Preparing TradingView chart for raw ticker: {ticker}')
    subprocess.run([
        'python', 'tradingview_chart_screenshot.py', ticker, timeframe
    ], check=True)
    return os.path.join('screenshots', f'cropped_tradingview_{ticker}_{timeframe}.png')

def get_current_price(ticker):
    if not ticker or not isinstance(ticker, str):
        logger.error(f"Invalid ticker for price lookup: {ticker}")
        return None
    if yf is None:
        logger.error("yfinance is not installed. Cannot fetch price.")
        return None
    try:
        info = yf.Ticker(ticker).info
        price = info.get('regularMarketPrice')
        return price
    except Exception as e:
        logger.error(f"Failed to fetch price for {ticker}: {e}")
        return None

def get_recent_low_high(ticker, days=10):
    if yf is None:
        logger.error("yfinance is not installed. Cannot fetch price data.")
        return None, None
    try:
        # Use only today's 5-minute bars for intraday stop
        df = yf.download(ticker, period='1d', interval='5m')
        if df is None or df.empty:
            return None, None
        recent_low = df['Low'].min()
        recent_high = df['High'].max()
        def safe_to_float(val):
            if val is None:
                return None
            if isinstance(val, pd.Series) or isinstance(val, pd.DataFrame):
                try:
                    val = val.item()
                except Exception:
                    try:
                        val = float(val.values[0])
                    except Exception:
                        return None
            try:
                return float(val)
            except Exception:
                return None
        return safe_to_float(recent_low), safe_to_float(recent_high)
    except Exception as e:
        logger.error(f"Error fetching price data for {ticker}: {e}")
        return None, None

def compose_post(headline, ai_result, link, instrument):
    if 'error' in ai_result:
        return f"🚨 {headline}\nAI Error: {ai_result['error']}"
    summary = ai_result.get('summary', '')
    sentiment = ai_result.get('sentiment', '')
    action = ai_result.get('action', '')
    rationale = ai_result.get('rationale', '').strip()
    if len(rationale) > 100:
        rationale = rationale[:100]
    sentiment_emoji = get_sentiment_emoji(sentiment)
    action_emoji = get_action_emoji(action)
    hashtags = "#StockMarket #Macro"
    price_line = ""
    if yf is not None and instrument and isinstance(instrument, str) and instrument != 'NONE':
        price = get_current_price(instrument)
        price_line = f"Current ${instrument} price: ${price}" if price else ""
    expected_impact = ai_result.get('expected_impact', '')
    impact_line = f"Expected impact: {expected_impact}" if expected_impact else ""

    # Add stop-loss suggestion
    stop_line = ""
    if action == "buy":
        recent_low, _ = get_recent_low_high(instrument)
        if recent_low is not None:
            stop_line = f"Consider stop below ${recent_low:.2f} (recent low)"
    elif action == "sell":
        _, recent_high = get_recent_low_high(instrument)
        if recent_high is not None:
            stop_line = f"Consider stop above ${recent_high:.2f} (recent high)"

    post_prefix = (
        f"🚨 {summary}\n"
        f"{sentiment_emoji} {sentiment.capitalize()} | {action_emoji} {action.capitalize()} signal\n"
        f"{price_line}\n"
        f"{impact_line}\n"
        f"{stop_line}\n"
    )
    post_suffix = f"{rationale}\n${instrument}\n{hashtags}"

    max_len = 240
    available = max_len - len(post_prefix) - len(post_suffix) - 2  # 2 for newlines

    post = f"{post_prefix}{post_suffix}"
    return post[:240]

def is_similar(a, b, threshold=0.9):
    return difflib.SequenceMatcher(None, a, b).ratio() > threshold

def normalize_headline(headline):
    # Lowercase, strip, and remove punctuation
    return ''.join(c for c in headline.lower().strip() if c not in string.punctuation and not c.isspace())

def headline_hash(headline):
    norm = normalize_headline(headline)
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()

def load_headline_hashes():
    if os.path.exists(HEADLINE_HASHES_FILE):
        try:
            with open(HEADLINE_HASHES_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_headline_hashes(hashes):
    try:
        with open(HEADLINE_HASHES_FILE, 'w') as f:
            json.dump(list(hashes), f)
    except Exception as e:
        logger.error(f"Failed to save headline hashes file: {e}")

# --- MAIN LOOP ---
def main():
    logger.info("FinancialJuice RSS AI Monitor started.")
    processed = load_processed()
    logger.info(f"Loaded {len(processed)} processed headlines.")
    headline_hashes = load_headline_hashes()
    recent_summaries = load_recent_summaries()
    TICKER_SET = load_ticker_set()

    while True:
        try:
            logger.info("Fetching RSS feed...")
            feed = feedparser.parse(RSS_URL)
            new_items = []
            for entry in feed.entries:
                guid = entry.get('guid', entry.link)
                if guid not in processed:
                    new_items.append(entry)
            # Limit initial burst to only the most recent unprocessed headline
            MAX_INITIAL_POSTS = 1
            if len(processed) == 0 and len(new_items) > MAX_INITIAL_POSTS:
                logger.info(f"Limiting initial posts to the {MAX_INITIAL_POSTS} most recent headline.")
                new_items = new_items[:MAX_INITIAL_POSTS]
            # On each scan, only post the most recent new headline (if any)
            if len(new_items) > 1:
                logger.info(f"Multiple new headlines found, only posting the most recent one.")
                new_items = new_items[:1]
            logger.info(f"Found {len(new_items)} new headlines.")
            for entry in reversed(new_items):  # Oldest first
                guid = entry.get('guid', entry.link)
                headline = entry.title
                if not isinstance(headline, str):
                    headline = str(headline)
                h_hash = headline_hash(headline)
                logger.debug(f"Headline hash: {h_hash}")
                logger.debug(f"Current headline_hashes set: {headline_hashes}")
                # Hash-based deduplication
                if h_hash in headline_hashes:
                    logger.info(f"Skipping duplicate headline by hash: {h_hash}")
                    processed.add(guid)
                    save_processed(processed)
                    continue
                link = entry.link
                logger.info(f"Analyzing headline: {headline}")
                ai_result = analyze_financial_news(headline)
                logger.info(f"AI result: {ai_result}")
                action = ai_result.get('action', '')
                if not isinstance(action, str):
                    action = ''
                action = action.strip().lower()
                sentiment = ai_result.get('sentiment', '')
                if not isinstance(sentiment, str):
                    sentiment = ''
                sentiment = sentiment.strip().lower()
                instrument = ai_result.get('instrument', '')
                if not isinstance(instrument, str):
                    instrument = ''
                # Remove '=X' suffix if present
                if instrument.endswith('=X'):
                    instrument = instrument[:-2]
                instrument = instrument.upper()
                # Block if instrument is not in TICKER_SET or MACRO_TICKERS
                if (
                    not instrument
                    or (instrument not in TICKER_SET and instrument not in MACRO_TICKERS)
                ):
                    logger.warning(f"Skipping post: Invalid ticker '{instrument}' in headline: {headline}")
                    processed.add(guid)
                    save_processed(processed)
                    continue
                # Fuzzy duplicate detection on summary
                already_posted = False
                for prev_summary in recent_summaries:
                    if is_similar(ai_result.get('summary', ''), prev_summary):
                        already_posted = True
                        break
                if already_posted:
                    logger.info(f"Skipping duplicate event for {instrument}: {ai_result.get('summary', '')}")
                    processed.add(guid)
                    save_processed(processed)
                    continue
                # Add to recent_summaries (keep last 50)
                recent_summaries.add(ai_result.get('summary', ''))
                if len(recent_summaries) > 50:
                    recent_summaries.pop()
                save_recent_summaries(recent_summaries)
                # Only post if instrument is a valid ticker
                if should_post_signal(action, sentiment) and (instrument in TICKER_SET or instrument in MACRO_TICKERS):
                    post_text = compose_post(headline, ai_result, link, instrument)
                    media_id = None
                    try:
                        chart_path = get_tradingview_chart(instrument, '1H')
                        media = api_v1.media_upload(chart_path)
                        media_id = media.media_id
                        logger.info(f"Chart attached for {instrument}")
                    except Exception as e:
                        logger.error(f"Chart generation or media upload failed: {e}")
                        processed.add(guid)
                        save_processed(processed)
                        continue
                    logger.info(f"Posting to X: {post_text}")
                    try:
                        if media_id:
                            response = posting_client.create_tweet(text=post_text, media_ids=[media_id])
                        else:
                            response = posting_client.create_tweet(text=post_text)
                        logger.info(f"Posted: {response}")
                    except Exception as e:
                        logger.error(f"Failed to post: {e}")
                    processed.add(guid)
                    # After successful post, add hash to headline_hashes
                    headline_hashes.add(h_hash)
                    save_headline_hashes(headline_hashes)
                else:
                    logger.warning(f"Skipping post: No actionable signal for instrument '{instrument}' in headline: {headline}")
                processed.add(guid)
                save_processed(processed)
                time.sleep(5)  # Small delay between posts
            logger.info(f"Waiting {POLL_INTERVAL} seconds before next check...")
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(POLL_INTERVAL)

def test_post_latest_headline():
    # Hardcoded test for ABG (Asbury Automotive Group Inc.)
    headline = "Asbury Automotive (ABG) announces record quarterly vehicle sales, driven by strong demand for electric cars."
    link = "https://www.nasdaq.com/market-activity/stocks/abg"  # Example link
    instrument = "ABG"
    ai_result = analyze_financial_news(headline)
    ai_result["expected_impact"] = "+5%"  # For test, add expected impact
    instrument = ai_result.get('instrument', instrument).upper()
    if not instrument or instrument == 'NONE':
        logger.warning(f"AI did not return a valid instrument for headline: {headline}. Skipping post.")
        return
    post_text = compose_post(headline, ai_result, link, instrument)
    try:
        chart_path = get_tradingview_chart(instrument, '1H')
        media = api_v1.media_upload(chart_path)
        media_id = media.media_id
        logger.info(f"Chart attached for {instrument}")
    except Exception as e:
        logger.error(f"Chart generation or media upload failed: {e}")
        media_id = None
    logger.info(f"Posting to X: {post_text}")
    try:
        if media_id:
            response = posting_client.create_tweet(text=post_text, media_ids=[media_id])
        else:
            response = posting_client.create_tweet(text=post_text)
        logger.info(f"Posted: {response}")
    except Exception as e:
        logger.error(f"Failed to post: {e}")

def should_post_signal(action, sentiment):
    action = action.strip().lower()
    # Only allow buy or sell
    return action in ['buy', 'sell']

def demo_post_mock_headline():
    """Demo: Post a mock headline for video recording/demo purposes."""
    # Example: Buy signal
    mock_headline = "Apple announces record profits, stock expected to surge."
    mock_link = "https://finance.yahoo.com/quote/AAPL"
    ai_result = {
        'summary': 'Apple reports record profits, bullish outlook',
        'sentiment': 'positive',
        'instrument': 'AAPL',
        'action': 'buy',
        'rationale': 'Strong earnings suggest further upside for AAPL',
        'expected_impact': '+3%'
    }
    instrument = ai_result['instrument']
    post_text = compose_post(mock_headline, ai_result, mock_link, instrument)
    media_id = None
    try:
        chart_path = get_tradingview_chart(instrument, '1H')
        media = api_v1.media_upload(chart_path)
        media_id = media.media_id
        logger.info(f"Chart attached for {instrument}")
    except Exception as e:
        logger.error(f"Chart generation or media upload failed: {e}")
    logger.info(f"Posting DEMO to X: {post_text}")
    try:
        if media_id:
            response = posting_client.create_tweet(text=post_text, media_ids=[media_id])
        else:
            response = posting_client.create_tweet(text=post_text)
        logger.info(f"Posted DEMO: {response}")
    except Exception as e:
        logger.error(f"Failed to post DEMO: {e}")

if __name__ == '__main__':
    # demo_post_mock_headline()  # <-- Run this for your demo, then comment/remove after
    main() 