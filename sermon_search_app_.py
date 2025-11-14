#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json, gzip, os, re
from functools import lru_cache

app = Flask(__name__)
CORS(app)

# Debug logging
print("=== APP STARTUP ===")
print(f"Files: {os.listdir('.')}")
print("=== END STARTUP ===")

# Lazy load with error handling
@lru_cache(maxsize=1)
def load_sermons():
    print("=== LOADING DB ===")
    try:
        if not os.path.exists('PASTOR_BOB_COMPLETE_1712.json.gz'):
            print("DB FILE MISSING!")
            return []
        with gzip.open('PASTOR_BOB_COMPLETE_1712.json.gz', 'rt', encoding='utf-8') as f:
            data = json.load(f)
        print(f"=== LOADED {len(data)} SERMONS ===")
        return data
    except Exception as e:
        print(f"=== DB ERROR: {e} ===")
        return []

def search_sermons(query):
    print(f"=== SEARCH: '{query}' ===")
    sermons = load_sermons()
    print(f"=== {len(sermons)} SERMONS AVAILABLE ===")
    q = query.lower()
    words = [w for w in q.split() if len(w) > 3]
    results = []
    for s in sermons[:100]:  # Limit for speed
        title = s.get('title', '').lower()
        score = sum(title.count(w)*10 for w in words)
        if score > 0:
            results.append({
                'title': s.get('title'),
                'date': s.get('date', '')[:10],
                'url': s.get('url', '')
            })
            print(f"=== MATCH: {s.get('title')[:50]} ===")
    print(f"=== {len(results)} RESULTS ===")
    return results

@app.route('/')
def home():
    return '''
    <h1>Ask Pastor Bob (1,712 Sermons)</h1>
    <input id="q" placeholder="e.g., faith" style="width:100%;padding:12px;font-size:16px;">
    <button onclick="search()">Search</button>
    <div id="status" style="margin:10px 0;color:#007bff;"></div>
    <div id="results"></div>
    <script>
    function search() {
        const q = document.getElementById('q').value;
        const status = document.getElementById('status');
        if (!q) return;
        status.innerHTML = "Searching...";
        fetch(`/api?q=${encodeURIComponent(q)}`)
            .then(r => {
                if (!r.ok) throw new Error('API error: ' + r.status);
                return r.json();
            })
            .then(d => {
                let html = d.length ? `<h2>${d.length} results</h2>` : '<p>No results. Try "faith".</p>';
                d.forEach(r => {
                    html += `<div style="margin:20px 0;padding:15px;background:white;border-radius:8px;">
                        <h3>${r.title} (${r.date})</h3>
                        ${r.url ? `<a href="${r.url}" target="_blank">Watch Video</a>` : ''}
                    </div>`;
                });
                document.getElementById('results').innerHTML = html;
                status.innerHTML = "";
            })
            .catch(e => { status.innerHTML = "Error: " + e.message; console.log(e); });
    }
    </script>
    '''

@app.route('/api')
def api():
    q = request.args.get('q', '')
    results = search_sermons(q)
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
