import os
import ssl
import json
import urllib.request
from datetime import datetime, timezone
from urllib.parse import quote
import feedparser
import yfinance as yf

# --- 1. OVERRIDE GLOBAL SSL FOR FEEDPARSER ---
ssl._create_default_https_context = ssl._create_unverified_context

# --- 2. WATCHLIST & TICKER CONFIGURATION ---
TICKERS = {
    "Zefiro": "ZEFI.NE",
    "Volatus": "FLT.TO",
    "Hammond": "HPS-A.TO",
    "Tantalus": "GRID.TO",
    "Kraken": "PNG.V",
    "5N Plus": "VNP.TO",
    "Firan": "FTG.TO",
    "Neo Perf.": "NEO.TO",
    "Polaris": "PIF.TO",
    "DIRTT": "DRT.TO",
    "Biorem": "BRM.V",
    "Atlas": "AEP.TO",
    "Calian": "CGY.TO"
}

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

DEFAULT_BLACKLIST = [
    "NHL.com", "nhl.com", "motor1.com", "Motor1.com", "marketscreener.com", "MarketBeat", 
    "Simply Wall St", "Simply Wall Street", "Zacks Investment Research", "Stock Traders Daily", 
    "University of Central Florida", "Mining.com", "NerdWallet", "Semafor", "BusinessDesk | NZ",
    "Defense World", "Best Stocks", "The Star", "kalkine.ca", "Kalkine Media", "driving.ca", 
    "Artsy", "Yahoo! Finance Canada", "Durham Region Transit", "insauga.com", 
    "Team Nice Cote d'Azur", "The Motley Fool Canada", "investincotedazur", "acc.org", "American College of Cardiology", "AOL.com", "aol.com", "ATP Tour", "atptour.com", 
]

def fetch_stock_prices():
    """Fetches real-time market quote data for watchlist tickers."""
    stock_data = []
    symbol_string = " ".join(TICKERS.values())
    try:
        tickers_obj = yf.Tickers(symbol_string)
        for label, symbol in TICKERS.items():
            try:
                fast_info = tickers_obj.tickers[symbol].fast_info
                price = fast_info.last_price
                prev_close = fast_info.previous_close
                if price and prev_close:
                    change_pct = ((price - prev_close) / prev_close) * 100
                    stock_data.append({
                        "label": label,
                        "symbol": symbol,
                        "price": f"${price:.2f}",
                        "change_pct": change_pct,
                        "is_up": change_pct >= 0
                    })
            except Exception as inner_e:
                print(f"Warning: Failed to fetch quote for {symbol}: {inner_e}")
    except Exception as e:
        print(f"Failed to download stock quotes: {e}")
    return stock_data

def fetch_fresh_news():
    """Fetches Google News RSS feeds applying strict freshness and source blacklists."""
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
                
                # Deduplicate links and exclude sources matching blacklist strings
                if link in seen_links or any(b.lower() in source.lower() for b in DEFAULT_BLACKLIST):
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

def build_html_email(group_results, stock_data):
    """Generates the executive HTML layout containing stock tickers and headlines."""
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
            .container {{ max-width: 720px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
            .header {{ background: #0f172a; color: #ffffff; padding: 28px 32px; text-align: left; border-bottom: 3px solid #2563eb; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }}
            .header p {{ margin: 6px 0 0 0; font-size: 13px; color: #94a3b8; font-weight: 500; }}
            .section {{ padding: 24px 32px; border-bottom: 1px solid #e2e8f0; }}
            .section-title {{ font-size: 12px; font-weight: 700; text-transform: uppercase; color: #2563eb; letter-spacing: 1px; margin-bottom: 16px; }}
            
            .ticker-grid {{ display: table; width: 100%; border-collapse: separate; border-spacing: 6px; margin-bottom: 8px; }}
            .ticker-card {{ display: table-cell; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px; text-align: center; vertical-align: middle; }}
            .ticker-name {{ font-size: 11px; font-weight: 700; color: #475569; display: block; }}
            .ticker-price {{ font-size: 13px; font-weight: 700; color: #0f172a; margin: 2px 0; display: block; }}
            .change-up {{ font-size: 11px; font-weight: 700; color: #16a34a; }}
            .change-down {{ font-size: 11px; font-weight: 700; color: #dc2626; }}
            
            .top-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #2563eb; border-radius: 6px; padding: 16px 20px; margin-bottom: 12px; }}
            .top-card a {{ color: #0f172a; font-size: 15px; font-weight: 600; text-decoration: none; display: block; margin-bottom: 8px; line-height: 1.4; }}
            .meta {{ font-size: 12px; color: #64748b; font-weight: 500; }}
            .badge {{ background: #e2e8f0; color: #334155; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-right: 8px; }}
            .group-title {{ font-size: 15px; font-weight: 700; color: #0f172a; margin: 20px 0 10px 0; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px; }}
            .article-item {{ padding: 10px 0; border-bottom: 1px dashed #e2e8f0; }}
            .article-item:last-child {{ border-bottom: none; }}
            .article-item a {{ color: #1e293b; font-size: 14px; font-weight: 500; text-decoration: none; display: block; margin-bottom: 4px; }}
            .footer {{ background: #f8fafc; padding: 20px 32px; text-align: center; font-size: 12px; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Daily Watchlist Intelligence</h1>
                <p>Morning Executive Summary • {date_str}</p>
            </div>
    """

    if stock_data:
        html += """
        <div class="section" style="background: #ffffff; padding-bottom: 16px;">
            <div class="section-title">MARKET SNAPSHOT</div>
            <div style="width: 100%; overflow-x: auto;">
        """
        for i in range(0, len(stock_data), 4):
            chunk = stock_data[i:i+4]
            html += '<div class="ticker-grid">'
            for stock in chunk:
                change_class = "change-up" if stock['is_up'] else "change-down"
                sign = "+" if stock['is_up'] else ""
                html += f"""
                <div class="ticker-card">
                    <span class="ticker-name">{stock['label']}</span>
                    <span class="ticker-price">{stock['price']}</span>
                    <span class="{change_class}">{sign}{stock['change_pct']:.1f}%</span>
                </div>
                """
            html += '</div>'
        html += """
            </div>
        </div>
        """

    html += """
            <div class="section">
                <div class="section-title">TOP 5 HEADLINES</div>
    """

    for item in top_5:
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

    recipient_list = [
        {"email": email.strip()} 
        for email in raw_recipients.split(",") 
        if email.strip()
    ]

    print("Fetching stock market quotes...")
    stock_data = fetch_stock_prices()
    print(f"Quotes fetched for {len(stock_data)} tickers.")

    print("Fetching news feeds...")
    news_data = fetch_fresh_news()
    print(f"Feeds fetched. Found updates for {len(news_data)} groups.")
    
    if not news_data:
        html_content = f"<h3>Daily Watchlist News Summary</h3><p>Date: {datetime.now().strftime('%B %d, %Y')}</p><p>No fresh headlines matched your watchlist criteria today.</p>"
    else:
        html_content = build_html_email(news_data, stock_data)

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "Purdchuk Screener", "email": sender_email},
        "to": recipient_list,
        "subject": f"Daily Watchlist News Summary - {datetime.now().strftime('%B %d, %Y')}",
        "htmlContent": html_content
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Executive HTML Email dispatched successfully! Status code: {response.getcode()}")
    except Exception as e:
        print(f"Failed to send email via Brevo API: {e}")
        raise e

if __name__ == "__main__":
    send_email()
