import os
import ssl
import json
import urllib.request
from datetime import datetime, timezone
from urllib.parse import quote
import feedparser

# --- 1. OVERRIDE GLOBAL SSL FOR FEEDPARSER ---
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

DEFAULT_BLACKLIST = ["kalkine.ca", "Artsy", "Motor1.com", "insauga.com", "Durham Region Transit", "CoinGecko", "Yahoo! Finance Canada", "ca.finance.yahoo.com/" "durhamregiontransit.com", "simplywall.st", "thestreet.com", "cranebriefing.com", "kalklinemedia.com", "durhamregiontransit.com", "driving.ca", "driving.com", "NHL.com", "nhl.com", "motor1.com", "marketscreener.com", "MarketBeat", "Simply Wall St", "Zacks Investment Research", "Stock Traders Daily", "Defense World", "Best Stocks"]

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

def build_html_email(group_results):
    date_str = datetime.now().strftime('%B %d, %Y')
    
    all_articles = [item for items in group_results.values() for item in items]
    top_5 = sorted(all_articles, key=lambda x: x['date'], reverse=True)[:5]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f5f7; margin: 0; padding: 20px; color: #172b4d; }}
            .container {{ max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
            .header {{ background: #0f172a; color: #ffffff; padding: 28px 32px; text-align: left; border-bottom: 3px solid #2563eb; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }}
            .header p {{ margin: 6px 0 0 0; font-size: 13px; color: #94a3b8; font-weight: 500; }}
            .section {{ padding: 28px 32px; border-bottom: 1px solid #e2e8f0; }}
            .section-title {{ font-size: 13px; font-weight: 700; text-transform: uppercase; color: #2563eb; letter-spacing: 1px; margin-bottom: 20px; }}
            .top-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #2563eb; border-radius: 6px; padding: 16px 20px; margin-bottom: 14px; }}
            .top-card a {{ color: #0f172a; font-size: 15px; font-weight: 600; text-decoration: none; display: block; margin-bottom: 8px; line-height: 1.4; }}
            .top-card a:hover {{ color: #2563eb; }}
            .meta {{ font-size: 12px; color: #64748b; font-weight: 500; }}
            .badge {{ background: #e2e8f0; color: #334155; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-right: 8px; }}
            .group-title {{ font-size: 16px; font-weight: 700; color: #0f172a; margin: 20px 0 12px 0; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px; }}
            .article-item {{ padding: 10px 0; border-bottom: 1px dashed #e2e8f0; }}
            .article-item:last-child {{ border-bottom: none; }}
            .article-item a {{ color: #1e293b; font-size: 14px; font-weight: 500; text-decoration: none; display: block; margin-bottom: 4px; }}
            .article-item a:hover {{ color: #2563eb; }}
            .footer {{ background: #f8fafc; padding: 20px 32px; text-align: center; font-size: 12px; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Daily Watchlist Intelligence</h1>
                <p>Morning Executive Summary • {date_str}</p>
            </div>
            
            <div class="section">
                <div class="section-title">TOP 5 HEADLINES</div>
    """

    for idx, item in enumerate(top_5, 1):
        html += f"""
        <div class="top-card">
            <a href="{item['link']}" target="_blank">{item['title']}</a>
            <div class="meta">
                <span class="badge">{item['source']}</span>
                <span>Keyword: {item['term']}</span>
            </div>
        </div>
        """

    html += """
            </div>
            <div class="section">
                <div class="section-title">WATCHLIST GROUP SUMMARIES</div>
    """

    for group, items in group_results.items():
        html += f'<div class="group-title">{group.upper()}</div>'
        for item in items[:3]:
            html += f"""
            <div class="article-item">
                <a href="{item['link']}" target="_blank">{item['title']}</a>
                <div class="meta">
                    <span class="badge">{item['source']}</span>
                </div>
            </div>
            """

    html += """
            </div>
            <div class="footer">
                Curated automatically via Purdchuk News Screener • Confidential
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_email():
    api_key = os.environ.get("API_KEY", "").strip()
    raw_recipients = os.environ.get("RECIPIENT_EMAIL", "").strip()
    sender_email = os.environ.get("SENDER_EMAIL", "").strip()

    if not api_key or not raw_recipients or not sender_email:
        print("Error: Missing API_KEY, SENDER_EMAIL, or RECIPIENT_EMAIL in environment secrets.")
        return

    # Parse comma-separated emails into Brevo recipient objects
    recipient_list = [
        {"email": email.strip()} 
        for email in raw_recipients.split(",") 
        if email.strip()
    ]

    print("Fetching news feeds...")
    news_data = fetch_fresh_news()
    print(f"Feeds fetched. Found updates for {len(news_data)} groups.")
    
    if not news_data:
        html_content = f"<h3>Daily Watchlist News Summary</h3><p>Date: {datetime.now().strftime('%B %d, %Y')}</p><p>No fresh headlines matched your watchlist criteria today.</p>"
    else:
        html_content = build_html_email(news_data)

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "Purdchuk Screener", "email": sender_email},
        "to": recipient_list,  # Passes both recipient addresses to Brevo
        "subject": f"Daily Watchlist News Summary - {datetime.now().strftime('%B %d, %Y')}",
        "htmlContent": html_content
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            print(f"HTML Email sent successfully to {len(recipient_list)} recipient(s)! Status code: {response.getcode()}")
    except Exception as e:
        print(f"Failed to send email via Brevo API: {e}")
        raise e
