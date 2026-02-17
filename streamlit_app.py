import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime
import requests  # New import for Webhooks

# --- 1. CONFIGURATION ---
WATCHLIST_GROUPS = {
    "Hammond Power": ["Hammond Power", "Dry Type Transformer", "Hyundai Electric"],
    "Tantalus": ["Tantalus", "Smart metering systems", "Kongsberg", "Boeing Defense", "Itron"],
    "Kraken": ["Kraken", "NAVSEA", "Lockheed Martin", "L3Harris", "Airbus", "Rtx defense", "Northrop Grumman"],
    "5N Plus": ["5N Plus", "VNP", "Germanium", "Tellurium", "Cadmium", "AZUR Space"],
    "ISC": ["ISC", "Information Services Corp", "Dye & Durham"],
    "Neo Performance": ["NEO", "Neo Performance Materials", "Rare Earth Oxides", "Rare Earth Minerals"],
    "Polaris": ["Polaris Renewable Energy", "PIF"],
    "DIRTT": ["DRT", "DIRTT"],
    "Biorem": ["BRM", "Biorem"],
    "Atlas": ["AEP", "Atlas Engineered Products"],
    "Calian": ["CGY", "Calian"]
}

DEFAULT_BLACKLIST = ["MarketBeat", "Simply Wall St", "Zacks Investment Research", "Stock Traders Daily", "Defense World", "Best Stocks"]
LOGO_URL = "https://cormark.com/Portals/_default/Skins/Cormark/Images/Cormark_4C_183x42px.png"

st.set_page_config(page_title="Purdchuk News Screener", page_icon=LOGO_URL, layout="wide")
st.logo(LOGO_URL, link="https://cormark.com/")

if 'news_data' not in st.session_state:
    st.session_state.news_data = []

# --- 2. WEBHOOK ALERT FUNCTION (No Password Required) ---
def trigger_webhook_alert(df, group_name, webhook_url):
    if df.empty or not webhook_url:
        return
    
    # Convert headlines to a simple text list for the alert
    headlines_list = "\n".join([f"- {row['Company']}: {row['Headline']}" for _, row in df.head(10).iterrows()])
    
    payload = {
        "group": group_name,
        "message": f"New intelligence found for {group_name}!",
        "headlines": headlines_list,
        "count": len(df)
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            st.toast("Alert triggered via Webhook!", icon="🚀")
        else:
            st.error(f"Webhook failed: {response.status_code}")
    except Exception as e:
        st.error(f"Alert Error: {e}")

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("Purdchuk Settings")
    selected_group = st.selectbox("Watchlist Category", options=list(WATCHLIST_GROUPS.keys()))
    
    st.divider()
    st.header("🔔 Alert System")
    # THE RADIO BUTTON YOU REQUESTED
    alert_mode = st.radio(
        "Alert Settings:",
        options=["Manual Review Only", "Send Email Alert on Search"],
        index=0
    )
    
    # You get this URL from Zapier, Make.com, or IFTTT
    webhook_url = st.text_input("Webhook URL", placeholder="https://hooks.zapier.com/...")
    
    st.divider()
    st.header("Source Controls")
    available_sources = sorted(list(set([item['Source'] for item in st.session_state.news_data]))) if st.session_state.news_data else []
    whitelist = st.multiselect("⭐ Whitelist:", options=available_sources)
    
    present_blacklist = [s for s in DEFAULT_BLACKLIST if s in available_sources]
    blacklist = st.multiselect("🚫 Blacklist:", options=available_sources, default=present_blacklist)

    st.divider()
    keyword_filter = st.text_input("🔍 Search Headlines", "").strip().lower()

# --- 4. SCANNER LOGIC (Same as before) ---
def get_google_news(company_name):
    query = quote(f'{company_name} when:7d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
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

# --- 5. MAIN UI ---
st.title("Purdchuk News Screener")

if st.button(f" Search {selected_group} List", use_container_width=True):
    all_hits = []
    with st.spinner('Gathering intelligence...'):
        for company in WATCHLIST_GROUPS[selected_group]:
            all_hits.extend(get_google_news(company))
    st.session_state.news_data = all_hits

if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data).sort_values(by="sort_key", ascending=False)
    
    if whitelist: df = df[df['Source'].isin(whitelist)]
    if blacklist: df = df[~df['Source'].isin(blacklist)]
    if keyword_filter: df = df[df['Headline'].str.lower().str.contains(keyword_filter)]

    st.success(f"Curated {len(df)} headlines.")
    
    # TRIGGER ALERT IF RADIO BUTTON IS SET
    if alert_mode == "Send Email Alert on Search" and not df.empty:
        trigger_webhook_alert(df, selected_group, webhook_url)

    st.dataframe(
        df[["Date", "Company", "Source", "Headline", "Link"]], 
        column_config={"Link": st.column_config.LinkColumn("View Article")},
        use_container_width=True, hide_index=True
    )
