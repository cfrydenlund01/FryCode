def get_analysis_prompt(data: dict) -> str:
    """
    Constructs a detailed prompt for Mistral 7B to analyze stock data
    and provide a structured investment recommendation.

    Args:
        data (dict): A dictionary containing market and user data:
            - 'ticker' (str): Stock ticker.
            - 'real_time_quote' (dict): Current price, volume, etc.
            - 'historical_data' (list): Daily/weekly OHLCV data.
            - 'sentiment_data' (dict): News sentiment, analyst ratings (if E*Trade provides).
            - 'user_risk_profile' (str): 'Low', 'Medium', or 'High'.

    Returns:
        str: The structured prompt for Mistral.
    """
    ticker = data.get('ticker', 'N/A')
    real_time_quote = data.get('real_time_quote', {})
    historical_data = data.get('historical_data', [])
    sentiment_data = data.get('sentiment_data', {})
    user_risk_profile = data.get('user_risk_profile', 'Medium')

    prompt = f"""
    Analyze the following stock data for {ticker} and provide a structured investment recommendation.
    Focus on pattern recognition (technical breakouts, reversals, momentum setups), profit maximization, and strict risk management.
    The recommendation must adhere to the user's risk profile: {user_risk_profile}.
    If a recommendation's risk level exceeds the user's profile, DO NOT recommend it.

    ---
    Market Data for {ticker}:

    Real-time Quote:
    Last Price: {real_time_quote.get('lastPrice', 'N/A')}
    Change (%): {real_time_quote.get('changePct', 'N/A')}
    Volume: {real_time_quote.get('volume', 'N/A')}
    Bid: {real_time_quote.get('bid', 'N/A')}
    Ask: {real_time_quote.get('ask', 'N/A')}
    High: {real_time_quote.get('high', 'N/A')}
    Low: {real_time_quote.get('low', 'N/A')}

    Historical Data (last few days/weeks, if available, simplified):
    """
    if historical_data:
        for i, entry in enumerate(historical_data[-5:]): # Last 5 entries for brevity
            prompt += f"\n  Day {i+1}: Date={entry.get('date')}, Open={entry.get('open')}, High={entry.get('high')}, Low={entry.get('low')}, Close={entry.get('close')}, Volume={entry.get('volume')}"
    else:
        prompt += "\n  No historical data available or provided."

    prompt += f"""

    Sentiment Data (if available):
    Earnings News: {sentiment_data.get('earningsNews', 'N/A')}
    Market Sentiment (general): {sentiment_data.get('marketSentiment', 'N/A')}
    Analyst Ratings: {sentiment_data.get('analystRatings', 'N/A')}

    ---
    Your Task:
    1.  **Analyze**: Identify significant technical patterns (e.g., strong trends, support/resistance, breakouts, reversals, momentum indicators like RSI, MACD if implicitly inferable from price/volume), and integrate sentiment.
    2.  **Evaluate Risk**: Assign a clear Risk Level (Low, Medium, High) to your recommendation.
        -   **Low Risk**: Stable stock, strong fundamentals, clear bullish/bearish signal with minimal volatility, consistent positive sentiment, clear stop-loss opportunities.
        -   **Medium Risk**: Moderate volatility, potential for good returns but also notable downsides, mixed signals requiring careful management.
        -   **High Risk**: High volatility, speculative play, strong but unconfirmed signals, significant potential for both gains and losses.
    3.  **Adhere to User Risk Profile**: If your determined 'Risk Level' for the recommendation is HIGHER than the user's '{user_risk_profile}' profile, then output 'Suggested Action: HOLD' with a 'Reasoning Summary' explaining why it exceeds the risk tolerance. Otherwise, proceed with BUY/SELL/HOLD.
    4.  **Determine Time Horizon**: Based on the pattern strength and expected catalyst, infer the ideal holding period: Short-term (days), Swing (weeks), Long-term (months).
    5.  **Structure Output**: Provide the recommendation in the exact format below, with each field on a new line. Do not include any other text before or after this structured output.

    ---
    Recommendation Format:
    Ticker: [Ticker Symbol]
    Confidence: [%, e.g., 85%]
    Risk Level: [Low/Medium/High]
    Suggested Action: [BUY/SELL/HOLD]
    Expected Time Horizon: [Short-term (days)/Swing (weeks)/Long-term (months)]
    Reasoning Summary: [Concise explanation based on technical signals, sentiment insights, and rationale for time horizon. Max 2-3 sentences.]
    """
    return prompt