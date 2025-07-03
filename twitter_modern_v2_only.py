"""
Twitter API v2 only client for ScryptBot
Modernized and maintained 2024
Uses only Twitter API v2 endpoints to work with limited access levels
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

class TwitterV2Only:
    """Twitter API v2 only client - works with limited access levels"""
    
    def __init__(self):
        """Initialize Twitter client with API v2 authentication only"""
        self.client = None
        self.streaming_client = None
        self.setup_client()
        
    def setup_client(self):
        """Setup Twitter API v2 client with Bearer Token only"""
        try:
            # Use only Bearer Token for v2 API access
            if TWITTER_BEARER_TOKEN:
                self.client = Client(bearer_token=TWITTER_BEARER_TOKEN)
                logger.info("Twitter client initialized with Bearer Token (v2 only)")
            else:
                logger.error("Bearer Token required for v2 API access")
                
        except Exception as e:
            logger.error(f"Failed to setup Twitter client: {e}")
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Get user ID from username using v2 API"""
        if not self.client:
            return None
            
        try:
            response = self.client.get_user(username=username)
            if response.data:
                return str(response.data.id)
        except TweepyException as e:
            logger.error(f"Failed to get user ID for {username}: {e}")
        return None
    
    def get_user_tweets(self, username: str, max_results: int = 10) -> List[Dict]:
        """Get recent tweets from a user using v2 API"""
        if not self.client:
            return []
            
        try:
            user_id = self.get_user_id(username)
            if not user_id:
                return []
                
            response = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'entities']
            )
            
            if response.data:
                return [self._format_tweet(tweet) for tweet in response.data]
                
        except TweepyException as e:
            logger.error(f"Failed to get tweets for {username}: {e}")
        except TooManyRequests:
            logger.warning("Rate limit exceeded, waiting...")
            time.sleep(RETRY_DELAY)
            
        return []
    
    def get_user_tweets_by_id(self, user_id: str, max_results: int = 10) -> List[Dict]:
        """Get recent tweets from a user by ID using v2 API"""
        if not self.client:
            return []
            
        try:
            response = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'entities']
            )
            
            if response.data:
                return [self._format_tweet(tweet) for tweet in response.data]
                
        except TweepyException as e:
            logger.error(f"Failed to get tweets for user ID {user_id}: {e}")
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
            'public_metrics': getattr(tweet.public_metrics, '_json', {}) if tweet.public_metrics else {},
            'entities': getattr(tweet.entities, '_json', {}) if tweet.entities else {},
            'url': f"https://twitter.com/user/status/{tweet.id}"
        }
    
    def post_tweet(self, text: str) -> bool:
        """Post a tweet - disabled for limited access"""
        logger.warning("Tweet posting disabled - limited API access")
        return False
    
    def start_streaming(self, callback: Callable, usernames: List[str] = None):
        """Start streaming tweets from specified users using v2 API"""
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
    """Create a summary tweet about found companies"""
    if not companies:
        return None
    
    summary = "📊 Company mentions detected:\n"
    for company in companies:
        sentiment_emoji = "📈" if company['sentiment'] > 0 else "📉" if company['sentiment'] < 0 else "➡️"
        summary += f"{sentiment_emoji} {company['name']} ({company['ticker']})\n"
    
    summary += f"\nOriginal: {original_tweet.get('url', '')}"
    return summary 