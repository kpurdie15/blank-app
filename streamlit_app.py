import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime

# --- 1. CONFIGURATION & BRANDING ---
# Organised into categories for dynamic filtering
WATCHLIST_GROUPS = {
    "Industrial/Manufacturing": ["Hammond Power", "NFI Group", "5N Plus", "Kraken Robotics", "DIRTT", "Atlas Engineered Products"],
    "Technology/Services": ["Tantalus", "Information Services Corp", "Calian", "Converge Technology", "Sylogist", "Lumine Group"],
    "Renewable Energy": ["Polaris Renewable Energy", "Biorem", "Boralex", "Innergex Renewable"]
}

LOGO_URL = "https://cormark.com/Portals/_default/Skins/Cormark/Images/Cormark_4C_183x42px.png"
WEBSITE_URL = "https://cormark.com/"

st.set_page_config(page_title="Purdchuk News Screener", page_icon=LOGO_URL, layout="wide")
st.logo(LOGO_URL, link=WEBSITE_URL)

# Initialize data persistence
if 'news_data' not in st.session_state:
    st.session_state.news_data = []

# --- 2. THE SCANNER ENGINE ---
def get_google_news(company_name):
    query = quote(f'{company_name} when:7d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    ssl_context = ssl._create_unverified_context()
    
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:5]:
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

# --- 3. SIDEBAR: DYNAMIC WATCHLIST SELECTION ---
with st.sidebar:
    st.header("Watchlist Controls")
    # THE FILTER: Choose which watchlist to pull
    selected_group = st.selectbox(
        "Select Watchlist Category", 
        options=list(WATCHLIST_GROUPS.keys())
    )
    
    current_watchlist = WATCHLIST_GROUPS[selected_group]
    st.info(f"Monitoring: {', '.join(current_watchlist)}")
    
    st.divider()
    st.header("Display Settings")
    sort_choice = st.selectbox("Primary Sort:", ["Newest First", "Source", "Company"])
    keyword_filter = st.text_input("🔍 Quick Keyword Filter", "").strip().lower()

st.title(f"Purdchuk News Screener: {selected_group}")

# --- 4. UI LOGIC ---
if st.button(f"Scan {selected_group} Watchlist", use_container_width=True):
    all_hits = []
    with st.spinner(f'Scouring newswires for {selected_group}...'):
        for company in current_watchlist:
            all_hits.extend(get_google_news(company))
    st.session_state.news_data = all_hits

if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data)
    
    # Apply Sorting
    if sort_choice == "Newest First":
        df = df.sort_values(by=["sort_key", "Source"], ascending=[False, True])
    elif sort_choice == "Source":
        df = df.sort_values(by=["Source", "sort_key"], ascending=[True, False])
    else:
        df = df.sort_values(by=["Company", "sort_key"], ascending=[True, False])

    # Apply Keyword Filter
    if keyword_filter:
        mask = df['Headline'].str.lower().str.contains(keyword_filter) | df['Company'].str.lower().str.contains(keyword_filter)
        df = df[mask]

    display_df = df[["Date", "Company", "Source", "Headline", "Link"]]
    
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
    st.info(f"Select a category and scan to view the {selected_group} feed.")
