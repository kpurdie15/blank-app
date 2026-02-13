import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime

# --- 1. CONFIGURATION ---
WATCHLIST = ["Aritzia", "NFI Group", "5N Plus", "Converge Technology", "Lumine Group", "Sylogist"]

st.set_page_config(page_title="Google Intel Sweep", layout="wide")
st.title("🗞️ Global News Intelligence (via Google)")

# --- 2. THE SCANNER ---
def get_google_news(company_name):
    """Fetches ticker-specific news from Google News RSS with formatted dates."""
    query = quote(f'{company_name} when:7d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    
    # SSL bypass for corporate firewalls
    ssl_context = ssl._create_unverified_context()
    
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:5]:
        # Extract the raw date string (e.g., 'Wed, 21 Jan 2026 03:00:00 GMT')
        raw_date = entry.get('published', '')
        
        # We also get a 'parsed' version from feedparser that is easier to format
        parsed_date = entry.get('published_parsed')
        if parsed_date:
            # Format to something clean like 'Jan 21, 2026'
            clean_date = datetime(*parsed_date[:6]).strftime('%b %d, %Y')
        else:
            clean_date = "Unknown"

        results.append({
            "Company": company_name,
            "Date": clean_date,  # New Date Column
            "Source": entry.source.get('title', 'Google News'),
            "Headline": entry.title,
            "Link": entry.link
        })
    return results

# --- 3. UI LOGIC ---
if st.button("🚀 Run Global Intel Sweep", use_container_width=True):
    all_hits = []
    with st.spinner('Scouring global newswires...'):
        for company in WATCHLIST:
            all_hits.extend(get_google_news(company))
            
    if all_hits:
        df = pd.DataFrame(all_hits)
        
        # Reorder columns to put Date near the front
        df = df[["Date", "Company", "Source", "Headline", "Link"]]
        
        st.dataframe(
            df, 
            column_config={
                "Link": st.column_config.LinkColumn("View Full Article"),
                "Date": st.column_config.Column(width="medium")
            },
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("No global mentions found for your watchlist this week.")
