#!/usr/bin/env python3
"""Refresh the projects section of the profile README.

The displayed list combines, in order:
  1. Manually featured repos listed in .github/featured_repos.txt
     (one "owner/repo" per line; lines starting with # are ignored).
  2. The user's own starred repos, to fill the remaining slots up to MAX.

Rewrites the content between the <!-- STARS:START --> and <!-- STARS:END -->
markers. Run by .github/workflows/update-stars.yml.
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
FEATURED_FILE = ".github/featured_repos.txt"


def read_featured():
    # Manually curated "owner/repo" entries that always appear, in file order.
    if not os.path.exists(FEATURED_FILE):
        return []
    out = []
    with open(FEATURED_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "/" in line:
                out.append(line)
    return out


def fetch_own_starred():
    # Pull up to 100 most-recent stars, then keep only repos owned by USERNAME.
    url = f"https://api.github.com/users/{USERNAME}/starred?per_page=100&sort=created"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as resp:
        repos = json.load(resp)
    return [
        r["full_name"]
        for r in repos
        if r["owner"]["login"].lower() == USERNAME.lower()
    ]


def select_repos():
    featured = read_featured()
    seen = {f.lower() for f in featured}
    combined = list(featured)
    for full in fetch_own_starred():
        if full.lower() not in seen:
            combined.append(full)
            seen.add(full.lower())
    return combined[:MAX]


def shield_escape(text):
    # shields.io badge text: '-' -> '--', '_' -> '__', ' ' -> '_'.
    return text.replace("-", "--").replace("_", "__").replace(" ", "_")


def build_block(repos):
    if not repos:
        return '<p align="center"><em>No projects to show yet.</em></p>'
    lines = ['<p align="center">']
    for full in repos:
        owner, name = full.split("/", 1)
        label = shield_escape(name)
        lines.append(f'  <a href="https://github.com/{full}">')
        lines.append(
            f'    <img src="https://img.shields.io/badge/{label}-238636'
            f'?style=for-the-badge&logo=github&logoColor=white" alt="{name}" />'
        )
        lines.append("  </a>")
    lines.append("</p>")
    return "\n".join(lines)


def main():
    block = build_block(select_repos())
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
