"""
financial_tool.py
------------------
Wraps yfinance so the Financial Agent can pull real market data (price,
market cap, P/E ratio, revenue growth, etc.) without needing a paid API key.
yfinance has no authentication requirement, which keeps the project easy
for anyone to run out of the box.
"""

import yfinance as yf


class FinancialDataTool:
    """Fetches and formats key financial metrics for a given stock ticker."""

    def get_metrics(self, ticker: str) -> dict:
        """
        Returns a dictionary of key financial metrics for `ticker`.
        Returns an empty dict (instead of raising) if the ticker is invalid
        or Yahoo Finance has no data for it — the agent handles that case
        by telling the user financial data wasn't available.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
                return {}

            return {
                "company_name": info.get("longName", ticker),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_margin": info.get("profitMargins"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "summary": info.get("longBusinessSummary", "")[:500],
            }
        except Exception as exc:
            print(f"[FinancialDataTool] Failed to fetch data for '{ticker}': {exc}")
            return {}
