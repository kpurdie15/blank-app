import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime

# --- 1. GLOBAL CONFIGURATION (Must be at the top) ---
# Broad Industry Feeds
MAJOR_FEEDS = {
    "Globe & Mail: Investing": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/investing/",
    "Globe & Mail: Business": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
    "Yahoo Finance: Top Stories": "https://finance.yahoo.com/news/rssindex"
}

# Company-Specific Newsrooms
WATCHLIST_FEEDS = {
    "VNP.TO (5N Plus)": "https://www.globenewswire.com/RssFeed/orgId/13361",
    "ATZ.TO (Aritzia)": "https://www.globenewswire.com/RssFeed/orgId/103681",
    "NFI.TO (NFI Group)": "https://www.globenewswire.com/RssFeed/orgId/6618",
    "CTS.TO (Converge)": "https://www.newswire.ca/rss/company/converge-technology-solutions-corp.rss"
}

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title="Equity Research Pro", layout="wide")
st.title("💼 Multi-Source Market Intelligence")

# --- 3. UTILITY FUNCTIONS ---
def fetch_feed(name, url):
    """Fetches and parses RSS entries into a standardized list."""
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:10]:
        results.append({
            "Source": name,
            "Date": entry.get('published', datetime.now().strftime('%b %d')),
            "Headline": entry.title,
            "Link": entry.link
        })
    return results

# --- 4. SIDEBAR & FILTERS ---
with st.sidebar:
    st.header("Intelligence Filters")
    # Search box for keywords like 'Defense' or 'Acquisition'
    search_query = st.text_input("🔍 Search Industry or Company", "").strip().lower()
    
    st.write("---")
    st.header("Watchlist Settings")
    selected_ticker = st.selectbox("Filter by Company", ["All"] + list(WATCHLIST_FEEDS.keys()))
    refresh = st.button("🔄 Refresh Data", use_container_width=True)

# --- 5. MAIN APP LOGIC ---
if refresh:
    all_news = []
    
    with st.spinner('Gathering intelligence...'):
        # Fetch broad industry news from Major Feeds
        for name, url in MAJOR_FEEDS.items():
            try:
                all_news.extend(fetch_feed(name, url))
            except Exception:
                pass
        
        # Fetch company-specific news
        if selected_ticker == "All":
            for name, url in WATCHLIST_FEEDS.items():
                try:
                    all_news.extend(fetch_feed(name, url))
                except Exception:
                    pass
        else:
            try:
                all_news.extend(fetch_feed(selected_ticker, WATCHLIST_FEEDS[selected_ticker]))
            except Exception:
                st.error(f"Could not reach feed for {selected_ticker}")

    if all_news:
        df = pd.DataFrame(all_news)
        
        # Apply Search Filter if user typed a keyword
        if search_query:
            # Case-insensitive search through headlines
            df = df[df['Headline'].str.lower().str.contains(search_query, na=False)]
        
        if not df.empty:
            st.subheader(f"Results: {search_query if search_query else 'All Headlines'}")
            st.dataframe(
                df, 
                column_config={"Link": st.column_config.LinkColumn("Full Article")},
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(f"No headlines found matching your criteria: '{search_query}'")
    else:
        st.warning("No data found. Please check your internet connection.")
else:
    st.info("Welcome! Use the sidebar to set your search criteria and click 'Refresh' to load data.")
