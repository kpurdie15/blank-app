import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import re

# --- 1. GLOBAL CONFIGURATION (Expanded Source List) ---
# Major Canadian Business Outlets
INDUSTRY_FEEDS = {
    "Globe & Mail: Business": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
    "Financial Post: Top Stories": "https://financialpost.com/feed/",
    "CBC Business News": "https://www.cbc.ca/webfeed/rss/rss-business",
    "Yahoo Finance Canada": "https://ca.finance.yahoo.com/news/rssindex",
    "BNN Bloomberg: Investing": "https://www.bnnbloomberg.ca/rss/investing"
}

# Targeted Press Release Subjects (TMX/GlobeNewswire)
SUBJECT_FEEDS = {
    "M&A Activity": "https://www.globenewswire.com/RssFeed/subject/46/Mergers%20and%20Acquisitions",
    "Earnings & Operating Results": "https://www.globenewswire.com/RssFeed/subject/28/Earnings%20Releases%20and%20Operating%20Results",
    "Public Companies (General)": "https://www.globenewswire.com/RssFeed/subject/5/Public%20Companies"
}

# Your Core Watchlist (Official Company Newsrooms)
WATCHLIST_FEEDS = {
    "VNP.TO (5N Plus)": "https://www.globenewswire.com/RssFeed/orgId/13361",
    "ATZ.TO (Aritzia)": "https://www.globenewswire.com/RssFeed/orgId/103681",
    "NFI.TO (NFI Group)": "https://www.globenewswire.com/RssFeed/orgId/6618",
    "CTS.TO (Converge)": "https://www.newswire.ca/rss/company/converge-technology-solutions-corp.rss"
}

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title="Market Intelligence Pro", layout="wide")
st.title("🏛️ Professional Canadian Market Intelligence")

# --- 3. UTILITY FUNCTIONS ---
def fetch_feed(name, url, limit=15):
    """Fetches RSS entries and formats them for a DataFrame."""
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:limit]:
        results.append({
            "Source": name,
            "Date": entry.get('published', datetime.now().strftime('%b %d')),
            "Headline": entry.title,
            "Link": entry.link
        })
    return results

# --- 4. SIDEBAR & FILTERS ---
with st.sidebar:
    st.header("Search Parameters")
    # Supports multiple keywords: e.g., 'Defense, Contract, Boeing'
    search_query = st.text_input("🔍 Keywords (separate with commas)", "Dividend, Acquisition, Q4").strip()
    
    st.write("---")
    st.header("Watchlist Settings")
    selected_ticker = st.selectbox("Company Specific", ["All Companies"] + list(WATCHLIST_FEEDS.keys()))
    
    st.write("---")
    st.checkbox("Include Broad Industry News", value=True, key="use_industry")
    st.checkbox("Include M&A / Earnings Feeds", value=True, key="use_subjects")
    
    refresh = st.button("🔄 Execute Intel Sweep", use_container_width=True)

# --- 5. MAIN APP LOGIC ---
if refresh:
    all_news = []
    
    with st.spinner('Scouring Canadian business outlets and wires...'):
        # 1. Fetch from Company Newsrooms
        if selected_ticker == "All Companies":
            for name, url in WATCHLIST_FEEDS.items():
                all_news.extend(fetch_feed(name, url))
        else:
            all_news.extend(fetch_feed(selected_ticker, WATCHLIST_FEEDS[selected_ticker]))
        
        # 2. Fetch from Broad Industry News (if checked)
        if st.session_state.use_industry:
            for name, url in INDUSTRY_FEEDS.items():
                all_news.extend(fetch_feed(name, url))
                
        # 3. Fetch from Special Subjects (if checked)
        if st.session_state.use_subjects:
            for name, url in SUBJECT_FEEDS.items():
                all_news.extend(fetch_feed(name, url))

    if all_news:
        df = pd.DataFrame(all_news).drop_duplicates(subset=['Headline'])
        
        # --- ENHANCED FILTERING LOGIC ---
        if search_query:
            # Convert 'gold, copper, mining' into '(gold|copper|mining)' for OR search
            keywords = [k.strip().lower() for k in search_query.split(',')]
            pattern = '|'.join(map(re.escape, keywords))
            df = df[df['Headline'].str.contains(pattern, case=False, na=False)]
        
        if not df.empty:
            st.subheader(f"Intelligence Report for: {search_query if search_query else 'General News'}")
            st.dataframe(
                df, 
                column_config={"Link": st.column_config.LinkColumn("View Source")},
                use_container_width=True,
                hide_index=True
            )
            # Export functionality
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Results to CSV", data=csv, file_name="market_intel.csv", mime='text/csv')
        else:
            st.warning(f"No results found for your specific keywords: '{search_query}'")
    else:
        st.warning("No data retrieved. Ensure your internet connection is active.")
else:
    st.info("Set your criteria in the sidebar and click 'Execute Intel Sweep' to begin.")
