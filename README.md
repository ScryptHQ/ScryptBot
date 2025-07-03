# ScryptBot

**ScryptBot** is an AI-powered, fully automated financial news and signal bot. It monitors real-time news from FinancialJuice (RSS and Twitter), applies advanced NLP analysis (via OpenAI GPT), extracts actionable trading signals, and posts insights—complete with TradingView chart screenshots—directly to X (Twitter).

---

## 🚀 Features

- **Real-Time News Monitoring:**  
  Tracks FinancialJuice RSS headlines and @financialjuice tweets for market-moving news.

- **AI-Driven Analysis:**  
  Uses GPT-based NLP to summarize headlines, extract sentiment, and identify actionable instruments.

- **Signal Generation:**  
  Detects buy/sell/hold signals and expected impact for stocks, indices, and macro assets.

- **Automated Charting:**  
  Captures and posts TradingView chart screenshots for each actionable ticker.

- **Auto-Posting to X (Twitter):**  
  Publishes insights and charts to your X account using the Twitter API.

- **Modular & Extensible:**  
  Easily adapt to new news sources, analysis models, or posting platforms.

---

## 🛠️ Quickstart

### 1. Clone the Repository

```sh
git clone https://github.com/ScryptHQ/ScryptBot.git
cd ScryptBot
```

### 2. Install Dependencies

```sh
pip install -r requirements.txt
# For chart screenshots, also run:
playwright install
```

### 3. Configure Environment

- Copy `env_example.txt` to `.env` and fill in your API keys (Twitter, OpenAI).
- Or run the setup script:
  ```sh
  python setup_env.py
  ```

### 4. Run ScryptBot

- **Monitor FinancialJuice RSS and auto-post to X:**
  ```sh
  python main_financialjuice_rss_ai.py
  ```
- **Monitor @financialjuice tweets:**
  ```sh
  python main_financial_juice_ai.py
  ```

---

## 📊 Example Output

```
🚨 US Government payrolls actual 73k, beating forecasts.
🟢 Positive | 💰 Buy signal
Current $SPY price: $620.45
Expected impact: +1%

Positive job data may boost market sentiment.
$SPY
#StockMarket #Macro
[Chart Screenshot Attached]
```

---

## 🧩 Project Structure

```
ScryptBot/
│
├── bot/           # Core modules and main scripts
├── data/          # Processed data, logs, and state
├── scripts/       # Setup and utility scripts
├── tests/         # Automated tests
├── Screenshots/   # Chart images
├── .github/       # Issue/PR templates, CI workflows
├── README.md
├── LICENSE
├── requirements.txt
├── env_example.txt
└── .gitignore
```

---

## 🧪 Testing

Run all tests with:

```sh
pytest tests/
```

---

## 🤝 Contributing

We welcome contributions!
- For bug reports, use the Issues tab and fill out the template.
- For new features or fixes, fork the repo, create a branch, and submit a pull request.

See `.github/` for templates and CI setup.

---

## 🔒 Security

- **No API keys or secrets are stored in the repository.**
- Use your own `.env` file for credentials (never commit it).

---

## 📄 License

MIT License © 2025 ScryptBot Team

---

**ScryptBot is not affiliated with Twitter/X, TradingView, or FinancialJuice. For research and educational use only.**
