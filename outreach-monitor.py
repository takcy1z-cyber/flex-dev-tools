#!/usr/bin/env python3
"""
Outreach Monitor - Find potential customers on GitHub
Searches for issues where people need scraping, monitoring, or API tools.
"""
import json
import subprocess
import os
from datetime import datetime, timedelta

STATE_FILE = os.path.expanduser('~/.openclaw/workspace/data/outreach_state.json')

SEARCHES = [
    "need scraper python",
    "csv to api",
    "site monitoring uptime",
    "looking for python developer",
    "web scraping help",
    "data extraction python",
]

COMMENT_TEMPLATE = """Hey! I built a tool that might help with this — {tool_description}

{code_example}

Zero dependencies, pure Python. Check it out: https://github.com/takcy1z-cyber/flex-dev-tools

Happy to help if you have questions!"""

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"commented": [], "last_run": None}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def search_issues(query, limit=5):
    try:
        result = subprocess.run(
            ['gh', 'search', 'issues', query, '--limit', str(limit),
             '--json', 'title,url,repository,createdAt,state'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Error searching: {e}")
    return []

def main():
    state = load_state()
    commented = set(state.get("commented", []))
    new_opportunities = []
    
    for query in SEARCHES:
        issues = search_issues(query)
        for issue in issues:
            url = issue['url']
            if url in commented or issue['state'] != 'open':
                continue
            
            # Skip old issues (more than 6 months)
            created = issue['createdAt'][:10]
            if created < (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'):
                continue
            
            new_opportunities.append({
                'url': url,
                'title': issue['title'],
                'repo': issue['repository']['nameWithOwner'],
                'created': created,
                'query': query
            })
    
    print(f"\n🔍 Found {len(new_opportunities)} new opportunities:")
    for opp in new_opportunities:
        print(f"  [{opp['created']}] {opp['repo']}: {opp['title'][:60]}")
        print(f"    {opp['url']}")
    
    state["last_run"] = datetime.now().isoformat()
    save_state(state)
    
    return new_opportunities

if __name__ == '__main__':
    main()
