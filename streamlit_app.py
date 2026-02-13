import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import urllib3

# This hides the 'Insecure Request' warning text from your app
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Equity Research News Feed", layout="wide")
st.title("🇨🇦 Canadian Small/Mid-Cap News Tracker")

# Your watchlist
watchlist = ["ATZ.TO", "NFI.TO", "LMN.V", "CTS.TO", "SYZ.TO"]

def get_ticker_news_bypass(ticker):
    """A more aggressive way to fetch news through corporate firewalls."""
    # We use a public search API that is often less restricted than Yahoo's main site
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}"
    
    # 'verify=False' is the magic key that ignores the SSL certificate error
    response = requests.get(url, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    data = response.json()
    
    processed_news = []
    if "news" in data:
        for item in data["news"]:
            processed_news.append({
                "Ticker": ticker,
                "Date": datetime.now().strftime('%Y-%m-%d'), # Simplified date
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
