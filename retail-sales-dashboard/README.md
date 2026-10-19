# Retail Sales Analytics Dashboard

A Streamlit dashboard built for the Sample Superstore retail sales dataset.

## Features
- KPI cards for sales, profit, orders, units sold, and profit margin
- Interactive date, region, category, customer segment, and shipping filters
- Interactive monthly trend selector (Sales, Profit, Quantity, or Average Discount)
- Monthly sales trend
- Sales by category and sub-category
- Profit by region
- Top 10 products by profit
- Customer segment breakdown
- Searchable transaction table and CSV export

## Run locally
1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Create/activate a virtual environment if you want.
4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Start the app:
   ```bash
   python -m streamlit run app.py
   ```

The CSV file is included in this project folder. The app supports UTF-8 and cp1252 encodings.

## Deploy to Streamlit Community Cloud
1. Upload `app.py`, `requirements.txt`, and `Sample - Superstore(1).csv` to a GitHub repository.
2. Go to https://share.streamlit.io/
3. Create a new app, select your repository and branch, and set the main file path to `app.py`.
4. Deploy.
