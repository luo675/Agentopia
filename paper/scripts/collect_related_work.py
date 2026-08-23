#!/usr/bin/env python3
"""Validate a curated primary-source literature list and fetch ACL BibTeX.

The script deliberately uses only official publisher, proceedings, arXiv, and
OpenReview URLs. It does not discover papers from search-engine snippets.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ALLOWED_HOST_SUFFIXES = (
    "aclanthology.org",
    "arxiv.org",
    "cambridge.org",
    "doi.org",
    "openreview.net",
    "proceedings.iclr.cc",
    "proceedings.mlr.press",
    "proceedings.mlsys.org",
)
USER_AGENT = "Agentopia-literature-audit/1.0 (research metadata validation)"


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.parts.append(data)

    @property
    def title(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def fetch(url: str, timeout: int) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.geturl(), response.read()


def acl_bib_url(url: str) -> str | None:
    match = re.fullmatch(r"https://aclanthology\.org/([^/]+)/?", url)
    return f"https://aclanthology.org/{match.group(1)}.bib" if match else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    seeds = json.loads(args.seeds.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    bib_entries: list[str] = []

    for item in seeds:
        url = item["official_url"]
        host = (urlparse(url).hostname or "").lower()
        if not any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_HOST_SUFFIXES):
            raise ValueError(f"Non-primary host rejected for {item['key']}: {host}")

        row = {
            "key": item["key"],
            "expected_title": item["title"],
            "year": item["year"],
            "topic": item["topic"],
            "official_url": url,
            "http_status": "",
            "resolved_url": "",
            "page_title": "",
            "result": "error",
            "note": "",
        }
        try:
            status, resolved, body = fetch(url, args.timeout)
            title_parser = TitleParser()
            title_parser.feed(body[:2_000_000].decode("utf-8", errors="replace"))
            challenged = host == "openreview.net" and "/challenge?" in resolved
            row.update(
                http_status=status,
                resolved_url=resolved,
                page_title=title_parser.title,
                result=(
                    "blocked-by-openreview-challenge"
                    if challenged
                    else "ok" if status == 200
                    else "http-error"
                ),
            )
        except urllib.error.HTTPError as exc:
            row.update(http_status=exc.code, resolved_url=exc.geturl(), note=str(exc))
            if host == "openreview.net" and exc.code in {403, 429, 503}:
                row["result"] = "blocked-by-openreview-challenge"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            row["note"] = str(exc)
        rows.append(row)

        bib_url = acl_bib_url(url)
        if bib_url:
            try:
                status, _, body = fetch(bib_url, args.timeout)
                if status == 200:
                    bib_entries.append(body.decode("utf-8").strip())
            except (urllib.error.URLError, TimeoutError, OSError):
                pass

    csv_path = args.output_dir / "url_verification.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    bib_path = args.output_dir / "fetched_acl_refs.bib"
    bib_path.write_text("\n\n".join(bib_entries) + ("\n" if bib_entries else ""), encoding="utf-8")

    ok = sum(row["result"] == "ok" for row in rows)
    blocked = sum(row["result"] == "blocked-by-openreview-challenge" for row in rows)
    print(f"validated={len(rows)} ok={ok} openreview_blocked={blocked} errors={len(rows)-ok-blocked}")
    print(csv_path)
    print(bib_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
