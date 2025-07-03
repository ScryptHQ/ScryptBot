"""
Configuration settings for ScryptBot
Modernized and maintained 2024
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twitter Configuration (API v2)
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Target Twitter accounts to monitor
# (Legacy: TRUMP_USER_ID, TRUMP_USERNAME, etc. can be removed if not used)
TARGET_ACCOUNTS = [
    'elonmusk',        # Definitely active account for testing
    'BillGates',       # Active account for testing
    # Add more accounts as needed
]

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Trading Configuration
# Using yfinance for free market data instead of paid APIs
USE_REAL_MONEY = os.getenv('USE_REAL_MONEY', 'NO') == 'YES'

# Polygon API for additional market data
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

# Trading parameters
CASH_HOLD = 1000  # Amount to keep in reserve
LIMIT_FRACTION = 0.1  # Limit order percentage
ORDER_DELAY_S = 30 * 60  # 30 minutes

# Blacklisted tickers (avoid insider trading)
TICKER_BLACKLIST = ['GOOG', 'GOOGL', 'META', 'TSLA']

# Market hours (Eastern Time)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# Logging configuration
LOGS_TO_CLOUD = os.getenv('LOGS_TO_CLOUD', 'NO') == 'YES'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Web interface configuration
WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.getenv('WEB_PORT', '8080'))

# Sentiment analysis thresholds
SENTIMENT_THRESHOLD_POSITIVE = 0.1
SENTIMENT_THRESHOLD_NEGATIVE = -0.1

# Company detection settings
MIN_COMPANY_CONFIDENCE = 0.7
MAX_COMPANIES_PER_TWEET = 5

# Rate limiting
TWITTER_RATE_LIMIT_DELAY = 1  # seconds between API calls
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Database configuration (optional)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///scryptbot.db')

# Notification settings
ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'NO') == 'YES'
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_TO = os.getenv('EMAIL_TO')

# Development settings
DEBUG = os.getenv('DEBUG', 'NO') == 'YES'
TEST_MODE = os.getenv('TEST_MODE', 'NO') == 'YES' 