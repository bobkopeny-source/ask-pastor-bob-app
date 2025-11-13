
#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json, gzip, os

app = Flask(__name__)
CORS(app)

# Load only titles/URLs (tiny memory, no crash)
print("Loading titles...")
try:
    with gzip.open('PASTOR_BOB_COMPLETE_1712.json.gz', 'rt', encoding='utf-8') as f:
        data = json.load(f)
    SERMONS = [{'title': s['title'], 'date': s['date'][:10], 'url': s.get('url', '')} for s in data[:500]]  # Limit to 500 for free tier
    print(f"Loaded {len(SERMONS)} titles")
except Exception as e:
    print(f"Load error: {e}")
    SERMONS = []  # Fallback

def search(query):
    q = query.lower()
    results = [s for s in SERMONS if q in s['title'].lower()]
    return results[:10]

@app.route('/')
def home():
    return '''
    <h1>Ask Pastor Bob (952 Sermons)</h1>
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
            .catch(e => { status.innerHTML = "Error — check console."; console.log(e); });
    }
    </script>
    '''

@app.route('/api')
def api():
    q = request.args.get('q', '')
    results = search(q)
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
