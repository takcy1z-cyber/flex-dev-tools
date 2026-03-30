# 💪 Flex Developer Tools

Three powerful Python developer tools. **Zero dependencies.** Pure stdlib. Works anywhere Python 3 runs.

[⭐ Star this repo](https://github.com/takcy1z-cyber/flex-dev-tools) if you find it useful!

---

## 🕷️ Web Scraper

Extract data from any website. CSS selectors, link extraction, text extraction. Export to CSV or JSON.

```bash
# Extract headlines from Hacker News
python3 scraper.py https://news.ycombinator.com --selector ".titleline" --output titles.csv

# Get all links from a page
python3 scraper.py https://example.com --mode links --output links.json

# Extract clean text
python3 scraper.py https://example.com --mode text --output content.txt
```

**Features:**
- CSS selector support (tag, `.class`, `#id`, `tag.class`)
- Link extraction with full URL resolution
- Clean text extraction (strips HTML, scripts, styles)
- CSV and JSON export
- Custom User-Agent headers

---

## 👁️ Site Monitor

Monitor websites for uptime and content changes. Watch mode with interval polling.

```bash
# Quick health check
python3 monitor.py check https://mysite.com

# Check multiple sites
python3 monitor.py status https://site1.com https://site2.com https://site3.com

# Watch for changes (checks every 30 seconds)
python3 monitor.py watch https://mysite.com --interval 30 --notify "Content changed!"
```

**Features:**
- Uptime detection with HTTP status codes
- Response time measurement
- Content change detection (SHA-256 hashing)
- Multi-site monitoring
- Persistent state tracking
- Custom check intervals

---

## 🚀 API Builder

Turn any CSV or JSON file into a full REST API in seconds. Filtering, search, sorting, pagination — all built in.

```bash
# Start an API from a CSV file
python3 apibuilder.py serve data.csv --port 8080

# Start an API from JSON
python3 apibuilder.py serve products.json --port 3000

# Preview the schema
python3 apibuilder.py schema data.json
```

**Auto-generated endpoints:**
| Endpoint | Description |
|----------|-------------|
| `GET /api` | API documentation |
| `GET /api/data` | List all records (with filtering, search, pagination) |
| `GET /api/data/:id` | Get single item by index |
| `GET /api/schema` | Data schema and sample |
| `GET /api/health` | Health check |

**Query parameters:**
- `?search=keyword` — Full-text search across all fields
- `?sort_by=field&sort_order=desc` — Sort results
- `?offset=0&limit=50` — Pagination
- `?fields=name,email` — Select specific fields
- `?field_name=value` — Filter by exact value

---

## 📦 Installation

No installation needed! Just Python 3.6+.

```bash
git clone https://github.com/takcy1z-cyber/flex-dev-tools.git
cd flex-dev-tools
```

That's it. Run any tool directly.

---

## 💰 Buy the Pack

| Option | Price |
|--------|-------|
| All 3 tools | $25 |
| Single tool | $10 |

**Payment (SOL/USDC on Solana):**
```
FnZKAw74KDx1vPoZ8B9jDa3cLAVKqc29yaBGpumVEJWJ
```

After payment, DM with your transaction ID.

---

## 📄 License

Commercial use allowed. You get full source code to customize and use in your projects.

---

## Built by Flex 💪

*Zero dependencies. Pure power.*
