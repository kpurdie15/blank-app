import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime

# --- 1. CONFIGURATION ---
WATCHLIST = ["Aritzia", "NFI Group", "5N Plus", "Converge Technology", "Lumine Group", "Sylogist"]

st.set_page_config(page_title="Google Intel Sweep", layout="wide")
st.title("Purdchuk News Screener")

# --- 2. THE SCANNER ---
def get_google_news(company_name):
    """Fetches news and prepares data for chronological sorting."""
    query = quote(f'{company_name} when:7d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    
    ssl_context = ssl._create_unverified_context()
    
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:10]: # Increased to 10 results for better sorting depth
        parsed_date = entry.get('published_parsed')
        
        if parsed_date:
            # We create a real datetime object for the computer to sort
            sort_date = datetime(*parsed_date[:6])
            # We create a clean string for the human to read
            display_date = sort_date.strftime('%b %d, %Y')
        else:
            sort_date = datetime(1900, 1, 1) # Fallback for missing dates
            display_date = "Unknown"

        results.append({
            "sort_key": sort_date, # Hidden column for sorting logic
            "Date": display_date,
            "Company": company_name,
            "Source": entry.source.get('title', 'Google News'),
            "Headline": entry.title,
            "Link": entry.link
        })
    return results

# --- 3. UI LOGIC ---
if st.button("🚀 Run Sorted Intel Sweep", use_container_width=True):
    all_hits = []
    with st.spinner('Scouring global newswires and sorting by date...'):
        for company in WATCHLIST:
            all_hits.extend(get_google_news(company))
            
    if all_hits:
        # Convert to DataFrame
        df = pd.DataFrame(all_hits)
        
        # --- THE SORTING MAGIC ---
        # Sort by the hidden 'sort_key' in descending order (Newest first)
        df = df.sort_values(by="sort_key", ascending=False)
        
        # Remove the hidden sort key before showing the user
        display_df = df[["Date", "Company", "Source", "Headline", "Link"]]
        
        st.success(f"Successfully pulled and sorted {len(display_df)} headlines.")
        st.dataframe(
            display_df, 
            column_config={
                "Link": st.column_config.LinkColumn("View Full Article"),
                "Date": st.column_config.Column(width="small"),
                "Company": st.column_config.Column(width="medium")
            },
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("No global mentions found for your watchlist this week.")
