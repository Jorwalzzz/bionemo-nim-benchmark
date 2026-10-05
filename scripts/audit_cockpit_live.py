import urllib.request
import re
from urllib.parse import urljoin

cockpit_url = "https://jorwalzzz.github.io/bionemo-nim-benchmark/cockpit.html"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def check_url(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except Exception as e:
        return str(e), None

status, html_bytes = check_url(cockpit_url)
print(f"COCKPIT URL STATUS: {status}, Size: {len(html_bytes) if html_bytes else 0} bytes")

if html_bytes:
    html = html_bytes.decode('utf-8', errors='ignore')
    
    scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
    anchors = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html)
    
    print("\n--- COCKPIT SCRIPTS ---")
    for s in set(scripts):
        full = urljoin(cockpit_url, s)
        st, b = check_url(full)
        print(f"Script: {s} -> {st} ({len(b) if b else 0}b)")
        
    print("\n--- COCKPIT LINKS (Testing first 15) ---")
    checked = 0
    for a in set(anchors):
        if not a.startswith('#') and not a.startswith('javascript:'):
            full = urljoin(cockpit_url, a)
            st, b = check_url(full)
            print(f"Link: {a} -> {st}")
            checked += 1
            if checked >= 15:
                break
