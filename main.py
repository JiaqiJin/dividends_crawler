import yfinance as yf

# Define the ticker symbol (example: 'AAPL' for Apple)
ticker_symbol = 'KBDC'  # Replace with a valid ticker symbol for testing

try:
    # Create a Ticker object
    ticker = yf.Ticker(ticker_symbol)
    
    # Fetch company information
    company_info = ticker.info

    if company_info:
        # Print company information
        print(company_info)
    else:
        print(f"No data found for ticker symbol: {ticker_symbol}")

except ValueError as e:
    print(f"Invalid value error: {e}")
except KeyError as e:
    print(f"Key error: {e}")
except AttributeError as e:
    print(f"Attribute error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
