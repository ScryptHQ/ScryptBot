# ScryptBot

ScryptBot is an AI-powered bot that monitors financial news (via RSS feeds and @financialjuice), analyzes headlines using GPT, and posts actionable insights and chart screenshots to X (Twitter).

## Features
- Monitors FinancialJuice RSS feed and @financialjuice tweets
- Analyzes headlines with AI for sentiment, instrument, and action
- Automatically posts to X (Twitter) with TradingView chart screenshots
- Supports custom ticker extraction and macro instruments

## Setup
1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/scryptbot.git
   cd scryptbot
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Copy `env_example.txt` to `.env` and fill in your Twitter API and OpenAI credentials.
   - Or run the setup script:
     ```sh
     python setup_env.py
     ```
4. **Run the bot:**
   - For RSS feed monitoring and posting:
     ```sh
     python main_financialjuice_rss_ai.py
     ```
   - For @financialjuice tweet monitoring:
     ```sh
     python main_financial_juice_ai.py
     ```

## Screenshots
Chart screenshots are saved in the `Screenshots/` directory and posted with each actionable tweet.

## Security
- No API keys or secrets are stored in the repository.
- Use your own `.env` file for credentials.

## License
MIT License

---

*This project is not affiliated with Twitter/X, TradingView, or FinancialJuice.*
