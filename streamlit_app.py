import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# --- 2. EMAIL UTILITY FUNCTION ---
def send_email_notification(df, group_name, target_email, app_password, sender_email):
    if df.empty:
        return
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = target_email
    msg['Subject'] = f"🚀 Purdchuk Alert: {group_name} Intelligence Update"

    # Minimalist HTML Table for the Email
    html_content = f"""
    <h3>Latest Headlines for {group_name}</h3>
    <p>The following news was captured based on your active filters:</p>
    {df[['Date', 'Company', 'Source', 'Headline']].to_html(index=False, border=0)}
    <br>
    <p><i>Sent via Purdchuk News Screener</i></p>
    """
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        st.toast(f"Email sent to {target_email}!", icon="📧")
    except Exception as e:
        st.error(f"Email failed: {e}")

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("Purdchuk Settings")
    selected_group = st.selectbox("Watchlist Category", options=list(WATCHLIST_GROUPS.keys()))
    
    st.divider()
    st.header("Source Controls")
    
    available_sources = sorted(list(set([item['Source'] for item in st.session_state.news_data]))) if st.session_state.news_data else []
    
    whitelist = st.multiselect("⭐ Whitelist (Show ONLY):", options=available_sources)
    
    present_blacklist = [s for s in DEFAULT_BLACKLIST if s in available_sources]
    blacklist = st.multiselect("🚫 Blacklist (Hide):", options=available_sources, default=present_blacklist)

    st.divider()
    keyword_filter = st.text_input("🔍 Search Headlines", "").strip().lower()

    st.divider()
    st.header("📧 Email Alerts")
    enable_email = st.checkbox("Send Email on Search")
    user_email = st.text_input("Receiver Email", "your-email@example.com")
    # Store these in st.secrets for production!
    sender_user = st.text_input("Sender Gmail", "your-gmail@gmail.com")
    sender_pass = st.text_input("Gmail App Password", type="password")

# --- 4. THE SCANNER ---
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

# --- 5. MAIN UI & LOGIC ---
st.title("Purdchuk News Screener")
st.subheader(f"Current Watchlist: {selected_group}")

if st.button(f" Search {selected_group} List", use_container_width=True):
    all_hits = []
    with st.spinner('Gathering intelligence...'):
        for company in WATCHLIST_GROUPS[selected_group]:
            all_hits.extend(get_google_news(company))
    st.session_state.news_data = all_hits

if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data).sort_values(by="sort_key", ascending=False)
    
    # Apply Filters
    if whitelist:
        df = df[df['Source'].isin(whitelist)]
    if blacklist:
        df = df[~df['Source'].isin(blacklist)]
    if keyword_filter:
        df = df[df['Headline'].str.lower().str.contains(keyword_filter)]

    st.success(f"Curated {len(df)} headlines for your review.")
    
    # TRIGGER EMAIL
    if enable_email and not df.empty and sender_pass:
        send_email_notification(df, selected_group, user_email, sender_pass, sender_user)

    st.dataframe(
        df[["Date", "Company", "Source", "Headline", "Link"]], 
        column_config={"Link": st.column_config.LinkColumn("View Article")},
        use_container_width=True, 
        hide_index=True
    )
