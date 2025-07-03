from twitter_modern_v2_only import TwitterV2Only

FINANCIAL_JUICE_ID = '381696140'
twitter = TwitterV2Only()
try:
    tweets = twitter.get_user_tweets(FINANCIAL_JUICE_ID, max_results=5)
    print("Fetched tweets:", tweets)
    if not tweets:
        print("No tweets returned. If you are rate limited or there is an API error, check the logs or error details below.")
except Exception as e:
    print("Exception occurred while fetching tweets:", e)
    import traceback
    traceback.print_exc() 