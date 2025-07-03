#!/usr/bin/env python3
"""
ScryptBot: TradingView Chart Screenshot Utility
Generates and saves chart screenshots for use in ScryptBot posts.
(C) 2024-present ScryptBot Team
"""
import sys
from playwright.sync_api import sync_playwright
import time
import os
from PIL import Image

SCREENSHOT_DIR = 'screenshots'
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def save_screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, name)
    page.screenshot(path=path)
    print(f"Saved screenshot: {path}")
    return path

def crop_chart_image(input_path, output_path):
    # These coordinates are (left, upper, right, lower)
    crop_box = (55, 42, 930, 612)  # User-specified for perfect chart crop
    img = Image.open(input_path)
    cropped = img.crop(crop_box)
    cropped.save(output_path)
    print(f"Cropped chart image saved as: {output_path}")

def is_valid_tradingview_symbol(symbol):
    url = f"https://www.tradingview.com/chart/?symbol={symbol}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        time.sleep(5)
        # Check for the 'invalid symbol' ghost by alt text or text content
        invalid = False
        try:
            # The ghost image usually has alt text 'Invalid symbol' or similar
            if page.locator('text="Invalid symbol"').count() > 0:
                invalid = True
            # Or check for the ghost icon by selector
            if page.locator('img[alt="Invalid symbol"]').count() > 0:
                invalid = True
        except Exception:
            pass
        browser.close()
        return not invalid

def screenshot_tradingview_chart(ticker='AAPL', timeframe='1H', out_file=None):
    url = f"https://www.tradingview.com/chart/?symbol={ticker.upper()}"
    out_file = out_file or f"tradingview_{ticker}_{timeframe}.png"
    with sync_playwright() as p:
        print("Launching browser in headless mode for background operation...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        print(f"Navigating to {url}")
        page.goto(url)
        time.sleep(5)  # Let chart render
        for popup_text in ["Got it", "Accept all", "Sign in", "Maybe later", "No, thanks"]:
            try:
                page.locator(f'button:has-text("{popup_text}")').click(timeout=2000)
                print(f"Closed popup: {popup_text}")
            except:
                pass
        # Click the '5D' button to set the chart timeframe
        try:
            page.locator('button:has-text("5D")').click(timeout=3000)
            print("Clicked 5D button for 5-day chart.")
            time.sleep(2)  # Wait for chart to update
        except Exception as e:
            print(f"Could not click 5D button: {e}")
        # Take full page screenshot
        screenshot_path = save_screenshot(page, out_file)
        # Crop to chart area
        cropped_path = os.path.join(SCREENSHOT_DIR, 'cropped_' + out_file)
        crop_chart_image(screenshot_path, cropped_path)
        browser.close()

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'AAPL'
    timeframe = sys.argv[2] if len(sys.argv) > 2 else '1H'
    screenshot_tradingview_chart(ticker, timeframe) 