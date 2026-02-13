import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import ssl

# --- 1. GLOBAL CONFIGURATION ---
# Use the official outbound RSS feeds from major Canadian publishers
MAJOR_CANADIAN_FEEDS = {
    "Globe & Mail: Investing": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/investing/",
    "Globe & Mail: Business": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
    "CBC Business News": "https://www.cbc.ca/webfeed/rss/rss-business",
    "Financial Post": "https://financialpost.com/category/business/feed/"
}

# The names/tickers we will scan for within these broad feeds
WATCHLIST_KEYWORDS = ["Aritzia", "ATZ", "NFI", "5N Plus", "VNP", "Converge", "CTS", "Lumine", "LMN", "Sylogist", "SYZ"]

# --- 2. PAGE SETUP ---
st.set_page_config(page_title="Equity Intelligence Dashboard", layout="wide")
st.title("🏛️ Professional Market Intelligence")
st.subheader("Scanning Globe & Mail, Financial Post, and CBC for Watchlist Mentions")

# --- 3. THE SCANNER ENGINE ---
def fetch_and_screen_news():
    """Fetches broad feeds and filters them for specific watchlist hits."""
    all_hits = []
    
    # Bypass corporate SSL/Firewall issues
    ssl_context = ssl._create_unverified_context()
    
    with st.spinner('Scanning major Canadian outlets...'):
        for source_name, url in MAJOR_CANADIAN_FEEDS.items():
            # Parse the feed using the SSL bypass context
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                headline = entry.title
                # Check if ANY of our watchlist keywords appear in the headline
                if any(keyword.lower() in headline.lower() for keyword in WATCHLIST_KEYWORDS):
                    all_hits.append({
                        "Source": source_name,
                        "Date": entry.get('published', datetime.now().strftime('%b %d')),
                        "Headline": headline,
                        "Link": entry.link
                    })
    return all_hits

# --- 4. MAIN UI LOGIC ---
if st.button("🔄 Execute Watchlist Intel Sweep", use_container_width=True):
    results = fetch_and_screen_news()
    
    if results:
        # Convert to DataFrame and remove any duplicate headlines
        df = pd.DataFrame(results).drop_duplicates(subset=['Headline'])
        
        st.success(f"Found {len(df)} specific mentions of your watchlist companies.")
        
        # Display the results in a professional table
        st.dataframe(
            df, 
            column_config={"Link": st.column_config.LinkColumn("View Full Article")},
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("No specific mentions of your watchlist were found in the current news cycles.")
else:
    st.info("Click the button above to scan major Canadian newsrooms for your stocks.")
