import streamlit as st
import pandas as pd
import feedparser
import requests
import yfinance as yf
from datetime import datetime
import urllib3
import io

# 1. FIREWALL BYPASS: Force Python to ignore corporate SSL issues globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
session = requests.Session()
session.verify = False  # Tells all requests to ignore the 'Self-signed certificate' error

# 2. WATCHLIST CONFIGURATION: Official Website RSS Feeds
# These links point directly to each company's press release room
WATCHLIST_FEEDS = {
    "VNP.TO (5N Plus)": "https://www.globenewswire.com/RssFeed/orgId/13361",
    "ATZ.TO (Aritzia)": "https://www.globenewswire.com/RssFeed/orgId/103681",
    "NFI.TO (NFI Group)": "https://www.globenewswire.com/RssFeed/orgId/6618",
    "CTS.TO (Converge)": "https://www.newswire.ca/rss/company/converge-technology-solutions-corp.rss",
    "LMN.V (Lumine Group)": "https://www.globenewswire.com/RssFeed/orgId/160350",
    "SYZ.TO (Sylogist)": "https://www.newsfilecorp.com/rss/company/8367"
}

# --- PAGE SETUP ---
st.set_page_config(page_title="Equity Research Dashboard", layout="wide")
st.title("🗞️ Official Company Intelligence Dashboard")
st.subheader("Direct-from-source press releases & live market data")

# --- UTILITY FUNCTIONS ---
def get_rss_news(ticker_name, url):
    """Fetches the 5 most recent official company releases."""
    feed = feedparser.parse(url)
    processed = []
    for entry in feed.entries[:5]:
        processed.append({
            "Ticker": ticker_name,
            "Date": entry.get('published', datetime.now().strftime('%Y-%m-%d')),
            "Headline": entry.title,
            "Source": "Official Press Release",
            "URL": entry.link
        })
    return processed

def get_stock_price(ticker_code):
    """Fetches stock price using yfinance with SSL bypass session."""
    try:
        stock = yf.Ticker(ticker_code, session=session)
        # Fetch only the most recent close price
        history = stock.history(period="1d")
        if not history.empty:
            return history['Close'].iloc[-1]
        return "N/A"
    except:
        return "Locked"

# --- MAIN APP LOGIC ---
with st.sidebar:
    st.header("Dashboard Controls")
    refresh = st.button("🔄 Refresh All Feeds", use_container_width=True)
    st.write("---")
    st.info("Bypassing firewall using unverified SSL session.")

if refresh:
    all_news = []
    prices = {}
    
    with st.spinner('Accessing corporate newsrooms and market data...'):
        for name, url in WATCHLIST_FEEDS.items():
            # 1. Fetch Company News
            try:
                all_news.extend(get_rss_news(name, url))
            except:
                st.error(f"Failed to reach newsroom for {name}")
            
            # 2. Fetch Market Price (extracting Ticker code like VNP.TO)
            ticker_code = name.split(' ')[0]
            prices[ticker_code] = get_stock_price(ticker_code)

    if all_news:
        # A. Display Market Metrics
        st.subheader("Live Market Snapshots")
        cols = st.columns(len(prices))
        for i, (ticker, price) in enumerate(prices.items()):
            if isinstance(price, float):
                cols[i].metric(ticker, f"${price:.2f}")
            else:
                cols[i].metric(ticker, price)

        # B. Display News Table
        st.subheader("Latest Official Press Releases")
        df = pd.DataFrame(all_news)
        
        # C. Add Download Button for Export
        @st.cache_data
        def convert_df(df_to_save):
            return df_to_save.to_csv(index=False).encode('utf-8')
        
        csv_data = convert_df(df)
        st.download_button(
            label="📥 Download Research Report (CSV)",
            data=csv_data,
            file_name=f"equity_research_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )

        st.dataframe(
            df, 
            column_config={"URL": st.column_config.LinkColumn("Full Article Link")},
            hide_index=True, 
            use_container_width=True
        )
    else:
        st.warning("No data found. Check your P: drive internet permissions.")
else:
    st.info("Welcome! Please click the 'Refresh All Feeds' button in the sidebar to load the latest company data.")
