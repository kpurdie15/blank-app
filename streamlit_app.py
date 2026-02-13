import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime

# Updated to use broad, reliable Canadian business sections
MAJOR_CANADIAN_FEEDS = {
    "Globe & Mail: Investing": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/investing/",
    "Globe & Mail: Business": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
    "CBC Business News": "https://www.cbc.ca/webfeed/rss/rss-business",
    "Financial Post": "https://financialpost.com/category/business/feed/"
}

# The names/tickers we will look for within those broad feeds
WATCHLIST_KEYWORDS = ["Aritzia", "ATZ", "NFI", "5N Plus", "VNP", "Converge", "CTS"]
}

# --- 2. PAGE SETUP ---
st.set_page_config(page_title="Equity Research Feed", layout="wide")
st.title("🇨🇦 Ticker-Specific News Feed")

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Filter Criteria")
    # Selection determines which company we pull for
    target_company = st.selectbox("Select Stock to Monitor", ["All Watchlist"] + list(WATCHLIST_FEEDS.keys()))
    
    # Optional: Keywords to look for within those company feeds
    keyword_filter = st.text_input("Additional Keyword (Optional)", "").strip().lower()
    
    refresh = st.button("Refresh News", use_container_width=True)

# --- 4. DATA FETCHING ---
def fetch_news(name, url):
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:15]:
        results.append({
            "Ticker": name.split(' ')[0], # Extracts 'VNP.TO'
            "Date": entry.get('published', datetime.now().strftime('%b %d')),
            "Headline": entry.title,
            "Link": entry.link
        })
    return results

if refresh:
    all_news = []
    
    with st.spinner('Pulling official releases...'):
        if target_company == "All Watchlist":
            for name, url in WATCHLIST_FEEDS.items():
                all_news.extend(fetch_news(name, url))
        else:
            all_news.extend(fetch_news(target_company, WATCHLIST_FEEDS[target_company]))

    if all_news:
        df = pd.DataFrame(all_news)
        
        # Apply the keyword filter if one was entered
        if keyword_filter:
            df = df[df['Headline'].str.lower().str.contains(keyword_filter, na=False)]
            
        if not df.empty:
            st.dataframe(
                df, 
                column_config={"Link": st.column_config.LinkColumn("Article")},
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning(f"No news found matching '{keyword_filter}' for these stocks.")
    else:
        st.error("Could not retrieve news. Check your connection.")
else:
    st.info("Select a stock and click 'Refresh' to see official news.")
