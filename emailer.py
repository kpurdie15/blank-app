import os
import ssl
import json
import urllib.request
from datetime import datetime, timezone
from urllib.parse import quote
import feedparser

# --- 1. OVERRIDE GLOBAL SSL FOR FEEDPARSER ---
# Prevents Google News RSS from silently returning 0 entries on Linux runners
ssl._create_default_https_context = ssl._create_unverified_context

# --- 2. CONFIGURATION ---
WATCHLIST_GROUPS = {
    "Zefiro": ["Zefiro", "Well Plugging", "Abandoned Wells", "Methane Abatement", "ZEFI", "Plants and Goodwin", "Ranger Energy Services"],
    "Volatus": ["Volatus", "Volatus Aerospace", "FLT", "Red Cat Holdings", "Ondas", "Draganfly", "Unusual Machines", "AeroVironment", "Kratos Defense & Security Solutions", "Parrot", "AgEagle Aerial Systems"],
    "Hammond Power": ["Hammond Power", "Dry Type Transformer", "Hyundai Electric", "AEG Power Systems", "Uninterruptible Power Supply", "Schneider Electric", "Siemens", "Eaton Corp", "SGB-SMIT", "SGB-SMIT IPO"],
    "Tantalus": ["Tantalus", "Tantalus Systems", "Smart metering systems", "Itron", "Landis + Gyr", "Grid Tech"],
    "Kraken": ["Kraken Robotics", "PNG", "REMUS", "NAVSEA", "Lockheed Martin", "L3Harris", "Airbus", "Rtx defense", "Northrop Grumman", "Thales Defense", "Subsea battery", "Kongsberg", "Cellula Robotics", "Huntington Ingalls", "Teledyne Technologies", "Anduril", "Covelya", "Sonardyne", "EIVA", "Forcys", "Wavefront", "Chelsea Technologies", "Voyis"],
    "5N Plus": ["Planet Labs", "Eutelsat", "OneWeb", "5N Plus", "VNP", "Germanium", "Tellurium", "Cadmium", "AZUR Space", "Sierra Space", "Bismuth", "USA Rare Earth", "MP Materials", "First Solar"],
    "Firan": ["FTG", "Firan Technologies", "Airbus Deliveries", "Boeing Deliveries", "Printed Circuit Boards", "Cockpit Products"],
    "Neo Performance": ["NEO", "Neo Performance Materials", "Rare Earth Oxides", "Rare Earth Minerals"],
    "Polaris": ["Polaris Renewable Energy", "PIF"],
    "DIRTT": ["DIRTT", "DRT"],
    "Biorem": ["BRM", "Biorem"],
    "Atlas": ["Atlas Engineered Products", "Canadian Roof Trusses", "Canadian Building Products"],
    "Calian": ["Calian", "Arctic Sovereignty", "Canadian Armed Forces", "Canadian Defense", "Arctic War", "Canadian Navy"]
}

DEFAULT_BLACKLIST = ["NHL.com", "nhl.com", "motor1.com", "marketscreener.com", "MarketBeat", "Simply Wall St", "Zacks Investment Research", "Stock Traders Daily", "Defense World", "Best Stocks"]

def fetch_fresh_news():
    group_results = {}
    seen_links = set()

    for group, terms in WATCHLIST_GROUPS.items():
        articles = []
        for term in terms:
            query = quote(f'{term} when:7d')
            url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
            
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:5]:
                link = entry.get('link', '')
                source = entry.source.get('title', 'Google News') if hasattr(entry, 'source') else 'Google News'
                
                if link in seen_links or source in DEFAULT_BLACKLIST:
                    continue
                
                parsed_date = entry.get('published_parsed')
                pub_datetime = datetime(*parsed_date[:6], tzinfo=timezone.utc) if parsed_date else datetime.now(timezone.utc)
                
                seen_links.add(link)
                articles.append({
                    "title": entry.title,
                    "link": link,
                    "source": source,
                    "term": term,
                    "date": pub_datetime
                })
        if articles:
            group_results[group] = sorted(articles, key=lambda x: x['date'], reverse=True)
            
    return group_results

def build_email_body(group_results):
    date_str = datetime.now().strftime('%B %d, %Y')
    
    all_articles = [item for items in group_results.values() for item in items]
    top_5 = sorted(all_articles, key=lambda x: x['date'], reverse=True)[:5]

    body = f"Daily Watchlist News Summary\nDate: {date_str}\n\n"
    body += "="*80 + "\nTOP 5 HEADLINES\n" + "="*80 + "\n\n"
    
    for idx, item in enumerate(top_5, 1):
        body += f"{idx}. {item['title']}\n"
        body += f"   • Source: {item['source']}\n"
        body += f"   • Link: {item['link']}\n\n"

    body += "="*80 + "\nGROUP SUMMARIES\n" + "="*80 + "\n\n"
    
    for group, items in group_results.items():
        body += f"{group.upper()}\n"
        for item in items[:3]:
            body += f"• {item['title']}\n"
            body += f"  - Source: {item['source']}\n"
            body += f"  - Link: {item['link']}\n"
        body += "\n"

    body += "-"*80 + "\nCurated via Purdchuk News Screener"
    return body

def send_email():
    api_key = os.environ.get("API_KEY", "").strip()
    recipient_email = os.environ.get("RECIPIENT_EMAIL", "").strip()
    sender_email = os.environ.get("SENDER_EMAIL", "").strip()

    if not api_key or not recipient_email or not sender_email:
        print("Error: Missing API_KEY, SENDER_EMAIL, or RECIPIENT_EMAIL in environment secrets.")
        return

    print("Fetching news feeds...")
    news_data = fetch_fresh_news()
    print(f"Feeds fetched. Found updates for {len(news_data)} groups.")
    
    if not news_data:
        print("No fresh news parsed today.")
        email_text = f"Daily Watchlist News Summary\nDate: {datetime.now().strftime('%B %d, %Y')}\n\nNo headlines matched your criteria today."
    else:
        email_text = build_email_body(news_data)

    # --- DISPATCH VIA BREVO API ---
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "Purdchuk Screener", "email": sender_email},
        "to": [{"email": recipient_email}],
        "subject": f"Daily Watchlist News Summary - {datetime.now().strftime('%B %d, %Y')}",
        "textContent": email_text
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Email sent successfully! Status code: {response.getcode()}")
    except Exception as e:
        print(f"Failed to send email via Brevo API: {e}")
        raise e

if __name__ == "__main__":
    send_email()
