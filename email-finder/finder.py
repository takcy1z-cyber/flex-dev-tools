#!/usr/bin/env python3
"""
Email & Contact Finder - Extract contact info from websites.
Finds emails, phone numbers, social media links from any webpage.

Usage:
    python3 finder.py https://example.com
    python3 finder.py https://example.com --output contacts.csv
    python3 finder.py https://example.com --emails-only
"""

import argparse
import csv
import json
import re
import sys
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse


def fetch(url, timeout=10):
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
    })
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode(resp.headers.get_content_charset() or 'utf-8', errors='replace')


def find_emails(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))


def find_phones(text):
    pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    return list(set(re.findall(pattern, text)))


def find_social_links(html, base_url):
    social_patterns = {
        'twitter': r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+',
        'linkedin': r'https?://(?:www\.)?linkedin\.com/(?:in|company)/[a-zA-Z0-9-]+',
        'github': r'https?://(?:www\.)?github\.com/[a-zA-Z0-9-]+',
        'facebook': r'https?://(?:www\.)?facebook\.com/[a-zA-Z0-9.]+',
        'instagram': r'https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.]+',
    }
    results = {}
    for platform, pattern in social_patterns.items():
        matches = list(set(re.findall(pattern, html)))
        if matches:
            results[platform] = matches
    return results


def main():
    parser = argparse.ArgumentParser(description='Find emails, phones, and social links from websites')
    parser.add_argument('url', help='URL to scan')
    parser.add_argument('--output', '-o', help='Output file (csv or json)')
    parser.add_argument('--emails-only', action='store_true', help='Only find emails')
    parser.add_argument('--format', '-f', choices=['csv', 'json'], help='Output format')
    args = parser.parse_args()

    print(f"Scanning {args.url}...")
    html = fetch(args.url)
    
    # Strip HTML for text analysis
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)

    results = {}

    if args.emails_only:
        emails = find_emails(text)
        results = {'emails': emails}
        print(f"\nFound {len(emails)} email(s):")
        for e in emails:
            print(f"  {e}")
    else:
        emails = find_emails(text)
        phones = find_phones(text)
        social = find_social_links(html, args.url)
        
        results = {
            'url': args.url,
            'emails': emails,
            'phones': phones,
            'social': social
        }
        
        print(f"\nEmails ({len(emails)}):")
        for e in emails:
            print(f"  {e}")
        
        print(f"\nPhones ({len(phones)}):")
        for p in phones:
            print(f"  {p}")
        
        print(f"\nSocial Links:")
        for platform, links in social.items():
            print(f"  {platform}: {links[0]}")

    if args.output:
        fmt = args.format or ('json' if args.output.endswith('.json') else 'csv')
        if fmt == 'json':
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            with open(args.output, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['type', 'value'])
                for e in results.get('emails', []):
                    writer.writerow(['email', e])
                for p in results.get('phones', []):
                    writer.writerow(['phone', p])
                for platform, links in results.get('social', {}).items():
                    for link in links:
                        writer.writerow([platform, link])
        print(f"\nSaved to {args.output}")


if __name__ == '__main__':
    main()
