#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json, gzip, os, re

app = Flask(__name__)
CORS(app)

# Tiny index: title, date, url, id, keywords
INDEX = []
DB = []

print("Building tiny index...")
with gzip.open('PASTOR_BOB_COMPLETE_1712.json.gz', 'rt', encoding='utf-8') as f:
    DB = json.load(f)

for s in DB:
    title = s.get('title', '').lower()
    words = re.findall(r'\b\w+\b', title)
    INDEX.append({
        'id': s.get('id'),
        'title': s.get('title'),
        'date': s.get('date', '')[:10],
        'url': s.get('url', ''),
        'keywords': [w for w in words if len(w) > 3]
    })
print(f"Index ready: {len(INDEX)} entries")

def search_index(query):
    q = query.lower()
    words = [w for w in q.split() if len(w) > 3]
    results = []
    for item in INDEX:
        score = sum(item['keywords'].count(w) for w in words)
        if score > 0:
            results.append((score, item))
    results.sort(reverse=True)
    return [item for score, item in results[:10]]

def get_sermon_by_id(sid):
    for s in DB:
        if s.get('id') == sid:
            return s
    return None

@app.route('/')
def home():
    return '''
    <h1>Ask Pastor Bob (1,712 Sermons)</h1>
    <input id="q" placeholder="e.g., faith" style="width:100%;padding:12px;">
    <button onclick="search()">Search</button>
    <div id="status"></div>
    <div id="results"></div>
    <script>
    function search() {
        const q = document.getElementById('q').value;
        const status = document.getElementById('status');
        status.innerHTML = "Searching...";
        fetch(`/api/search?q=${encodeURIComponent(q)}`)
            .then(r => r.json())
            .then(d => {
                let html = d.length ? `<h2>${d.length} results</h2>` : '<p>No results.</p>';
                d.forEach(r => {
                    html += `<div style="margin:20px 0;padding:15px;background:white;border-radius:8px;">
                        <h3>${r.title} (${r.date})</h3>
                        ${r.url ? `<a href="${r.url}" target="_blank">Watch Video</a>` : ''}
                        <p><i>Full transcript available on click.</i></p>
                    </div>`;
                });
                document.getElementById('results').innerHTML = html;
                status.innerHTML = "";
            });
    }
    </script>
    '''

@app.route('/api/search')
def api():
    q = request.args.get('q', '')
    results = search_index(q)
    return jsonify([{
        'title': r['title'],
        'date': r['date'],
        'url': r['url']
    } for r in results])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
