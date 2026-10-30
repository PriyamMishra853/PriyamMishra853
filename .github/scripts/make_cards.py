"""Draw self-hosted stats and repo cards into assets/ from the GitHub API."""
import json, os, urllib.request
from html import escape

USER = os.environ["GH_USER"]
PINS = ["VectorDB-", "SIH2025-", "YounifyAI-", "SystemDesignResources-"]
HEADERS = {"Accept": "application/vnd.github+json"}
if os.environ.get("GH_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
LANG_COLORS = {"JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572A5", "C++": "#f34b7d",
               "C": "#555555", "HTML": "#e34c26", "CSS": "#663399", "Java": "#b07219", "Jupyter Notebook": "#DA5B0B"}
FONT = 'font-family="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif"'
STYLE = "<style>.f{animation:f .6s ease-out backwards}@keyframes f{from{opacity:0;transform:translateY(6px)}}</style>"
GRAD = ('<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#ffb300"/>'
        '<stop offset=".5" stop-color="#ff5e62"/><stop offset="1" stop-color="#8a5cff"/></linearGradient></defs>')


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as r:
        return json.load(r)


user = get(f"https://api.github.com/users/{USER}")
repos = [r for r in get(f"https://api.github.com/users/{USER}/repos?per_page=100") if not r["fork"]]
langs = {}
for r in repos:
    for lang, n in get(r["languages_url"]).items():
        langs[lang] = langs.get(lang, 0) + n
total = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]

# Stats card: headline numbers on the left, language bar on the right.
W, H = 860, 200
commits = get(f"https://api.github.com/search/commits?q=author:{USER}&per_page=1")["total_count"]
nums = [("Public repos", len(repos)), ("Commits authored", commits),
        ("Followers", user["followers"]), ("Languages", len(langs))]
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" {FONT}>', STYLE, GRAD,
     f'<rect width="{W}" height="{H}" rx="14" fill="#0d1117" stroke="#30363d"/>',
     '<text x="28" y="40" fill="#ff5e62" font-size="17" font-weight="700">⚡ GitHub at a glance</text>']
for i, (label, n) in enumerate(nums):
    x, y = 28 + (i % 2) * 170, 92 + (i // 2) * 72
    o.append(f'<g class="f" style="animation-delay:{.1 + i * .12}s"><text x="{x}" y="{y}" fill="url(#g)" font-size="34" '
             f'font-weight="800">{n}</text><text x="{x}" y="{y + 22}" fill="#8b949e" font-size="13">{label}</text></g>')
o.append('<text x="400" y="40" fill="#ff5e62" font-size="17" font-weight="700">🧪 Code by language</text>')
x = 400.0
o.append('<clipPath id="bar"><rect x="400" y="60" width="430" height="12" rx="6"/></clipPath><g clip-path="url(#bar)">')
for lang, n in top:
    w = 430 * n / total
    o.append(f'<rect x="{x:.1f}" y="60" width="{w:.1f}" height="12" fill="{LANG_COLORS.get(lang, "#8a5cff")}"/>')
    x += w
o.append('</g>')
for i, (lang, n) in enumerate(top):
    lx, ly = 400 + (i % 2) * 215, 106 + (i // 2) * 30
    o.append(f'<g class="f" style="animation-delay:{.3 + i * .1}s"><circle cx="{lx + 6}" cy="{ly - 5}" r="6" '
             f'fill="{LANG_COLORS.get(lang, "#8a5cff")}"/><text x="{lx + 20}" y="{ly}" fill="#e6edf3" font-size="14">'
             f'{escape(lang)} <tspan fill="#8b949e">{100 * n / total:.1f}%</tspan></text></g>')
o.append('</svg>')
open("assets/stats.svg", "w", encoding="utf-8").write("".join(o))

# Repo cards.
by_name = {r["name"]: r for r in repos}
for name in PINS:
    r = by_name.get(name)
    if not r:
        continue
    desc = (r["description"] or "Work in progress, details coming soon.")[:58]
    lang = r["language"] or "Code"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 120" width="420" height="120" {FONT}>', GRAD,
         '<rect width="420" height="120" rx="12" fill="#0d1117" stroke="#30363d"/>',
         '<rect width="4" height="120" rx="2" fill="url(#g)"/>',
         f'<text x="22" y="36" fill="#ff5e62" font-size="17" font-weight="700">📦 {escape(name.rstrip("-"))}</text>',
         f'<text x="22" y="64" fill="#8b949e" font-size="13">{escape(desc)}</text>',
         f'<circle cx="28" cy="94" r="6" fill="{LANG_COLORS.get(lang, "#8a5cff")}"/>',
         f'<text x="40" y="99" fill="#e6edf3" font-size="13">{escape(lang)}</text>',
         f'<text x="150" y="99" fill="#e6edf3" font-size="13">⭐ {r["stargazers_count"]}   🍴 {r["forks_count"]}</text>',
         '</svg>']
    open(f"assets/pin-{name.rstrip('-').lower()}.svg", "w", encoding="utf-8").write("".join(o))
