#!/usr/bin/env python3
"""
Test Financial Juice Monitor
Test the focused monitor for @financialjuice
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_financial_juice_focused import FinancialJuiceMonitor

def test_financial_juice_monitor():
    """Test the financial juice monitor"""
    print("🧪 Testing Financial Juice Monitor")
    print("=" * 50)
    
    # Create monitor instance
    monitor = FinancialJuiceMonitor()
    
    # Test status
    status = monitor.get_status()
    print(f"✅ Monitor initialized: {status['running']}")
    print(f"📊 Stats: {status['stats']}")
    print(f"📝 Processed tweets: {status['processed_tweets_count']}")
    
    # Test with sample financial tweet
    sample_tweet = {
        'id': '1234567890',
        'text': 'Apple (AAPL) just announced amazing earnings! The stock is going to the moon! 🚀',
        'author_id': '381696140'  # @financialjuice ID
    }
    
    print("\n🔍 Testing with sample tweet:")
    print(f"📝 Tweet: {sample_tweet['text']}")
    
    # Process the sample tweet
    monitor.process_tweet(sample_tweet)
    
    # Check updated stats
    updated_status = monitor.get_status()
    print(f"\n📊 Updated stats:")
    print(f"   Tweets Processed: {updated_status['stats']['tweets_processed']}")
    print(f"   Financial Juice Tweets: {updated_status['stats']['financial_juice_tweets_processed']}")
    print(f"   Companies Found: {updated_status['stats']['companies_found']}")
    
    print("\n✅ Test completed successfully!")
    
    # Clean up
    monitor.stop()

if __name__ == "__main__":
    test_financial_juice_monitor() 