from flask import Flask, request, render_template_string
import os
import tempfile
from ai_analyzer import (
    tokenize,
    analyze_keywords,
    KEYWORD_CATEGORIES,
    analyze_text_with_openai,
)

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<title>AI Analyzer Web</title>
<h1>Upload text files for analysis</h1>
<form method=post enctype=multipart/form-data action="/analyze">
  <input type=file name=files multiple required><br><br>
  <label><input type=checkbox name=use_ai> Use OpenAI analysis</label><br><br>
  <button type=submit>Analyze</button>
</form>
"""

RESULT_HTML = """
<!doctype html>
<title>Analysis Result</title>
<h1>Analysis Result</h1>
{% for res in results %}
  <h2>{{ res.filename }}</h2>
  <h3>Keyword Counts</h3>
  <ul>
  {% for cat, count in res.keyword_counts.items() %}
    <li>{{ cat }}: {{ count }}</li>
  {% endfor %}
  </ul>
  {% if res.ai_result %}
  <h3>AI Summary</h3>
  <pre>{{ res.ai_result | tojson(indent=2, ensure_ascii=False) }}</pre>
  {% endif %}
{% endfor %}
<a href="/">Back</a>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/analyze", methods=["POST"])
def analyze():
    uploaded_files = request.files.getlist("files")
    use_ai = bool(request.form.get("use_ai"))
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for f in uploaded_files:
            filename = os.path.basename(f.filename)
            path = os.path.join(tmpdir, filename)
            f.save(path)
            with open(path, "r", encoding="utf-8") as fp:
                text = fp.read()

            # keyword analysis
            keyword_counts, _ = analyze_keywords(text, KEYWORD_CATEGORIES)

            ai_result = None
            if use_ai:
                ai_result = analyze_text_with_openai(text)

            results.append({
                "filename": filename,
                "keyword_counts": keyword_counts,
                "ai_result": ai_result,
            })

    return render_template_string(RESULT_HTML, results=results)

if __name__ == "__main__":
    app.run(debug=True)
