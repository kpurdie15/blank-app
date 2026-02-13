import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import re
from concurrent.futures import ThreadPoolExecutor # For parallel speed

# --- 1. GLOBAL CONFIGURATION ---
INDUSTRY_FEEDS = {
    "Globe & Mail: Business": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
    "Financial Post": "https://financialpost.com/feed/",
    "CBC Business": "https://www.cbc.ca/webfeed/rss/rss-business",
    "BNN Bloomberg": "https://www.bnnbloomberg.ca/rss/investing"
}

WATCHLIST_FEEDS = {
    "VNP.TO (5N Plus)": "https://www.globenewswire.com/RssFeed/orgId/13361",
    "ATZ.TO (Aritzia)": "https://www.globenewswire.com/RssFeed/orgId/103681",
    "NFI.TO (NFI Group)": "https://www.globenewswire.com/RssFeed/orgId/6618",
    "CTS.TO (Converge)": "https://www.newswire.ca/rss/company/converge-technology-solutions-corp.rss"
}

# --- 2. THE PERFORMANCE ENGINE ---

# We cache this data for 10 minutes (600 seconds) so it's instant on refresh
@st.cache_data(ttl=600) 
def fetch_all_intelligence():
    """Fetches all sources in parallel to maximize speed."""
    all_sources = {**INDUSTRY_FEEDS, **WATCHLIST_FEEDS}
    
    def get_single_feed(name_url):
        name, url = name_url
        try:
            feed = feedparser.parse(url)
            return [{
                "Source": name,
                "Date": entry.get('published', datetime.now().strftime('%b %d')),
                "Headline": entry.title,
                "Link": entry.link
            } for entry in feed.entries[:10]]
        except:
            return []

    # 'ThreadPoolExecutor' acts like 20 people fetching news at once
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(get_single_feed, all_sources.items()))
    
    # Flatten the list of lists into one single list
    return [item for sublist in results for item in sublist]

# --- 3. PAGE SETUP & UI ---
st.set_page_config(page_title="High-Speed Market Intel", layout="wide")
st.title("🏛️ Professional Market Intelligence Dashboard")

with st.sidebar:
    st.header("Search Parameters")
    search_query = st.text_input("🔍 Keywords (separate with commas)", "Dividend, Acquisition, Q4")
    
    # A single button now just triggers the display of the cached data
    refresh = st.button("🔄 Force New Intel Sweep", use_container_width=True)
    if refresh:
        st.cache_data.clear() # Clears the 10-minute memory to get fresh news

# --- 4. DATA PROCESSING ---
all_news = fetch_all_intelligence()

if all_news:
    df = pd.DataFrame(all_news).drop_duplicates(subset=['Headline'])
    
    # Instant Filtering (Doesn't require a network fetch)
    if search_query:
        keywords = [k.strip().lower() for k in search_query.split(',')]
        pattern = '|'.join(map(re.escape, keywords))
        df = df[df['Headline'].str.contains(pattern, case=False, na=False)]
    
    st.subheader(f"Current Intelligence: {len(df)} relevant headlines")
    st.dataframe(
        df, 
        column_config={"Link": st.column_config.LinkColumn("View Source")},
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("Gathering initial data... Please wait.")
