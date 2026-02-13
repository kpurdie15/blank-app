import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime

# --- 1. CONFIGURATION & BRANDING ---
WATCHLIST_GROUPS = {
    "Industrial": ["Hammond Power", "NFI Group", "5N Plus", "Kraken Robotics"],
    "Tech": ["Tantalus", "Calian", "Converge Technology", "Lumine Group"]
}
LOGO_URL = "https://cormark.com/Portals/_default/Skins/Cormark/Images/Cormark_4C_183x42px.png"

st.set_page_config(page_title="Purdchuk News Screener", page_icon=LOGO_URL, layout="wide")
st.logo(LOGO_URL, link="https://cormark.com/")

if 'news_data' not in st.session_state:
    st.session_state.news_data = []

# --- 2. SIDEBAR: FILTERS & BLACKLIST ---
with st.sidebar:
    st.header("Intelligence Filters")
    selected_group = st.selectbox("Watchlist Category", options=list(WATCHLIST_GROUPS.keys()))
    
    # SOURCE FILTERING UI
    st.subheader("Source Control")
    filter_mode = st.radio("Mode:", ["Show All", "Whitelist (Only these)", "Blacklist (Exclude these)"])
    
    # We extract unique sources from the data to populate the filter
    available_sources = []
    if st.session_state.news_data:
        available_sources = sorted(list(set([item['Source'] for item in st.session_state.news_data])))
    
    selected_sources = st.multiselect("Select Sources:", options=available_sources)

st.title(f"Market Intelligence: {selected_group}")

# --- 3. THE SCANNER ---
def get_google_news(company_name):
    query = quote(f'{company_name} when:7d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    ssl_context = ssl._create_unverified_context()
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:10]:
        parsed_date = entry.get('published_parsed')
        sort_date = datetime(*parsed_date[:6]) if parsed_date else datetime(1900, 1, 1)
        results.append({
            "sort_key": sort_date,
            "Date": sort_date.strftime('%b %d, %Y'),
            "Company": company_name,
            "Source": entry.source.get('title', 'Google News'),
            "Headline": entry.title,
            "Link": entry.link
        })
    return results

# --- 4. UI LOGIC & FILTERING ---
if st.button(f"Scan {selected_group}", use_container_width=True):
    all_hits = []
    with st.spinner('Scouring newswires...'):
        for company in WATCHLIST_GROUPS[selected_group]:
            all_hits.extend(get_google_news(company))
    st.session_state.news_data = all_hits

if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data).sort_values(by="sort_key", ascending=False)
    
    # --- DATA FILTERING ENGINE ---
    if selected_sources:
        if filter_mode == "Whitelist (Only these)":
            # Keep only the sources in our list
            df = df[df['Source'].isin(selected_sources)]
        elif filter_mode == "Blacklist (Exclude these)":
            # Keep everything EXCEPT the sources in our list
            df = df[~df['Source'].isin(selected_sources)]

    display_df = df[["Date", "Company", "Source", "Headline", "Link"]]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
