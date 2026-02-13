import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import urllib3
import time  # Add this at the top with other imports

# Your watchlist
watchlist = ["VNP.TO", "NEO.TO", "LMN.V", "CTS.TO", "SYZ.TO"]

# ... inside your button click logic ...
for ticker in watchlist:
    try:
        ticker_news = get_ticker_news_bypass(ticker)
        all_news.extend(ticker_news)
        time.sleep(1.5)  # Wait 1.5 seconds between each ticker
    except Exception as e:
        st.error(f"Network Block on {ticker}: Connection reset.")

# This hides the 'Insecure Request' warning text from your app
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Equity Research News Feed", layout="wide")
st.title("🇨🇦 Canadian Small/Mid-Cap News Tracker")

def get_ticker_news_bypass(ticker):
    """Refined news fetcher that filters for relevancy."""
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}"
    response = requests.get(url, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    data = response.json()
    
    processed_news = []
    if "news" in data:
        for item in data["news"]:
            # --- RELEVANCY FILTER ---
            # 1. Check if the ticker is specifically mentioned in the 'relatedTickers' metadata
            related = item.get('relatedTickers', ["VNP.TO", "NEO.TO", "LMN.V", "CTS.TO", "SYZ.TO"])
            
            # 2. Check if the ticker or a keyword is in the title
            title = item.get('title', '').upper()
            clean_ticker = ticker.split('.')[0] # Changes 'VNP.TO' to 'VNP'
            
            if clean_ticker in related or clean_ticker in title:
                processed_news.append({
                    "Ticker": ticker,
                    "Date": datetime.now().strftime('%Y-%m-%d'),
                    "Headline": item.get('title'),
                    "Source": item.get('publisher'),
                    "URL": item.get('link')
                })
    return processed_news

# --- APP LOGIC ---
if st.button('Refresh News Feed'):
    all_news = []
    with st.spinner('Fetching data through firewall...'):
        for ticker in watchlist:
            try:
                ticker_news = get_ticker_news_bypass(ticker)
                all_news.extend(ticker_news)
            except Exception as e:
                st.error(f"Network Block on {ticker}: Connection reset by firewall.")

    if all_news:
        df = pd.DataFrame(all_news)
        st.dataframe(df, column_config={"URL": st.column_config.LinkColumn("Article")}, 
                     hide_index=True, use_container_width=True)
    else:
        st.warning("The firewall is still blocking the connection. You may need to use a mobile hotspot.")
else:
    st.info("Click 'Refresh' to bypass firewall and load news.")
