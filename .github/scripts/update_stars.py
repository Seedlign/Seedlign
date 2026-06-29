#!/usr/bin/env python3
"""Refresh the starred-projects section of the profile README.

Fetches the user's most recently starred repos and rewrites the content
between the <!-- STARS:START --> and <!-- STARS:END --> markers.
Run by .github/workflows/update-stars.yml.
"""
import json
import os
import re
import sys
import urllib.request

USERNAME = os.environ.get("USERNAME", "Seedlign")
MAX = int(os.environ.get("MAX", "6"))
TOKEN = os.environ.get("GH_TOKEN", "")
README = "README.md"


def fetch_starred():
    url = f"https://api.github.com/users/{USERNAME}/starred?per_page={MAX}&sort=created"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def build_block(repos):
    if not repos:
        return '<p align="center"><em>No starred projects yet.</em></p>'
    lines = ['<p align="center">']
    for r in repos:
        full = r["full_name"]
        owner, name = full.split("/", 1)
        lines.append(f'  <a href="https://github.com/{full}">')
        lines.append(
            f'    <img src="https://github-readme-stats.vercel.app/api/pin/'
            f'?username={owner}&repo={name}&hide_border=true&theme=transparent" alt="{name}" />'
        )
        lines.append("  </a>")
    lines.append("</p>")
    return "\n".join(lines)


def main():
    repos = fetch_starred()
    block = build_block(repos)
    with open(README, encoding="utf-8") as f:
        text = f.read()
    new = re.sub(
        r"(<!-- STARS:START -->).*?(<!-- STARS:END -->)",
        lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}",
        text,
        flags=re.S,
    )
    if new == text:
        print("No changes.")
        return
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)
    print("README.md updated.")


if __name__ == "__main__":
    sys.exit(main())
