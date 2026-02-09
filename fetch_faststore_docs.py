#!/usr/bin/env python3
"""
Fetch (crawl) all FastStore docs URLs listed in README.md and save them locally.

Usage (from repo root):
  python fetch_faststore_docs.py

Outputs:
  - Creates a 'docs-cache' folder with one HTML file per URL.
"""

from __future__ import annotations

import os
import re
import sys
import urllib.parse
from pathlib import Path

try:
  import requests  # type: ignore
except ImportError:
  print("This script requires the 'requests' package. Install it with:")
  print("  pip install requests")
  sys.exit(1)


ROOT = Path(__file__).resolve().parent
README_PATH = ROOT / "README.md"
OUT_DIR = ROOT / "docs-cache"


def extract_urls(text: str) -> list[str]:
  # Simple regex to capture http/https URLs up to whitespace or closing paren
  pattern = r"https?://[^\s)]+"
  urls = re.findall(pattern, text)
  # Remove trailing punctuation that sometimes sticks to URLs
  cleaned: list[str] = []
  for u in urls:
    cleaned.append(u.rstrip(".,);"))
  # Keep order but remove duplicates
  seen: set[str] = set()
  ordered: list[str] = []
  for u in cleaned:
    if u not in seen:
      seen.add(u)
      ordered.append(u)
  return ordered


def slugify_url(url: str, index: int) -> str:
  parsed = urllib.parse.urlparse(url)
  base = (parsed.netloc + parsed.path).strip("/")
  if not base:
    base = f"doc_{index:03d}"
  # Replace anything that isn't alphanumeric, dash, or underscore
  safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
  return f"{index:03d}_{safe or f'doc_{index:03d}'}"


def main() -> None:
  if not README_PATH.exists():
    print(f"README not found at {README_PATH}")
    sys.exit(1)

  text = README_PATH.read_text(encoding="utf-8")
  urls = extract_urls(text)

  if not urls:
    print("No URLs found in README.md")
    return

  OUT_DIR.mkdir(exist_ok=True)

  print(f"Found {len(urls)} URLs in README.md")
  print(f"Saving HTML files under {OUT_DIR}")
  print()

  session = requests.Session()

  for idx, url in enumerate(urls, start=1):
    filename = slugify_url(url, idx) + ".html"
    out_path = OUT_DIR / filename

    print(f"[{idx:03d}/{len(urls):03d}] Fetching {url}")
    try:
      resp = session.get(url, timeout=30)
      resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
      print(f"  -> ERROR: {e}")
      continue

    out_path.write_text(resp.text, encoding="utf-8")
    print(f"  -> Saved to {out_path}")


if __name__ == "__main__":
  main()

