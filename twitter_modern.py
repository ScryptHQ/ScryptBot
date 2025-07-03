"""
Modern Twitter API integration for ScryptBot
Modernized and maintained 2024
Uses Twitter API v2 with proper authentication and rate limiting
"""

import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable
import tweepy
from tweepy import Client, StreamingClient, StreamRule
from tweepy.errors import TweepyException, TooManyRequests

from config import (
    TWITTER_BEARER_TOKEN, TWITTER_API_KEY, TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET,
    TARGET_ACCOUNTS, TWITTER_RATE_LIMIT_DELAY, MAX_RETRIES, RETRY_DELAY
)

logger = logging.getLogger(__name__)

class TwitterModern:
    """Modern Twitter API client using Twitter API v2"""
    
    def __init__(self):
        """Initialize Twitter client with API v2 authentication"""
        self.client = None
        self.streaming_client = None
        self.setup_client()
        
    def setup_client(self):
        """Setup Twitter API v2 client with proper authentication"""
        try:
            # For read-only access (streaming tweets)
            if TWITTER_BEARER_TOKEN:
                self.client = Client(bearer_token=TWITTER_BEARER_TOKEN)
                logger.info("Twitter client initialized with Bearer Token")
            
            # For posting tweets (if credentials are provided)
            if all([TWITTER_API_KEY, TWITTER_API_SECRET, 
                   TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
                self.client = Client(
                    consumer_key=TWITTER_API_KEY,
                    consumer_secret=TWITTER_API_SECRET,
                    access_token=TWITTER_ACCESS_TOKEN,
                    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
                )
                logger.info("Twitter client initialized with full credentials")
            
            if not self.client:
                logger.warning("Twitter client not initialized - missing credentials")
                
        except Exception as e:
            logger.error(f"Failed to setup Twitter client: {e}")
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Get user ID from username"""
        if not self.client:
            return None
            
        try:
            user = self.client.get_user(username=username)
            if user.data:
                return str(user.data.id)
        except TweepyException as e:
            logger.error(f"Failed to get user ID for {username}: {e}")
        return None
    
    def get_user_tweets(self, username: str, max_results: int = 10) -> List[Dict]:
        """Get recent tweets from a user"""
        if not self.client:
            return []
            
        try:
            user_id = self.get_user_id(username)
            if not user_id:
                return []
                
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'entities']
            )
            
            if tweets.data:
                return [self._format_tweet(tweet) for tweet in tweets.data]
                
        except TweepyException as e:
            logger.error(f"Failed to get tweets for {username}: {e}")
        except TooManyRequests:
            logger.warning("Rate limit exceeded, waiting...")
            time.sleep(RETRY_DELAY)
            
        return []
    
    def _format_tweet(self, tweet) -> Dict:
        """Format tweet data for internal use"""
        return {
            'id': str(tweet.id),
            'text': tweet.text,
            'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
            'author_id': tweet.author_id,
            'public_metrics': tweet.public_metrics._json if tweet.public_metrics else {},
            'entities': tweet.entities._json if tweet.entities else {},
            'url': f"https://twitter.com/user/status/{tweet.id}"
        }
    
    def post_tweet(self, text: str) -> bool:
        """Post a tweet (if authenticated)"""
        if not self.client or not all([TWITTER_API_KEY, TWITTER_API_SECRET, 
                                      TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
            logger.warning("Cannot post tweet - missing credentials")
            return False
            
        try:
            response = self.client.create_tweet(text=text)
            if response.data:
                logger.info(f"Tweet posted successfully: {response.data['id']}")
                return True
        except TweepyException as e:
            logger.error(f"Failed to post tweet: {e}")
        except TooManyRequests:
            logger.warning("Rate limit exceeded for posting")
            time.sleep(RETRY_DELAY)
            
        return False
    
    def start_streaming(self, callback: Callable, usernames: List[str] = None):
        """Start streaming tweets from specified users"""
        if not TWITTER_BEARER_TOKEN:
            logger.error("Bearer token required for streaming")
            return
            
        usernames = usernames or TARGET_ACCOUNTS
        user_ids = []
        
        # Get user IDs for streaming
        for username in usernames:
            user_id = self.get_user_id(username)
            if user_id:
                user_ids.append(user_id)
                logger.info(f"Added {username} (ID: {user_id}) to stream")
            else:
                logger.warning(f"Could not find user ID for {username}")
        
        if not user_ids:
            logger.error("No valid user IDs found for streaming")
            return
            
        # Start streaming
        try:
            self.streaming_client = TwitterStreamingClient(callback)
            self.streaming_client.filter(follow=user_ids)
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
    
    def stop_streaming(self):
        """Stop the streaming client"""
        if self.streaming_client:
            self.streaming_client.disconnect()
            self.streaming_client = None
            logger.info("Streaming stopped")


class TwitterStreamingClient(StreamingClient):
    """Custom streaming client for handling tweets"""
    
    def __init__(self, callback: Callable):
        super().__init__(TWITTER_BEARER_TOKEN)
        self.callback = callback
        self.logger = logging.getLogger(__name__)
    
    def on_tweet(self, tweet):
        """Handle incoming tweet"""
        try:
            tweet_data = self._format_streaming_tweet(tweet)
            self.logger.info(f"Received tweet: {tweet_data['id']}")
            self.callback(tweet_data)
        except Exception as e:
            self.logger.error(f"Error processing tweet: {e}")
    
    def on_error(self, status):
        """Handle streaming errors"""
        self.logger.error(f"Streaming error: {status}")
    
    def on_connection_error(self):
        """Handle connection errors"""
        self.logger.error("Streaming connection error")
    
    def _format_streaming_tweet(self, tweet) -> Dict:
        """Format streaming tweet data"""
        return {
            'id': str(tweet.id),
            'text': tweet.text,
            'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
            'author_id': tweet.author_id,
            'public_metrics': tweet.public_metrics._json if hasattr(tweet, 'public_metrics') else {},
            'entities': tweet.entities._json if hasattr(tweet, 'entities') else {},
            'url': f"https://twitter.com/user/status/{tweet.id}"
        }


def create_tweet_summary(companies: List[Dict], original_tweet: Dict) -> str:
    """Create a summary tweet about detected companies"""
    if not companies:
        return ""
    
    # Build company lines
    company_lines = []
    for company in companies:
        name = company.get('name', 'Unknown')
        ticker = company.get('ticker', '')
        sentiment = company.get('sentiment', 0)
        
        # Sentiment emoji
        if sentiment > 0:
            emoji = "📈"
        elif sentiment < 0:
            emoji = "📉"
        else:
            emoji = "➡️"
        
        ticker_str = f"${ticker}" if ticker else ""
        line = f"{emoji} {name} {ticker_str}"
        company_lines.append(line)
    
    # Combine with original tweet link
    tweet_url = original_tweet.get('url', '')
    summary = "\n".join(company_lines)
    
    # Check length limit (280 characters for Twitter)
    max_length = 280 - len(tweet_url) - 2  # -2 for newline
    if len(summary) > max_length:
        summary = summary[:max_length-3] + "..."
    
    return f"{summary}\n{tweet_url}"


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the Twitter client
    twitter = TwitterModern()
    
    # Test getting user ID
    user_id = twitter.get_user_id("realDonaldTrump")
    print(f"Trump user ID: {user_id}")
    
    # Test getting recent tweets
    tweets = twitter.get_user_tweets("realDonaldTrump", max_results=5)
    print(f"Found {len(tweets)} tweets")
    
    for tweet in tweets:
        print(f"Tweet: {tweet['text'][:100]}...") 