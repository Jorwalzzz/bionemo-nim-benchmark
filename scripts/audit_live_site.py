import urllib.request
import re
from urllib.parse import urljoin

base_url = "https://jorwalzzz.github.io/bionemo-nim-benchmark/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def check_url(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except Exception as e:
        return str(e), None

status, html_bytes = check_url(base_url)
print(f"MAIN URL STATUS: {status}, Size: {len(html_bytes) if html_bytes else 0} bytes")

if html_bytes:
    html = html_bytes.decode('utf-8', errors='ignore')
    
    # Extract assets
    scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
    stylesheets = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', html)
    anchors = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html)
    
    print("\n--- CHECKING SCRIPTS ---")
    for s in set(scripts):
        full = urljoin(base_url, s)
        st, b = check_url(full)
        print(f"Script: {s} -> {st} ({len(b) if b else 0}b)")
        
    print("\n--- CHECKING STYLESHEETS ---")
    for s in set(stylesheets):
        full = urljoin(base_url, s)
        st, b = check_url(full)
        print(f"CSS: {s} -> {st} ({len(b) if b else 0}b)")
        
    print("\n--- CHECKING INTERNAL LINKS ---")
    for a in set(anchors):
        if not a.startswith('#') and not a.startswith('javascript:'):
            full = urljoin(base_url, a)
            st, b = check_url(full)
            print(f"Link: {a} -> {st} ({len(b) if b else 0}b)")
