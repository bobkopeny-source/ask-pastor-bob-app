#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json, gzip, os, re
from functools import lru_cache

app = Flask(__name__)
CORS(app)

# Lazy load DB (no startup crash)
@lru_cache(maxsize=1)
def load_sermons():
    print("Loading 1,712 sermons on first search...")
    try:
        with gzip.open('PASTOR_BOB_COMPLETE_1712.json.gz', 'rt', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} sermons")
        return data
    except Exception as e:
        print(f"DB error: {e}")
        return []

def search_sermons(query):
    sermons = load_sermons()
    q = query.lower()
    words = [w for w in q.split() if len(w) > 3]
    results = []
    for s in sermons:
        title = s.get('title', '').lower()
        score = sum(title.count(w)*10 for w in words)
        if score > 0:
            results.append({
                'title': s.get('title'),
                'date': s.get('date', '')[:10],
                'url': s.get('url', '')
            })
        if len(results) >= 10:
            break
    return sorted(results, key=lambda x: -sum(x['title'].lower().count(w) for w in words))

@app.route('/')
def home():
    return '''
    <h1>Ask Pastor Bob (1,712 Sermons)</h1>
    <input id="q" placeholder="e.g., faith" style="width:100%;padding:12px;font-size:16px;">
    <button onclick="search()" style="padding:12px 20px;background:#007bff;color:white;border:none;cursor:pointer;font-size:16px;">Search</button>
    <div id="status" style="margin:10px 0;color:#007bff;"></div>
    <div id="results" style="margin-top:20px;"></div>
    <script>
    function search() {
        const q = document.getElementById('q').value;
        const status = document.getElementById('status');
        if (!q) return;
        status.innerHTML = "Searching...";
        fetch(`/api?q=${encodeURIComponent(q)}`)
            .then(r => r.json())
            .then(d => {
                let html = d.length ? `<h2>${d.length} results</h2>` : '<p>No results. Try "faith" or "Israel".</p>';
                d.forEach(r => {
                    html += `<div style="margin:20px 0;padding:15px;background:white;border-radius:8px;box-shadow:0 2px 5px #ddd;">
                        <h3>${r.title} (${r.date})</h3>
                        ${r.url ? `<a href="${r.url}" target="_blank" style="color:#007bff;">Watch Video</a>` : ''}
                    </div>`;
                });
                document.getElementById('results').innerHTML = html;
                status.innerHTML = "";
            })
            .catch(() => { status.innerHTML = "Error"; });
    }
    </script>
    '''

@app.route('/api')
def api():
    q = request.args.get('q', '')
    results = search_sermons(q)
    return jsonify(results)

if __name__ == '__main__':
    # DigitalOcean requires port 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
