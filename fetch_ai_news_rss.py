import urllib.request
import xml.etree.ElementTree as ET
import json
import ssl
import re
import html
from datetime import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

feeds = [
    {"source": "Law.com / The American Lawyer", "url": "https://feeds.feedburner.com/law/headlines"},
    {"source": "Reuters Legal News", "url": "https://www.reuters.com/legal/rss"},
    {"source": "Above the Law", "url": "https://abovethelaw.com/feed/"},
    {"source": "Law360", "url": "https://www.law360.com/rss/articles"},
    {"source": "Legaltech News", "url": "https://feeds.feedburner.com/legaltechnews/headlines"},
    {"source": "Staffing Industry Analysts", "url": "https://www2.staffingindustry.com/rss"},
    {"source": "SHRM", "url": "https://www.shrm.org/rss/pages/rss.aspx"},
    {"source": "ERE.net", "url": "https://www.ere.net/feed/"},
    {"source": "Artificial Lawyer", "url": "https://www.artificiallawyer.com/feed/"},
    {"source": "LawSites by Bob Ambrogi", "url": "https://www.lawnext.com/feed"},
    {"source": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"}
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

all_news = []

for feed in feeds:
    print(f"Fetching RSS for {feed['source']}: {feed['url']}")
    req = urllib.request.Request(feed['url'], headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            rss_content = response.read()
            root = ET.fromstring(rss_content)
            
            # RSS namespace maps (usually empty/default namespace, but let's be safe)
            # Find all <item> tags
            items = root.findall('.//item')
            print(f"Found {len(items)} items in {feed['source']}")
            
            for item in items:
                title_el = item.find('title')
                title = title_el.text if title_el is not None else ""
                
                link_el = item.find('link')
                link = link_el.text if link_el is not None else ""
                
                desc_el = item.find('description')
                desc_html = desc_el.text if desc_el is not None else ""
                
                pub_el = item.find('pubDate')
                pub_date = pub_el.text if pub_el is not None else ""
                
                # Clean description
                clean_desc = ""
                if desc_html:
                    decoded = html.unescape(desc_html)
                    # Strip HTML tags
                    text_with_newlines = re.sub(r'<(?:p|br|div)[^>]*>', '\n', decoded)
                    clean_desc = re.sub(r'<[^>]+>', '', text_with_newlines)
                    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
                
                if not title:
                    continue
                
                news_item = {
                    "source": feed["source"],
                    "title": title,
                    "description": clean_desc,
                    "pubDate": pub_date,
                    "url": link
                }
                all_news.append(news_item)
    except Exception as e:
        print(f"Error fetching {feed['source']}: {e}")

# Save to ai_news_data.json
with open("./ai_news_data.json", "w") as f:
    json.dump(all_news, f, indent=2)

print(f"Saved {len(all_news)} news items to ./ai_news_data.json")
