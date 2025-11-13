#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json, gzip, os, re

app = Flask(__name__)
CORS(app)

# Load DB once at startup (safe chunked)
print("Loading database...")
try:
    with gzip.open('PASTOR_BOB_COMPLETE_1712.json.gz', 'rt', encoding='utf-8') as f:
        SERMONS = json.load(f)
    print(f"Loaded {len(SERMONS)} sermons")
except Exception as e:
    print(f"DB LOAD ERROR: {e}")
    SERMONS = []

def search_sermons(query, max_results=10):
    if not SERMONS:
        return [{'title': 'Error', 'passages': ['Database not loaded. Check logs.']}]
    
    q = query.lower()
    words = [w for w in q.split() if len(w) > 3]
    if not words:
        return []
    
    results = []
    for s in SERMONS:  # Process all, but fast
        title = s.get('title', '').lower()
        transcript = s.get('transcript', '').lower()
        score = sum(title.count(w)*10 + transcript.count(w) for w in words)
        if score > 0:
            passages = [p.strip() for p in re.split(r'[.!?]', transcript) if any(w in p.lower() for w in words)][:3]
            results.append({
                'title': s.get('title'),
                'date': s.get('date', '')[:10],
                'url': s.get('url', ''),
                'passages': passages
            })
        if len(results) >= max_results:
            break
    return results

@app.route('/')
def home():
    return '''
    <h1>Ask Pastor Bob (1,712 Sermons)</h1>
    <input id="q" placeholder="e.g., faith" style="width:100%;padding:12px;font-size:16px;">
    <button onclick="search()" id="btn">Search</button>
    <div id="status" style="margin:10px 0; color:#007bff;"></div>
    <div id="results"></div>
    <script>
    function search() {
        const q = document.getElementById('q').value;
        const btn = document.getElementById('btn');
        const status = document.getElementById('status');
        if (!q) return;
        btn.disabled = true;
        status.innerHTML = "Searching 1,712 sermons...";
        fetch(`/api/search?q=${encodeURIComponent(q)}`)
            .then(r => r.json())
            .then(d => {
                let html = d.length ? `<h2>${d.length} results for "${q}"</h2>` : '<p>No results found.</p>';
                d.forEach(r => {
                    html += `<div style="margin:20px 0;padding:15px;background:white;border-radius:8px;">
                        <h3>${r.title} (${r.date})</h3>
                        ${r.url ? `<a href="${r.url}" target="_blank">Watch Video</a><br>` : ''}
                        ${r.passages.map(p => `<p>${p}</p>`).join('')}
                    </div>`;
                });
                document.getElementById('results').innerHTML = html;
                status.innerHTML = "";
                btn.disabled = false;
            })
            .catch(e => {
                status.innerHTML = "Error — check Render logs.";
                btn.disabled = false;
            });
    }
    </script>
    '''

@app.route('/api/search')
def api():
    q = request.args.get('q', '')
    results = search_sermons(q)
    return jsonify(results)
