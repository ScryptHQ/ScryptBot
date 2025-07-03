# Financial Juice Monitor Runner
# Optimized for @financialjuice (5-20 posts/day)

Write-Host "Starting Financial Juice Monitor" -ForegroundColor Green
Write-Host "Focus: @financialjuice (5-20 posts/day)" -ForegroundColor Cyan
Write-Host "Polling interval: 5 minutes" -ForegroundColor Yellow
Write-Host "=================================================="

# Check if Python is available
try {
    python --version
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.13+" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found. Please run setup_env.py first" -ForegroundColor Red
    exit 1
}

Write-Host "Environment ready" -ForegroundColor Green
Write-Host ""

# Run the financial juice monitor
Write-Host "Starting monitor..." -ForegroundColor Cyan
python main_financial_juice_focused.py

Write-Host ""
Write-Host "Monitor stopped" -ForegroundColor Yellow 