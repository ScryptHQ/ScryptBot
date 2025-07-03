"""
Modern trading module for ScryptBot
Modernized and maintained 2024
Uses yfinance for market data and simulates trading for safety
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yfinance as yf
import pandas as pd
from pytz import timezone

from config import (
    USE_REAL_MONEY, CASH_HOLD, LIMIT_FRACTION, ORDER_DELAY_S,
    TICKER_BLACKLIST, MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE,
    MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE
)

logger = logging.getLogger(__name__)

class TradingModern:
    """Modern trading system using yfinance and simulation"""
    
    def __init__(self):
        """Initialize the trading system"""
        self.market_tz = timezone('US/Eastern')
        self.portfolio = {
            'cash': 10000.0,  # Starting cash
            'positions': {},  # Current stock positions
            'history': []     # Trading history
        }
        self.logger = logging.getLogger(__name__)
        
    def make_trades(self, companies: List[Dict]) -> bool:
        """Execute trades based on company sentiment analysis"""
        if not companies:
            self.logger.warning("No companies to trade")
            return False
        
        # Check if market is open
        if not self.is_market_open():
            self.logger.info("Market is closed - simulating trades for next open")
        
        # Calculate available budget
        available_cash = self.portfolio['cash'] - CASH_HOLD
        if available_cash <= 0:
            self.logger.warning("Insufficient cash for trading")
            return False
        
        # Determine trading strategies
        strategies = []
        for company in companies:
            strategy = self.get_trading_strategy(company)
            if strategy['action'] != 'hold':
                strategies.append(strategy)
        
        if not strategies:
            self.logger.info("No actionable trading strategies")
            return False
        
        # Calculate budget per strategy
        budget_per_strategy = available_cash / len(strategies)
        
        # Execute trades
        success_count = 0
        for strategy in strategies:
            if self.execute_strategy(strategy, budget_per_strategy):
                success_count += 1
        
        self.logger.info(f"Executed {success_count}/{len(strategies)} strategies successfully")
        return success_count > 0
    
    def get_trading_strategy(self, company: Dict) -> Dict:
        """Determine trading strategy based on company sentiment"""
        ticker = company.get('ticker', '').upper()
        sentiment = company.get('sentiment', 0)
        name = company.get('name', 'Unknown')
        
        strategy = {
            'company': name,
            'ticker': ticker,
            'sentiment': sentiment,
            'action': 'hold',
            'reason': 'no action needed'
        }
        
        # Check blacklist
        if ticker in TICKER_BLACKLIST:
            strategy['reason'] = 'blacklisted ticker'
            return strategy
        
        # Determine action based on sentiment
        if sentiment > 0.1:  # Positive sentiment
            strategy['action'] = 'buy'
            strategy['reason'] = 'positive sentiment'
        elif sentiment < -0.1:  # Negative sentiment
            strategy['action'] = 'sell'
            strategy['reason'] = 'negative sentiment'
        else:
            strategy['reason'] = 'neutral sentiment'
        
        return strategy
    
    def execute_strategy(self, strategy: Dict, budget: float) -> bool:
        """Execute a trading strategy"""
        ticker = strategy['ticker']
        action = strategy['action']
        
        try:
            if action == 'buy':
                return self.buy_stock(ticker, budget)
            elif action == 'sell':
                return self.sell_stock(ticker, budget)
            else:
                self.logger.info(f"Holding {ticker}: {strategy['reason']}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to execute strategy for {ticker}: {e}")
            return False
    
    def buy_stock(self, ticker: str, budget: float) -> bool:
        """Buy stock using available budget"""
        try:
            # Get current stock price
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('currentPrice')
            
            if not current_price:
                self.logger.error(f"Could not get price for {ticker}")
                return False
            
            # Calculate quantity to buy
            quantity = int(budget / current_price)
            if quantity <= 0:
                self.logger.warning(f"Insufficient budget to buy {ticker}")
                return False
            
            # Calculate actual cost
            actual_cost = quantity * current_price
            
            # Check if we have enough cash
            if actual_cost > self.portfolio['cash']:
                self.logger.warning(f"Insufficient cash to buy {ticker}")
                return False
            
            # Execute the trade
            if USE_REAL_MONEY:
                self.logger.warning("REAL MONEY TRADING DISABLED - This is a simulation")
                # In a real implementation, you would place actual orders here
                # using a broker API like Alpaca, Interactive Brokers, etc.
            
            # Update portfolio
            self.portfolio['cash'] -= actual_cost
            
            if ticker in self.portfolio['positions']:
                # Add to existing position
                existing_quantity = self.portfolio['positions'][ticker]['quantity']
                existing_cost = self.portfolio['positions'][ticker]['cost']
                
                new_quantity = existing_quantity + quantity
                new_cost = existing_cost + actual_cost
                new_avg_price = new_cost / new_quantity
                
                self.portfolio['positions'][ticker] = {
                    'quantity': new_quantity,
                    'cost': new_cost,
                    'avg_price': new_avg_price
                }
            else:
                # New position
                self.portfolio['positions'][ticker] = {
                    'quantity': quantity,
                    'cost': actual_cost,
                    'avg_price': current_price
                }
            
            # Record trade
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker,
                'action': 'buy',
                'quantity': quantity,
                'price': current_price,
                'cost': actual_cost,
                'sentiment': 'positive'
            }
            self.portfolio['history'].append(trade_record)
            
            self.logger.info(f"Bought {quantity} shares of {ticker} at ${current_price:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to buy {ticker}: {e}")
            return False
    
    def sell_stock(self, ticker: str, budget: float) -> bool:
        """Sell stock (if we have it) or simulate short selling"""
        try:
            # Check if we have the stock
            if ticker in self.portfolio['positions']:
                # We have the stock, sell it
                position = self.portfolio['positions'][ticker]
                quantity = position['quantity']
                
                # Get current price
                stock = yf.Ticker(ticker)
                current_price = stock.info.get('currentPrice')
                
                if not current_price:
                    self.logger.error(f"Could not get price for {ticker}")
                    return False
                
                # Calculate sale value
                sale_value = quantity * current_price
                
                # Update portfolio
                self.portfolio['cash'] += sale_value
                del self.portfolio['positions'][ticker]
                
                # Record trade
                trade_record = {
                    'timestamp': datetime.now().isoformat(),
                    'ticker': ticker,
                    'action': 'sell',
                    'quantity': quantity,
                    'price': current_price,
                    'value': sale_value,
                    'sentiment': 'negative'
                }
                self.portfolio['history'].append(trade_record)
                
                self.logger.info(f"Sold {quantity} shares of {ticker} at ${current_price:.2f}")
                return True
            else:
                # We don't have the stock - simulate short selling
                self.logger.info(f"Simulating short sale of {ticker} (not implemented)")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to sell {ticker}: {e}")
            return False
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        total_value = self.portfolio['cash']
        
        for ticker, position in self.portfolio['positions'].items():
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.info.get('currentPrice', 0)
                position_value = position['quantity'] * current_price
                total_value += position_value
            except Exception as e:
                self.logger.error(f"Could not get current price for {ticker}: {e}")
        
        return total_value
    
    def get_portfolio_summary(self) -> Dict:
        """Get a summary of the current portfolio"""
        portfolio_value = self.get_portfolio_value()
        
        positions_summary = []
        for ticker, position in self.portfolio['positions'].items():
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.info.get('currentPrice', 0)
                position_value = position['quantity'] * current_price
                gain_loss = position_value - position['cost']
                gain_loss_pct = (gain_loss / position['cost']) * 100 if position['cost'] > 0 else 0
                
                positions_summary.append({
                    'ticker': ticker,
                    'quantity': position['quantity'],
                    'avg_price': position['avg_price'],
                    'current_price': current_price,
                    'value': position_value,
                    'gain_loss': gain_loss,
                    'gain_loss_pct': gain_loss_pct
                })
            except Exception as e:
                self.logger.error(f"Could not get summary for {ticker}: {e}")
        
        return {
            'cash': self.portfolio['cash'],
            'total_value': portfolio_value,
            'positions': positions_summary,
            'total_trades': len(self.portfolio['history'])
        }
    
    def is_market_open(self) -> bool:
        """Check if the US stock market is currently open"""
        now = datetime.now(self.market_tz)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check if it's within market hours
        market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
        market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def get_market_status(self) -> str:
        """Get current market status"""
        if self.is_market_open():
            return "open"
        else:
            return "closed"
    
    def get_stock_price(self, ticker: str) -> Optional[float]:
        """Get current stock price"""
        try:
            stock = yf.Ticker(ticker)
            return stock.info.get('currentPrice')
        except Exception as e:
            self.logger.error(f"Failed to get price for {ticker}: {e}")
            return None
    
    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """Get comprehensive stock information"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'ticker': ticker,
                'name': info.get('longName', ticker),
                'current_price': info.get('currentPrice'),
                'previous_close': info.get('previousClose'),
                'open': info.get('open'),
                'high': info.get('dayHigh'),
                'low': info.get('dayLow'),
                'volume': info.get('volume'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield'),
                'sector': info.get('sector'),
                'industry': info.get('industry')
            }
        except Exception as e:
            self.logger.error(f"Failed to get info for {ticker}: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the trading system
    trader = TradingModern()
    
    # Test companies
    test_companies = [
        {'name': 'Apple', 'ticker': 'AAPL', 'sentiment': 0.8},
        {'name': 'Tesla', 'ticker': 'TSLA', 'sentiment': -0.6},
        {'name': 'Microsoft', 'ticker': 'MSFT', 'sentiment': 0.3}
    ]
    
    print("Making trades...")
    success = trader.make_trades(test_companies)
    print(f"Trading success: {success}")
    
    # Get portfolio summary
    summary = trader.get_portfolio_summary()
    print(f"\nPortfolio Summary:")
    print(f"Cash: ${summary['cash']:.2f}")
    print(f"Total Value: ${summary['total_value']:.2f}")
    print(f"Total Trades: {summary['total_trades']}")
    
    if summary['positions']:
        print("\nPositions:")
        for pos in summary['positions']:
            print(f"- {pos['ticker']}: {pos['quantity']} shares @ ${pos['avg_price']:.2f}")
    
    # Market status
    print(f"\nMarket Status: {trader.get_market_status()}") 