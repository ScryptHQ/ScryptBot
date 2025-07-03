#!/usr/bin/env python3
"""
ScryptBot: Focused FinancialJuice Monitor
Optimized for high-frequency monitoring of @financialjuice (5-20 posts/day)
(C) 2024-present ScryptBot Team
"""

import logging
import time
import signal
import sys
import os
import json
import tweepy
from datetime import datetime, timedelta
from typing import Dict, List
from dotenv import load_dotenv

from config import LOG_LEVEL, LOGS_TO_CLOUD, DEBUG, TEST_MODE
from twitter_modern_v2_only import TwitterV2Only
from analysis_modern import AnalysisModern
from trading_modern import TradingModern

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('financial_juice_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Focus on @financialjuice - high frequency account
FINANCIAL_JUICE_ID = '381696140'  # Real user ID for @financialjuice

class FinancialJuiceMonitor:
    """Optimized monitor for @financialjuice high-frequency posts"""
    
    def __init__(self):
        """Initialize the financial juice monitor"""
        self.twitter = TwitterV2Only()
        self.analyzer = AnalysisModern()
        self.trader = TradingModern()
        self.running = False
        self.processed_tweets = set()
        
        # Load environment variables for posting
        load_dotenv()
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        # Setup posting client
        self.posting_client = None
        if all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            try:
                self.posting_client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
                logger.info("Twitter posting client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize posting client: {e}")
        
        self.stats = {
            'tweets_processed': 0,
            'companies_found': 0,
            'trades_executed': 0,
            'tweets_posted': 0,
            'retweets_posted': 0,
            'start_time': datetime.now().isoformat(),
            'last_tweet_time': None,
            'financial_juice_tweets_processed': 0
        }
        
        # Load previously processed tweets
        self.processed_tweets = self.load_processed_tweets()
        logger.info(f"Loaded {len(self.processed_tweets)} previously processed tweets")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Financial Juice Monitor initialized - focusing on @financialjuice")
    
    def load_processed_tweets(self) -> set:
        """Load previously processed tweet IDs from file"""
        try:
            if os.path.exists('financial_juice_processed_tweets.json'):
                with open('financial_juice_processed_tweets.json', 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_tweets', []))
        except Exception as e:
            logger.error(f"Failed to load processed tweets: {e}")
        return set()
    
    def save_processed_tweets(self):
        """Save processed tweet IDs to file"""
        try:
            data = {
                'processed_tweets': list(self.processed_tweets),
                'last_updated': datetime.now().isoformat()
            }
            with open('financial_juice_processed_tweets.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processed tweets: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.save_processed_tweets()
        self.stop()
        sys.exit(0)
    
    def create_analysis_tweet(self, companies: List[Dict], original_tweet: Dict) -> str | None:
        """Create analysis tweet optimized for financial content"""
        if not companies:
            return None
        
        analysis = "📊 FINANCIAL ANALYSIS\n\n"
        
        for company in companies:
            sentiment_emoji = "📈" if company['sentiment'] > 0 else "📉" if company['sentiment'] < 0 else "➡️"
            action = "BUY" if company['sentiment'] > 0.3 else "SELL" if company['sentiment'] < -0.3 else "HOLD"
            confidence = "HIGH" if abs(company['sentiment']) > 0.5 else "MEDIUM" if abs(company['sentiment']) > 0.2 else "LOW"
            
            analysis += f"{sentiment_emoji} {company['name']} ({company['ticker']})\n"
            analysis += f"   Sentiment: {company['sentiment']:.3f} ({confidence})\n"
            analysis += f"   Signal: {action}\n\n"
        
        analysis += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
        analysis += "\n#FinancialAnalysis #TradingSignals #StockMarket"
        
        return analysis
    
    def retweet_original(self, tweet_id: str) -> bool:
        """Retweet the original tweet"""
        if not self.posting_client:
            logger.warning("No posting client available")
            return False
            
        try:
            response = self.posting_client.retweet(tweet_id)
            
            if response and hasattr(response, 'data'):
                retweet_data = getattr(response, 'data', None)
                if retweet_data and isinstance(retweet_data, dict) and 'id' in retweet_data:
                    retweet_id = retweet_data['id']
                    logger.info(f"Retweeted Financial Juice tweet! ID: {retweet_id}")
                    self.stats['retweets_posted'] += 1
                    return True
            
            logger.warning("Retweet failed - no response data")
            return False
                
        except Exception as e:
            logger.error(f"Failed to retweet: {e}")
            return False
    
    def post_analysis_reply(self, tweet_text: str, original_tweet_id: str) -> bool:
        """Post analysis as a reply to the original tweet"""
        if not self.posting_client:
            logger.warning("No posting client available")
            return False
            
        try:
            response = self.posting_client.create_tweet(
                text=tweet_text,
                in_reply_to_tweet_id=original_tweet_id
            )
            
            if response and hasattr(response, 'data'):
                tweet_data = getattr(response, 'data', None)
                if tweet_data and isinstance(tweet_data, dict) and 'id' in tweet_data:
                    reply_id = tweet_data['id']
                    logger.info(f"Analysis reply posted! ID: {reply_id}")
                    self.stats['tweets_posted'] += 1
                    return True
            
            logger.warning("Reply posting failed - no response data")
            return False
                
        except Exception as e:
            logger.error(f"Failed to post reply: {e}")
            return False
    
    def process_tweet(self, tweet: Dict):
        """Process a single tweet from @financialjuice"""
        tweet_id = tweet.get('id')
        tweet_text = tweet.get('text', '')
        author_id = tweet.get('author_id')
        
        # Only process @financialjuice tweets
        if author_id != FINANCIAL_JUICE_ID:
            return
        
        # Skip if already processed
        if tweet_id in self.processed_tweets:
            return
        
        # Ensure tweet_id is a string
        if not tweet_id:
            logger.warning("Tweet ID is missing")
            return
        
        tweet_id_str = str(tweet_id)
        
        logger.info(f"Processing Financial Juice tweet: {tweet_id_str}")
        logger.info(f"Tweet text: {tweet_text[:100]}...")
        
        # Analyze for companies
        companies = self.analyzer.find_companies(tweet_text)
        
        if companies:
            logger.info(f"Found {len(companies)} companies in tweet")
            
            # Retweet the original
            retweet_success = self.retweet_original(tweet_id_str)
            
            # Create and post analysis
            analysis_text = self.create_analysis_tweet(companies, tweet)
            if analysis_text:
                reply_success = self.post_analysis_reply(analysis_text, tweet_id_str)
                
                if reply_success:
                    logger.info("Successfully posted analysis reply")
                else:
                    logger.warning("Failed to post analysis reply")
            
            # Simulate trading
            trade_result = self.trader.make_trades(companies)
            if trade_result:
                logger.info("Simulated trades executed successfully")
            
            self.stats['companies_found'] += len(companies)
            self.stats['trades_executed'] += len(companies)
        
        # Mark as processed
        self.processed_tweets.add(tweet_id_str)
        self.stats['tweets_processed'] += 1
        self.stats['financial_juice_tweets_processed'] += 1
        self.stats['last_tweet_time'] = datetime.now().isoformat()
        
        # Save processed tweets periodically
        if len(self.processed_tweets) % 10 == 0:
            self.save_processed_tweets()
    
    def monitor_financial_juice(self, interval: int = 600):  # 10 minutes for safer frequency
        """Monitor @financialjuice tweets with high frequency and 429 backoff"""
        logger.info(f"Starting Financial Juice Monitor (interval: {interval}s)")
        logger.info("Focus: @financialjuice (5-20 posts/day)")
        
        self.running = True
        
        while self.running:
            try:
                logger.info("Checking for new Financial Juice tweets...")
                
                tweets = self.twitter.get_user_tweets(FINANCIAL_JUICE_ID, max_results=10)
                logger.info(f"DEBUG: Raw tweets fetched: {tweets}")
                
                # Check for 429 error in tweets (assuming error is returned as None or empty list)
                if tweets is None or (isinstance(tweets, list) and len(tweets) == 0):
                    # Check for last error in logs or add a check in the Twitter client for 429
                    # For now, log and backoff if no tweets and last error was 429
                    last_log = getattr(self.twitter, 'last_error', None)
                    if last_log and '429' in str(last_log):
                        logger.warning("429 Too Many Requests detected. Backing off for 30 minutes.")
                        time.sleep(1800)  # 30 minutes
                        continue
                
                if tweets:
                    logger.info(f"Found {len(tweets)} recent tweets")
                    
                    for tweet in tweets:
                        self.process_tweet(tweet)
                        time.sleep(2)
                else:
                    logger.info("No new tweets found")
                
                self.log_stats()
                logger.info(f"Waiting {interval} seconds before next check...")
                time.sleep(interval)
                
            except Exception as e:
                # If 429 in exception, backoff
                if '429' in str(e):
                    logger.warning("429 Too Many Requests detected in exception. Backing off for 30 minutes.")
                    time.sleep(1800)
                else:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(interval)
    
    def log_stats(self):
        """Log current statistics"""
        logger.info("Current Stats:")
        logger.info(f"   Tweets Processed: {self.stats['tweets_processed']}")
        logger.info(f"   Financial Juice Tweets: {self.stats['financial_juice_tweets_processed']}")
        logger.info(f"   Companies Found: {self.stats['companies_found']}")
        logger.info(f"   Trades Executed: {self.stats['trades_executed']}")
        logger.info(f"   Tweets Posted: {self.stats['tweets_posted']}")
        logger.info(f"   Retweets Posted: {self.stats['retweets_posted']}")
        
        if self.stats['last_tweet_time']:
            last_time = datetime.fromisoformat(self.stats['last_tweet_time'])
            time_diff = datetime.now() - last_time
            logger.info(f"   Last Tweet: {time_diff.total_seconds()/60:.1f} minutes ago")
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'running': self.running,
            'stats': self.stats,
            'processed_tweets_count': len(self.processed_tweets)
        }
    
    def stop(self):
        """Stop the monitor"""
        self.running = False
        self.save_processed_tweets()
        logger.info("Financial Juice Monitor stopped")

def main():
    """Main function"""
    print("Financial Juice Monitor")
    print("Optimized for @financialjuice (5-20 posts/day)")
    print("=" * 50)
    
    monitor = FinancialJuiceMonitor()
    
    try:
        # Start monitoring with 10-minute intervals for high frequency
        monitor.monitor_financial_juice(interval=600)  # 10 minutes
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main() 