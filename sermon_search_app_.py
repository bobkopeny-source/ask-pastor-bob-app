#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json, gzip, os, re
from functools import lru_cache

app = Flask(__name__)
CORS(app)

# === MEMORY-SAFE: Load only when needed ===
@lru_cache(maxsize=1)
def load_sermons():
    print("Loading 1,712 sermons (memory-safe)...")
    with gzip.open('PASTOR_BOB_COMPLETE_1712.json.gz', 'rt', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} sermons")
    return data

def search_sermons(query, max_results=10):
    sermons = load_sermons()
    q = query.lower()
    words = [w for w in q.split() if len(w) > 3]
    results = []
    for s in sermons:
        title = s.get('title', '').lower()
        transcript = s.get('transcript', '').lower()
        score = sum(title.count(w)*10 + transcript.count(w) for w in words)
        if score > 0:
            passages = [p.strip() for p in re.split(r'[.!?]', transcript) if any(w in p.lower() for w in words)][:3]
            results.append({
                'title': s.get('title'),
                'date': s.get('date', '')[:10],
                'url': s.get('url', ''),
                'passages': passages,
                'score': score
            })
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:max_results]

@app.route('/')
def home():
    return render_template_string('''
    <h1>Ask Pastor Bob (1,712 Sermons)</h1>
    <input type="text" id="q" placeholder="e.g., What does Pastor Bob say about faith?" style="width:100%;padding:12px;font-size:16px;">
    <button onclick="search()" style="padding:12px 20px;background:#007bff;color:white;border:none;cursor:pointer;font-size:16px;">Search</button>
    <div id="results" style="margin-top:20px;"></div>
    <script>
    function search() {
        const q = document.getElementById('q').value;
        if (!q) return;
        fetch(`/api/search?q=${encodeURIComponent(q)}`)
            .then(r => r.json())
            .then(d => {
                let html = `<h2>${d.results.length} results for "<i>${q}</i>"</h2>`;
                d.results.forEach(r => {
                    html += `<div style="margin:20px 0;padding:15px;background:white;border-radius:8px;box-shadow:0 2px 5px #ddd;">
                        <h3>${r.title} <small>(${r.date})</small></h3>
                        ${r.url ? `<a href="${r.url}" target="_blank" style="color:#007bff;">Watch Video</a><br><br>` : ''}
                        ${r.passages.map(p => `<p style="margin:8px 0;">${p}</p>`).join('')}
                    </div>`;
                });
                document.getElementById('results').innerHTML = html;
            });
    }
    </script>
    ''')

@app.route('/api/search')
def api():
    q = request.args.get('q', '')
    results = search_sermons(q)
    return jsonify({'results': results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
