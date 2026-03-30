#!/usr/bin/env python3
"""
Universal Web Scraper - A clean, sellable scraping tool.
Extracts data from any website and exports to CSV/JSON.

Usage:
    python3 scraper.py <url> --selector "css-selector" --output data.csv
    python3 scraper.py <url> --selector "css-selector" --output data.json
    python3 scraper.py <url> --mode links --output links.csv
    python3 scraper.py <url> --mode text --output content.txt
"""

import argparse
import csv
import json
import sys
import re
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser


class SimpleScraper(HTMLParser):
    """Lightweight HTML scraper using only stdlib."""
    
    def __init__(self):
        super().__init__()
        self.results = []
        self.current_tag = None
        self.current_attrs = {}
        self.current_text = []
        self.links = []
        self.all_text = []
        self.in_target = False
        self.depth = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag
        self.current_attrs = attrs_dict
        if tag == 'a' and attrs_dict.get('href'):
            href = attrs_dict['href']
            text = ''
            self.links.append({'url': href, 'text': ''})
        if tag in ('script', 'style', 'noscript'):
            return
        self.all_text.append('')
            
    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.links and not self.links[-1].get('text'):
                self.links[-1]['text'] = text
            self.all_text.append(text)
            
    def handle_endtag(self, tag):
        pass


def fetch_page(url):
    """Fetch page content using stdlib urllib."""
    import urllib.request
    import urllib.error
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read()
            charset = response.headers.get_content_charset() or 'utf-8'
            return content.decode(charset, errors='replace')
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def extract_by_selector(html, selector):
    """Extract elements matching a simple CSS selector."""
    results = []
    
    # Parse simple tag selectors and class selectors
    tag_match = re.match(r'^(\w+)$', selector)
    class_match = re.match(r'^\.(\w[\w-]*)$', selector)
    id_match = re.match(r'^#(\w[\w-]*)$', selector)
    tag_class_match = re.match(r'^(\w+)\.(\w[\w-]*)$', selector)
    
    if tag_class_match:
        tag, cls = tag_class_match.groups()
        pattern = rf'<{tag}[^>]*class="[^"]*\b{cls}\b[^"]*"[^>]*>(.*?)</{tag}>'
    elif tag_match:
        tag = tag_match.group(1)
        pattern = rf'<{tag}[^>]*>(.*?)</{tag}>'
    elif class_match:
        cls = class_match.group(1)
        pattern = rf'<(\w+)[^>]*class="[^"]*\b{cls}\b[^"]*"[^>]*>(.*?)</\1>'
    elif id_match:
        id_val = id_match.group(1)
        pattern = rf'<(\w+)[^>]*id="{id_val}"[^>]*>(.*?)</\1>'
    else:
        # Fallback: try as tag
        pattern = rf'<{re.escape(selector)}[^>]*>(.*?)</{re.escape(selector)}>'
    
    for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
        content = match.group(match.lastindex) if match.lastindex else match.group(1)
        # Strip HTML tags for clean text
        clean = re.sub(r'<[^>]+>', ' ', content)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if clean:
            results.append(clean)
    
    return results


def extract_links(html, base_url):
    """Extract all links from HTML."""
    links = []
    for match in re.finditer(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE):
        href = match.group(1)
        text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        full_url = urljoin(base_url, href)
        if full_url.startswith('http'):
            links.append({'url': full_url, 'text': text or ''})
    return links


def extract_text(html):
    """Extract clean text from HTML."""
    # Remove script and style blocks
    text = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '\n', text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


def export_csv(data, output_file, headers=None):
    """Export data to CSV."""
    if not data:
        print("No data to export.", file=sys.stderr)
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if isinstance(data[0], dict):
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        else:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            for item in data:
                writer.writerow([item] if not isinstance(item, (list, tuple)) else item)
    
    print(f"✅ Exported {len(data)} items to {output_file}")


def export_json(data, output_file):
    """Export data to JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported {len(data)} items to {output_file}")


def export_text(text, output_file):
    """Export text to file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"✅ Exported text to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Universal Web Scraper - Extract data from any website',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com --selector "h2" --output titles.csv
  %(prog)s https://example.com --mode links --output links.csv
  %(prog)s https://example.com --mode text --output page.txt
  %(prog)s https://example.com --selector ".product" --output products.json
        """
    )
    parser.add_argument('url', help='URL to scrape')
    parser.add_argument('--selector', '-s', help='CSS selector (tag, .class, #id, tag.class)')
    parser.add_argument('--mode', '-m', choices=['links', 'text'], help='Extraction mode')
    parser.add_argument('--output', '-o', required=True, help='Output file (csv, json, or txt)')
    parser.add_argument('--format', '-f', choices=['csv', 'json', 'text'], help='Output format (auto-detected from extension)')
    
    args = parser.parse_args()
    
    # Auto-detect format from extension
    fmt = args.format
    if not fmt:
        ext = args.output.rsplit('.', 1)[-1].lower() if '.' in args.output else ''
        fmt = {'csv': 'csv', 'json': 'json', 'txt': 'text', 'md': 'text'}.get(ext, 'csv')
    
    print(f"🔍 Fetching {args.url}...")
    html = fetch_page(args.url)
    
    if args.mode == 'links':
        print("🔗 Extracting links...")
        data = extract_links(html, args.url)
        if fmt == 'json':
            export_json(data, args.output)
        else:
            export_csv(data, args.output, headers=['url', 'text'])
    
    elif args.mode == 'text':
        print("📄 Extracting text...")
        text = extract_text(html)
        export_text(text, args.output)
    
    elif args.selector:
        print(f"🎯 Extracting elements matching '{args.selector}'...")
        data = extract_by_selector(html, args.selector)
        if fmt == 'json':
            export_json(data, args.output)
        else:
            export_csv(data, args.output, headers=['content'])
    
    else:
        print("Please specify --selector, --mode links, or --mode text", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
