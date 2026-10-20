import os
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import feedparser

# --- CONFIGURATION ---
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
    ssl_context = ssl._create_unverified_context()
    now = datetime.now(timezone.utc)
    # Use 24-hour window to catch all after-market & morning updates
    cutoff_time = now - timedelta(hours=24)
    
    group_results = {}
    seen_links = set()

    for group, terms in WATCHLIST_GROUPS.items():
        articles = []
        for term in terms:
            query = quote(f'{term} when:1d')
            url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:5]:
                link = entry.get('link', '')
                source = entry.source.get('title', 'Google News') if hasattr(entry, 'source') else 'Google News'
                
                if link in seen_links or source in DEFAULT_BLACKLIST:
                    continue
                
                parsed_date = entry.get('published_parsed')
                if parsed_date:
                    pub_datetime = datetime(*parsed_date[:6], tzinfo=timezone.utc)
                else:
                    pub_datetime = now
                
                if pub_datetime >= cutoff_time:
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


def send_email():
    sender_email = os.environ.get("SENDER_EMAIL", "").strip()
    sender_password = os.environ.get("SENDER_PASSWORD", "").replace(" ", "").strip()
    recipient_email = os.environ.get("RECIPIENT_EMAIL", "").strip()

    if not sender_email or not sender_password or not recipient_email:
        print("Error: Missing email environment variables in GitHub Secrets.")
        return

    news_data = fetch_fresh_news()
    
    # Fallback message if no new articles matched the cutoff window
    if not news_data:
        print("No fresh news found within cutoff window. Sending status update email.")
        email_text = f"Daily Watchlist News Summary\nDate: {datetime.now().strftime('%B %d, %Y')}\n\nNo new headlines matched your watchlist criteria in the past 24 hours."
    else:
        email_text = build_email_body(news_data)

    msg = MIMEMultipart()
    msg["Subject"] = f"Daily Watchlist News Summary - {datetime.now().strftime('%B %d, %Y')}"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(email_text, "plain"))

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print("Daily digest email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e
