#!/usr/bin/env python3
"""
API Builder - Generate a REST API from any data source in seconds.
Turns CSV, JSON, or a Python list into a full API with filtering, pagination, search.

Usage:
    python3 apibuilder.py serve data.json --port 8080
    python3 apibuilder.py serve data.csv --port 8080
    python3 apibuilder.py schema data.json
"""

import argparse
import csv
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes


class DataStore:
    """Simple in-memory data store."""
    
    def __init__(self, data, fields=None):
        self.data = data
        self.fields = fields or (list(data[0].keys()) if data else [])
    
    @classmethod
    def from_json(cls, filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get('data', data.get('items', [data]))
        return cls(data)
    
    @classmethod
    def from_csv(cls, filepath):
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        return cls(data)
    
    def query(self, filters=None, search=None, sort_by=None, sort_order='asc', 
              offset=0, limit=50, fields=None):
        """Query data with filters, search, sorting, pagination."""
        results = self.data[:]
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                results = [r for r in results if str(r.get(key, '')).lower() == value.lower()]
        
        # Apply search
        if search:
            search_lower = search.lower()
            results = [
                r for r in results
                if any(search_lower in str(v).lower() for v in r.values())
            ]
        
        # Apply sorting
        if sort_by and sort_by in self.fields:
            reverse = sort_order.lower() == 'desc'
            results.sort(key=lambda x: str(x.get(sort_by, '')), reverse=reverse)
        
        total = len(results)
        results = results[offset:offset + limit]
        
        # Field selection
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
            results = [{k: v for k, v in r.items() if k in field_list} for r in results]
        
        return {
            'data': results,
            'meta': {
                'total': total,
                'offset': offset,
                'limit': limit,
                'count': len(results)
            }
        }


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the API."""
    
    datastore = None
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # Flatten single-value params
        params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        
        if path == '/' or path == '/api':
            self.send_json({
                'name': 'API Builder',
                'version': '1.0.0',
                'endpoints': {
                    'GET /api/data': 'Get all data (with filtering, search, pagination)',
                    'GET /api/data/:id': 'Get single item by index',
                    'GET /api/schema': 'Get data schema',
                    'GET /api/health': 'Health check'
                },
                'params': {
                    'search': 'Full-text search',
                    'sort_by': 'Sort by field',
                    'sort_order': 'asc or desc',
                    'offset': 'Pagination offset',
                    'limit': 'Items per page (default 50)',
                    'fields': 'Comma-separated field list',
                    '{field}': 'Filter by exact field value'
                }
            })
        
        elif path == '/api/health':
            self.send_json({'status': 'ok', 'records': len(self.datastore.data)})
        
        elif path == '/api/schema':
            schema = {}
            if self.datastore.data:
                sample = self.datastore.data[0]
                for k, v in sample.items():
                    schema[k] = type(v).__name__
            self.send_json({'fields': self.datastore.fields, 'sample_types': schema, 'count': len(self.datastore.data)})
        
        elif path.startswith('/api/data/'):
            try:
                idx = int(path.split('/')[-1])
                if 0 <= idx < len(self.datastore.data):
                    self.send_json(self.datastore.data[idx])
                else:
                    self.send_error(404, 'Not found')
            except ValueError:
                self.send_error(400, 'Invalid index')
        
        elif path == '/api/data':
            # Extract query params
            filters = {k: v for k, v in params.items() 
                      if k not in ('search', 'sort_by', 'sort_order', 'offset', 'limit', 'fields')}
            
            result = self.datastore.query(
                filters=filters,
                search=params.get('search'),
                sort_by=params.get('sort_by'),
                sort_order=params.get('sort_order', 'asc'),
                offset=int(params.get('offset', 0)),
                limit=int(params.get('limit', 50)),
                fields=params.get('fields')
            )
            self.send_json(result)
        
        else:
            self.send_error(404, 'Not found')
    
    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        print(f"  {args[0]}")


def main():
    parser = argparse.ArgumentParser(description='API Builder - Generate a REST API from data')
    sub = parser.add_subparsers(dest='command')
    
    p_serve = sub.add_parser('serve', help='Start API server')
    p_serve.add_argument('file', help='Data file (JSON or CSV)')
    p_serve.add_argument('--port', '-p', type=int, default=8080)
    p_serve.add_argument('--host', default='0.0.0.0')
    
    p_schema = sub.add_parser('schema', help='Show data schema')
    p_schema.add_argument('file', help='Data file (JSON or CSV)')
    
    args = parser.parse_args()
    
    if args.command == 'schema':
        ext = args.file.rsplit('.', 1)[-1].lower()
        store = DataStore.from_json(args.file) if ext == 'json' else DataStore.from_csv(args.file)
        print(json.dumps({
            'fields': store.fields,
            'count': len(store.data),
            'sample': store.data[:3] if store.data else []
        }, indent=2))
    
    elif args.command == 'serve':
        ext = args.file.rsplit('.', 1)[-1].lower()
        store = DataStore.from_json(args.file) if ext == 'json' else DataStore.from_csv(args.file)
        APIHandler.datastore = store
        
        server = HTTPServer((args.host, args.port), APIHandler)
        print(f"🚀 API running at http://{args.host}:{args.port}")
        print(f"📊 {len(store.data)} records loaded from {args.file}")
        print(f"📖 Docs at http://{args.host}:{args.port}/api")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
