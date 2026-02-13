import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime

# --- ADD SEARCH CRITERIA TO SIDEBAR ---
with st.sidebar:
    st.header("Intelligence Filters")
    # This is where you type 'Defense', 'Acquisition', or a ticker
    search_query = st.text_input("🔍 Search Industry or Company", "").strip().lower()
    refresh = st.button("🔄 Refresh Data", use_container_width=True)

if refresh:
    all_news = []
    with st.spinner('Filtering data by criteria...'):
        # 1. Fetch data as before...
        for name, url in WATCHLIST_FEEDS.items():
            try:
                news_items = get_rss_news(name, url)
                all_news.extend(news_items)
            except: pass

    if all_news:
        df = pd.DataFrame(all_news)
        
        # --- THE FILTERING LOGIC ---
        if search_query:
            # Only keep headlines that contain your search word
            df = df[df['Headline'].str.lower().contains(search_query)]
        
        if not df.empty:
            st.subheader(f"Results for: '{search_query if search_query else 'All Headlines'}'")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No headlines found matching '{search_query}'.")

# --- CONFIGURATION ---
st.set_page_config(page_title="Equity Research Pro", layout="wide")
st.title("💼 Multi-Source Market Intelligence")

# 1. Broad Industry Feeds (Globe & Mail / Yahoo)
MAJOR_FEEDS = {
    "Globe & Mail: Investing": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/investing/",
    "Globe & Mail: Business": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
    "Yahoo Finance: Top Stories": "https://finance.yahoo.com/news/rssindex"
}

# 2. Company-Specific Newsrooms
COMPANY_FEEDS = {
    "VNP.TO (5N Plus)": "https://www.globenewswire.com/RssFeed/orgId/13361",
    "ATZ.TO (Aritzia)": "https://www.globenewswire.com/RssFeed/orgId/103681",
    "NFI.TO (NFI Group)": "https://www.globenewswire.com/RssFeed/orgId/6618",
    "CTS.TO (Converge)": "https://www.newswire.ca/rss/company/converge-technology-solutions-corp.rss"
}

def fetch_feed(name, url, is_ticker=False):
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

# --- UI LAYOUT ---
col1, col2 = st.columns([1, 3])

with col1:
    st.header("Watchlist")
    selected_ticker = st.selectbox("Filter by Company", ["All"] + list(COMPANY_FEEDS.keys()))
    refresh = st.button("🔄 Refresh Data")

if refresh:
    all_news = []
    
    # Fetch broad industry news
    for name, url in MAJOR_FEEDS.items():
        all_news.extend(fetch_feed(name, url))
        
    # Fetch specific company news
    if selected_ticker == "All":
        for name, url in COMPANY_FEEDS.items():
            all_news.extend(fetch_feed(name, url, is_ticker=True))
    else:
        all_news.extend(fetch_feed(selected_ticker, COMPANY_FEEDS[selected_ticker], is_ticker=True))

    if all_news:
        df = pd.DataFrame(all_news)
        st.dataframe(
            df, 
            column_config={"Link": st.column_config.LinkColumn("Full Article")},
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No data found. Check your internet connection.")
