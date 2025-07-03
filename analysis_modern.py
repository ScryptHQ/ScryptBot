"""
Modern analysis module for ScryptBot
Uses Google Cloud Natural Language API and improved company detection
"""

import logging
import re
import time
from typing import List, Dict, Optional
from google.cloud import language_v1
from google.cloud.language_v1 import Document, AnalyzeEntitiesResponse
import requests
import yfinance as yf

from config import (
    GOOGLE_APPLICATION_CREDENTIALS, MIN_COMPANY_CONFIDENCE,
    MAX_COMPANIES_PER_TWEET, SENTIMENT_THRESHOLD_POSITIVE,
    SENTIMENT_THRESHOLD_NEGATIVE, TICKER_BLACKLIST
)

logger = logging.getLogger(__name__)

class AnalysisModern:
    """Modern analysis using Google Cloud Natural Language API"""
    
    def __init__(self):
        """Initialize the analysis client"""
        self.language_client = None
        self.setup_language_client()
        
        # Common company name variations and their tickers
        self.company_mappings = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'amazon': 'AMZN',
            'facebook': 'META',
            'meta': 'META',
            'tesla': 'TSLA',
            'netflix': 'NFLX',
            'nvidia': 'NVDA',
            'amd': 'AMD',
            'intel': 'INTC',
            'coca cola': 'KO',
            'coca-cola': 'KO',
            'coke': 'KO',
            'mcdonalds': 'MCD',
            'disney': 'DIS',
            'walmart': 'WMT',
            'target': 'TGT',
            'home depot': 'HD',
            'lowes': 'LOW',
            'boeing': 'BA',
            'lockheed': 'LMT',
            'lockheed martin': 'LMT',
            'general electric': 'GE',
            'ge': 'GE',
            'ford': 'F',
            'general motors': 'GM',
            'gm': 'GM',
            'chevron': 'CVX',
            'exxon': 'XOM',
            'exxon mobil': 'XOM',
            'shell': 'SHEL',
            'bp': 'BP',
            'jpmorgan': 'JPM',
            'jpmorgan chase': 'JPM',
            'bank of america': 'BAC',
            'wells fargo': 'WFC',
            'goldman sachs': 'GS',
            'morgan stanley': 'MS',
            'blackrock': 'BLK',
            'visa': 'V',
            'mastercard': 'MA',
            'paypal': 'PYPL',
            'square': 'SQ',
            'block': 'SQ',
            'uber': 'UBER',
            'lyft': 'LYFT',
            'airbnb': 'ABNB',
            'doordash': 'DASH',
            'zoom': 'ZM',
            'slack': 'WORK',
            'salesforce': 'CRM',
            'oracle': 'ORCL',
            'ibm': 'IBM',
            'cisco': 'CSCO',
            'qualcomm': 'QCOM',
            'verizon': 'VZ',
            'at&t': 'T',
            'att': 'T',
            'comcast': 'CMCSA',
            'charter': 'CHTR',
            'time warner': 'T',
            'warner bros': 'WBD',
            'warner brothers': 'WBD',
            'paramount': 'PARA',
            'viacom': 'PARA',
            'fox': 'FOX',
            'fox news': 'FOX',
            'cnn': 'CMCSA',  # Part of Comcast
            'msnbc': 'CMCSA',  # Part of Comcast
            'cnbc': 'CMCSA',  # Part of Comcast
            'new york times': 'NYT',
            'washington post': 'AMZN',  # Owned by Amazon
            'wall street journal': 'NWS',
            'wsj': 'NWS',
            'bloomberg': 'BLK',  # Part of BlackRock
            'reuters': 'TRI',
            'associated press': 'AP',
            'ap': 'AP',
        }
        
    def setup_language_client(self):
        """Setup Google Cloud Natural Language client"""
        try:
            if GOOGLE_APPLICATION_CREDENTIALS:
                self.language_client = language_v1.LanguageServiceClient()
                logger.info("Google Cloud Language client initialized")
            else:
                logger.warning("Google Cloud credentials not found - using fallback analysis")
        except Exception as e:
            logger.error(f"Failed to setup Google Cloud client: {e}")
    
    def find_companies(self, tweet_text: str) -> List[Dict]:
        """Find companies mentioned in tweet text"""
        if not tweet_text:
            return []
        
        companies = []
        
        # Use Google Cloud Natural Language API if available
        if self.language_client:
            companies.extend(self._analyze_with_google_cloud(tweet_text))
        
        # Fallback to pattern matching
        companies.extend(self._analyze_with_patterns(tweet_text))
        
        # Remove duplicates and limit results
        unique_companies = self._deduplicate_companies(companies)
        return unique_companies[:MAX_COMPANIES_PER_TWEET]
    
    def _analyze_with_google_cloud(self, text: str) -> List[Dict]:
        """Analyze text using Google Cloud Natural Language API"""
        companies = []
        
        try:
            document = Document(
                content=text,
                type_=Document.Type.PLAIN_TEXT,
                language='en'
            )
            
            # Analyze entities
            response = self.language_client.analyze_entities(document=document)
            
            for entity in response.entities:
                # Check if entity is an organization with sufficient confidence
                if (entity.type_ == language_v1.Entity.Type.ORGANIZATION and 
                    entity.salience >= MIN_COMPANY_CONFIDENCE):
                    
                    company_name = entity.name.lower()
                    ticker = self._get_ticker_for_company(company_name)
                    
                    if ticker:
                        sentiment = self._analyze_sentiment_for_entity(text, entity)
                        companies.append({
                            'name': entity.name,
                            'ticker': ticker,
                            'confidence': entity.salience,
                            'sentiment': sentiment,
                            'source': 'google_cloud'
                        })
                        
        except Exception as e:
            logger.error(f"Google Cloud analysis failed: {e}")
        
        return companies
    
    def _analyze_with_patterns(self, text: str) -> List[Dict]:
        """Fallback analysis using pattern matching"""
        companies = []
        text_lower = text.lower()
        
        # Look for company names in our mapping
        for company_name, ticker in self.company_mappings.items():
            if company_name in text_lower:
                # Simple sentiment analysis based on keywords
                sentiment = self._simple_sentiment_analysis(text)
                
                companies.append({
                    'name': company_name.title(),
                    'ticker': ticker,
                    'confidence': 0.8,  # High confidence for known companies
                    'sentiment': sentiment,
                    'source': 'pattern_matching'
                })
        
        # Look for ticker symbols (e.g., $AAPL, $TSLA)
        ticker_pattern = r'\$([A-Z]{1,5})'
        matches = re.findall(ticker_pattern, text, re.IGNORECASE)
        
        for ticker in matches:
            if ticker.upper() not in TICKER_BLACKLIST:
                sentiment = self._simple_sentiment_analysis(text)
                companies.append({
                    'name': ticker.upper(),
                    'ticker': ticker.upper(),
                    'confidence': 0.9,  # Very high confidence for ticker symbols
                    'sentiment': sentiment,
                    'source': 'ticker_symbol'
                })
        
        return companies
    
    def _get_ticker_for_company(self, company_name: str) -> Optional[str]:
        """Get ticker symbol for a company name"""
        # Check our mapping first
        if company_name in self.company_mappings:
            return self.company_mappings[company_name]
        
        # Try to find exact matches
        for name, ticker in self.company_mappings.items():
            if name in company_name or company_name in name:
                return ticker
        
        # Could add API calls to financial data providers here
        return None
    
    def _analyze_sentiment_for_entity(self, text: str, entity) -> float:
        """Analyze sentiment specifically for an entity"""
        try:
            # Get the context around the entity
            entity_text = entity.name
            entity_start = text.lower().find(entity_text.lower())
            
            if entity_start != -1:
                # Get surrounding context (50 characters on each side)
                context_start = max(0, entity_start - 50)
                context_end = min(len(text), entity_start + len(entity_text) + 50)
                context = text[context_start:context_end]
                
                # Analyze sentiment of the context
                document = Document(
                    content=context,
                    type_=Document.Type.PLAIN_TEXT,
                    language='en'
                )
                
                response = self.language_client.analyze_sentiment(document=document)
                return response.document_sentiment.score
                
        except Exception as e:
            logger.error(f"Entity sentiment analysis failed: {e}")
        
        # Fallback to overall text sentiment
        return self._simple_sentiment_analysis(text)
    
    def _simple_sentiment_analysis(self, text: str) -> float:
        """Simple keyword-based sentiment analysis"""
        text_lower = text.lower()
        
        # Positive keywords
        positive_words = [
            'great', 'excellent', 'amazing', 'fantastic', 'wonderful', 'outstanding',
            'best', 'top', 'leading', 'successful', 'profitable', 'growing',
            'love', 'like', 'support', 'approve', 'endorse', 'recommend',
            'strong', 'powerful', 'innovative', 'revolutionary', 'breakthrough'
        ]
        
        # Negative keywords
        negative_words = [
            'terrible', 'awful', 'horrible', 'disaster', 'failure', 'bankrupt',
            'worst', 'bottom', 'failing', 'losing', 'declining', 'shrinking',
            'hate', 'dislike', 'oppose', 'reject', 'condemn', 'boycott',
            'weak', 'powerless', 'outdated', 'obsolete', 'broken'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate sentiment score (-1 to 1)
        total_words = positive_count + negative_count
        if total_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment))
    
    def _deduplicate_companies(self, companies: List[Dict]) -> List[Dict]:
        """Remove duplicate companies, keeping the highest confidence ones"""
        seen_tickers = set()
        unique_companies = []
        
        # Sort by confidence (highest first)
        sorted_companies = sorted(companies, key=lambda x: x.get('confidence', 0), reverse=True)
        
        for company in sorted_companies:
            ticker = company.get('ticker', '').upper()
            if ticker and ticker not in seen_tickers:
                seen_tickers.add(ticker)
                unique_companies.append(company)
        
        return unique_companies
    
    def get_company_info(self, ticker: str) -> Optional[Dict]:
        """Get additional company information using yfinance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0),
                'volume': info.get('volume', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get company info for {ticker}: {e}")
            return None
    
    def analyze_tweet_sentiment(self, tweet_text: str) -> Dict:
        """Analyze overall sentiment of a tweet"""
        if not self.language_client:
            return {
                'score': self._simple_sentiment_analysis(tweet_text),
                'magnitude': 0.0,
                'method': 'simple'
            }
        
        try:
            document = Document(
                content=tweet_text,
                type_=Document.Type.PLAIN_TEXT,
                language='en'
            )
            
            response = self.language_client.analyze_sentiment(document=document)
            sentiment = response.document_sentiment
            
            return {
                'score': sentiment.score,
                'magnitude': sentiment.magnitude,
                'method': 'google_cloud'
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'score': self._simple_sentiment_analysis(tweet_text),
                'magnitude': 0.0,
                'method': 'simple_fallback'
            }


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the analysis
    analyzer = AnalysisModern()
    
    # Test tweet
    test_tweet = "Apple is doing great! Their new iPhone is amazing. Tesla on the other hand is having problems."
    
    print("Analyzing tweet:", test_tweet)
    
    # Find companies
    companies = analyzer.find_companies(test_tweet)
    print(f"Found {len(companies)} companies:")
    
    for company in companies:
        print(f"- {company['name']} ({company['ticker']}): {company['sentiment']:.2f}")
    
    # Overall sentiment
    sentiment = analyzer.analyze_tweet_sentiment(test_tweet)
    print(f"Overall sentiment: {sentiment['score']:.2f} ({sentiment['method']})") 