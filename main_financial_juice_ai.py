#!/usr/bin/env python3
"""
ScryptBot: AI-Powered FinancialJuice Tweet Monitor
Fetches @financialjuice tweets, analyzes with GPT, and posts to your X profile.
(C) 2024-present ScryptBot Team
"""
import logging
import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import tweepy
from twitter_modern_v2_only import TwitterV2Only
from ai_analysis import analyze_financial_news

FINANCIAL_JUICE_ID = '381696140'
POLL_INTERVAL = 600  # 10 minutes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('financial_juice_ai_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv('TWITTER_API_KEY')
api_secret = os.getenv('TWITTER_API_SECRET')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Setup posting client
posting_client = None
if all([api_key, api_secret, access_token, access_token_secret]):
    posting_client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
else:
    logger.error("Twitter API credentials not found in .env file.")
    sys.exit(1)

twitter = TwitterV2Only()

# Track processed tweets
PROCESSED_FILE = 'financial_juice_ai_processed.json'
def load_processed():
    import json
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            try:
                return set(json.load(f))
            except Exception:
                return set()
    return set()
def save_processed(processed):
    import json
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(list(processed), f)

def compose_post(headline, ai_result):
    if 'error' in ai_result:
        return f"FinancialJuice: {headline}\n\nAI Analysis Error: {ai_result['error']}"
    return (
        f"FinancialJuice: {headline}\n\n"
        f"AI Analysis: {ai_result.get('summary','')}\n"
        f"Sentiment: {ai_result.get('sentiment','')}\n"
        f"Instrument: {ai_result.get('instrument','')}\n"
        f"Action: {ai_result.get('action','')}\n"
        f"Rationale: {ai_result.get('rationale','')}"
    )

def main():
    logger.info("Financial Juice AI Monitor started.")
    processed = load_processed()
    logger.info(f"Loaded {len(processed)} processed tweets.")

    # --- First launch: always process and post the most recent tweet ---
    try:
        logger.info("Fetching the most recent tweet from @financialjuice for first launch...")
        tweets = twitter.get_user_tweets(FINANCIAL_JUICE_ID, max_results=1)
        logger.info(f"Fetched tweets: {tweets}")
        if tweets:
            tweet = tweets[0]
            tweet_id = tweet.get('id')
            text = tweet.get('text','')
            logger.info(f"[FIRST LAUNCH] Analyzing tweet ID {tweet_id}: {text}")
            ai_result = analyze_financial_news(text)
            logger.info(f"AI result: {ai_result}")
            post_text = compose_post(text, ai_result)
            logger.info(f"Posting to X: {post_text}")
            if not posting_client:
                logger.error("Posting client not initialized.")
            else:
                try:
                    response = posting_client.create_tweet(text=post_text)
                    logger.info(f"Posted tweet: {response}")
                except Exception as e:
                    logger.error(f"Failed to post tweet: {e}")
            processed.add(tweet_id)
            save_processed(processed)
        else:
            logger.info("No tweets found for @financialjuice on first launch.")
    except Exception as e:
        logger.error(f"Error during first launch post: {e}")

    # --- Normal polling loop ---
    while True:
        try:
            logger.info("Fetching latest tweets from @financialjuice...")
            tweets = twitter.get_user_tweets(FINANCIAL_JUICE_ID, max_results=5)
            logger.info(f"Fetched tweets: {tweets}")
            new_tweets = [t for t in tweets if t.get('id') not in processed]
            logger.info(f"Found {len(new_tweets)} new tweets.")
            for tweet in new_tweets:
                tweet_id = tweet.get('id')
                text = tweet.get('text','')
                logger.info(f"Analyzing tweet ID {tweet_id}: {text}")
                ai_result = analyze_financial_news(text)
                logger.info(f"AI result: {ai_result}")
                post_text = compose_post(text, ai_result)
                logger.info(f"Posting to X: {post_text}")
                if not posting_client:
                    logger.error("Posting client not initialized.")
                    continue
                try:
                    response = posting_client.create_tweet(text=post_text)
                    logger.info(f"Posted tweet: {response}")
                except Exception as e:
                    logger.error(f"Failed to post tweet: {e}")
                processed.add(tweet_id)
                save_processed(processed)
                time.sleep(5)  # Small delay between posts
            logger.info(f"Waiting {POLL_INTERVAL} seconds before next check...")
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main() 