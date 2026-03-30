#!/usr/bin/env python3
"""
Site Monitor - Uptime & Change Detection Tool
Monitors websites for changes and downtime. Sells for $20-40.

Usage:
    python3 monitor.py check https://example.com
    python3 monitor.py watch https://example.com --interval 60 --notify "Site changed!"
    python3 monitor.py status https://example.com https://google.com https://github.com
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import ssl

STATE_FILE = os.path.expanduser('~/.site_monitor_state.json')


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def fetch(url, timeout=10):
    """Fetch URL and return (status_code, content_hash, response_time_ms, headers)."""
    ctx = ssl.create_default_context()
    req = Request(url, headers={
        'User-Agent': 'SiteMonitor/1.0',
    })
    
    start = time.time()
    try:
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            content = resp.read()
            elapsed = (time.time() - start) * 1000
            content_hash = hashlib.sha256(content).hexdigest()
            return {
                'status': resp.status,
                'hash': content_hash,
                'time_ms': round(elapsed),
                'size': len(content),
                'headers': dict(resp.headers),
                'error': None
            }
    except HTTPError as e:
        elapsed = (time.time() - start) * 1000
        return {
            'status': e.code,
            'hash': None,
            'time_ms': round(elapsed),
            'size': 0,
            'headers': {},
            'error': f"HTTP {e.code}: {e.reason}"
        }
    except (URLError, OSError) as e:
        elapsed = (time.time() - start) * 1000
        return {
            'status': 0,
            'hash': None,
            'time_ms': round(elapsed),
            'size': 0,
            'headers': {},
            'error': str(e)
        }


def cmd_check(args):
    """Check a single URL."""
    print(f"Checking {args.url}...")
    result = fetch(args.url)
    
    if result['error']:
        print(f"❌ DOWN - {result['error']} ({result['time_ms']}ms)")
        return 1
    
    status_emoji = '✅' if result['status'] == 200 else '⚠️'
    print(f"{status_emoji} {result['status']} - {result['time_ms']}ms - {result['size']} bytes")
    return 0 if result['status'] == 200 else 1


def cmd_status(args):
    """Check multiple URLs."""
    results = []
    for url in args.urls:
        result = fetch(url)
        results.append((url, result))
    
    print(f"\n{'URL':<50} {'Status':<10} {'Time':<10} {'Health'}")
    print('-' * 80)
    
    for url, r in results:
        short_url = url[:48] + '..' if len(url) > 50 else url
        if r['error']:
            print(f"{short_url:<50} {'ERR':<10} {r['time_ms']}ms{'':<4} ❌ {r['error'][:30]}")
        else:
            emoji = '✅' if r['status'] == 200 else '⚠️'
            print(f"{short_url:<50} {r['status']:<10} {r['time_ms']}ms{'':<4} {emoji}")
    
    return 0


def cmd_watch(args):
    """Watch a URL for changes."""
    state = load_state()
    url = args.url
    interval = args.interval
    
    print(f"👁️  Watching {url} every {interval}s")
    print("Press Ctrl+C to stop\n")
    
    prev_hash = state.get(url, {}).get('hash')
    check_count = 0
    
    try:
        while True:
            result = fetch(url)
            check_count += 1
            now = datetime.now().strftime('%H:%M:%S')
            
            if result['error']:
                print(f"[{now}] ❌ DOWN - {result['error']}")
            elif prev_hash and result['hash'] != prev_hash:
                print(f"[{now}] 🔄 CHANGED! Content differs from last check")
                if args.notify:
                    print(f"  📢 {args.notify}")
            else:
                print(f"[{now}] ✅ OK - {result['status']} - {result['time_ms']}ms (check #{check_count})")
            
            prev_hash = result['hash']
            state[url] = {
                'hash': result['hash'],
                'last_check': now,
                'status': result['status'],
                'time_ms': result['time_ms']
            }
            save_state(state)
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Stopped after {check_count} checks")
        save_state(state)
        return 0


def main():
    parser = argparse.ArgumentParser(description='Site Monitor - Uptime & Change Detection')
    sub = parser.add_subparsers(dest='command')
    
    # check
    p_check = sub.add_parser('check', help='Check a single URL')
    p_check.add_argument('url')
    
    # status
    p_status = sub.add_parser('status', help='Check multiple URLs')
    p_status.add_argument('urls', nargs='+')
    
    # watch
    p_watch = sub.add_parser('watch', help='Watch URL for changes')
    p_watch.add_argument('url')
    p_watch.add_argument('--interval', '-i', type=int, default=60, help='Check interval in seconds')
    p_watch.add_argument('--notify', '-n', help='Message to show on change')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        return cmd_check(args)
    elif args.command == 'status':
        return cmd_status(args)
    elif args.command == 'watch':
        return cmd_watch(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main() or 0)
