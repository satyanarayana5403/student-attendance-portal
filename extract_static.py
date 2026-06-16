import os
import re

base_html_path = 'templates/base.html'
with open(base_html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract CSS
css_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
if css_match:
    css_content = css_match.group(1).strip()
    # Remove Jinja block from CSS (if any)
    css_content = re.sub(r'\{% block extra_css %\}\{% endblock %\}', '', css_content)
    
    os.makedirs('static/css', exist_ok=True)
    with open('static/css/style.css', 'w', encoding='utf-8') as f:
        f.write(css_content)

# Extract JS
# We want the script blocks at the end, specifically the one with the logic
js_match = re.search(r'<script>(.*?)</script>.*?</body>', content, re.DOTALL)
if js_match:
    js_content = js_match.group(1).strip()
    js_content = re.sub(r'\{% block extra_js %\}\{% endblock %\}', '', js_content)
    
    os.makedirs('static/js', exist_ok=True)
    with open('static/js/main.js', 'w', encoding='utf-8') as f:
        f.write(js_content)

# Replace in base.html
new_content = re.sub(r'<style>.*?</style>', '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/style.css\') }}">\n    {% block extra_css %}{% endblock %}', content, flags=re.DOTALL)
new_content = re.sub(r'<script>.*?</script>(\s*</body>)', r'<script src="{{ url_for(\'static\', filename=\'js/main.js\') }}"></script>\n    {% block extra_js %}{% endblock %}\1', new_content, flags=re.DOTALL)

with open(base_html_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Extraction complete.")
