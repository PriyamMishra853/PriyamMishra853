"""Rewrite the live-activity block in README.md from the GitHub API."""
import json, os, re, urllib.request
from datetime import datetime, timezone

USER = os.environ["GH_USER"]
HEADERS = {"Authorization": f"Bearer {os.environ['GH_TOKEN']}", "Accept": "application/vnd.github+json"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as r:
        return json.load(r)


def ago(ts):
    s = (datetime.now(timezone.utc) - datetime.fromisoformat(ts.replace("Z", "+00:00"))).total_seconds()
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if s >= n:
            return f"{int(s // n)}{unit} ago"
    return "just now"


lines, seen = [], set()
for e in get(f"https://api.github.com/users/{USER}/events/public?per_page=100"):
    repo = e["repo"]["name"]
    if repo == f"{USER}/{USER}":
        continue
    name, t, p = repo.split("/")[1], e["type"], e["payload"]
    if t == "PushEvent":
        msg = (p.get("commits") or [{}])[-1].get("message", "").splitlines()[0][:60] if p.get("commits") else "pushed code"
        text = f"🔨 Pushed to **{name}**: `{msg}`"
    elif t == "CreateEvent" and p.get("ref_type") == "repository":
        text = f"✨ Created **{name}**"
    elif t == "PullRequestEvent":
        text = f"🔀 {p['action'].capitalize()} PR in **{name}**"
    elif t == "WatchEvent":
        text = f"⭐ Starred **{name}**"
    else:
        continue
    key = (t, name)
    if key in seen:
        continue
    seen.add(key)
    lines.append(f"| {text} | <sub>{ago(e['created_at'])}</sub> |")
    if len(lines) == 6:
        break

if not lines:
    lines = ["| 💤 Quiet right now: probably configuring the M5 | |"]

now = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
block = "\n".join(["| What I've been up to | When |", "|:--|--:|", *lines, "", f"<sub>🤖 This section updates itself every 6 hours · last sync {now}</sub>"])
path = "README.md"
s = open(path, encoding="utf-8").read()
s = re.sub(r"(<!-- LIVE:START -->\n).*?(\n<!-- LIVE:END -->)", lambda m: m.group(1) + block + m.group(2), s, flags=re.S)
open(path, "w", encoding="utf-8").write(s)
