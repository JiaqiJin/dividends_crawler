import pandas as pd
from yahooquery import search

class Dividend:
    def __init__(self, company, ex_date, pay_date, div_percent, amount, month, ticker=None):
        self.company = company
        self.ex_date = ex_date
        self.pay_date = pay_date
        self.div_percent = div_percent
        self.amount = amount
        self.month = month  # Store the month for reference
        self.ticker = ticker  # Store ticker symbol

    def __repr__(self):
        return f"Dividend({self.company}, {self.ex_date}, {self.pay_date}, {self.div_percent}, {self.amount}, {self.month}, {self.ticker})"

class DividendTracker:
    def __init__(self, file_path):
        self.file_path = file_path
        self.dividends_by_month = {}
        self.load_data()

    def load_data(self):
        """Loads data from the Excel file and organizes it by month."""
        sheets = pd.read_excel(self.file_path, sheet_name=None)  # Read all sheets
        
        for month, df in sheets.items():
            if not df.empty:  # Ensure sheet has data
                self.dividends_by_month[month] = []
                for _, row in df.iterrows():
                    company = row["Company"]
                    ticker = self.get_ticker(company)
                    dividend = Dividend(company, row["Ex-Date"], row["Pay Date"], row["Div.%"], row["Amount"], month, ticker)
                    self.dividends_by_month[month].append(dividend)
    
    def get_ticker(self, company_name):
        """Searches for a company's ticker using Yahoo Finance."""
        print(f"Company name: {company_name}")
        results = search(company_name)
        if results and "quotes" in results:
            for quote in results["quotes"]:
                if "symbol" in quote:
                    return quote["symbol"]
        return None
    
    def get_first_company_per_month(self):
        """Returns the first company in each month's dividend list."""
        return {month: dividends[0] for month, dividends in self.dividends_by_month.items() if dividends}

    def get_record_counts(self):
        """Returns the number of companies per month."""
        return {month: len(dividends) for month, dividends in self.dividends_by_month.items()}

    def get_total_records(self):
        """Returns the total number of records across all months."""
        return sum(len(dividends) for dividends in self.dividends_by_month.values())

if __name__ == "__main__":
    file_path = "dividends_2025.xlsx"  # Update with actual path if needed
    tracker = DividendTracker(file_path)
    
    print("\nOne company from each month:")
    for month, dividend in tracker.get_first_company_per_month().items():
        print(f"{month}: {dividend}")
    
    print("\nTotal number of records for each month:")
    for month, count in tracker.get_record_counts().items():
        print(f"{month}: {count} companies")
    
    print(f"\nTotal records across all months: {tracker.get_total_records()}")