from DividendTracker import DividendTracker
import yfinance as yf
from yahooquery import search

if __name__ == "__main__":
    file_path = "dividends_2025.xlsx"  # Ensure this file is in your project directory
    tracker = DividendTracker(file_path)  # Initialize the tracker

    # Print one company from each month with ticker symbol
    print("\nOne company from each month with Ticker:")
    for month, dividend in tracker.get_first_company_per_month().items():
        print(f"{month}: {dividend.company} | Ticker: {dividend.ticker}")

    # Print number of records per month
    print("\nTotal number of records for each month:")
    for month, count in tracker.get_record_counts().items():
        print(f"{month}: {count} companies")

    # Print total records across all months
    print(f"\nTotal records across all months: {tracker.get_total_records()}")
    
    # print(f"\nTotal records across all months: {tracker.get_total_records()}")
    # Fetch data for a specific stock (e.g., Apple - AAPL)
#     ticker = "919913"
#     stock = yf.Ticker(ticker)

#    # Search for a company name
#     company_name = "Derayah Financial - Derayah Reit Fund"
#     results = search(company_name)

#     # Extract possible tickers
#     if results and "quotes" in results:
#         for quote in results["quotes"]:
#             print(f"Company: {quote['shortname']} | Ticker: {quote['symbol']}")
#     else:
#         print("No ticker found.")

