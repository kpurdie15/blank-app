import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl

# --- 1. CONFIGURATION ---
WATCHLIST = ["Aritzia", "NFI Group", "5N Plus", "Converge Technology", "Lumine Group", "Sylogist"]

st.set_page_config(page_title="Google Intel Sweep", layout="wide")
st.title("🗞️ Global News Intelligence (via Google)")

# --- 2. THE SCANNER ---
def get_google_news(company_name):
    """Fetches ticker-specific news from Google News RSS."""
    # This URL structure is a stable 'backdoor' for Google News RSS
    # We use 'when:7d' to only get news from the last week for speed
    query = quote(f'{company_name} when:7d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    
    # SSL bypass for corporate firewalls
    ssl_context = ssl._create_unverified_context()
    
    # We only take the top 5 results per company to keep it lightning fast
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:5]:
        results.append({
            "Company": company_name,
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
        st.dataframe(
            df, 
            column_config={"Link": st.column_config.LinkColumn("View Full Article")},
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("No global mentions found for your watchlist this week.")
