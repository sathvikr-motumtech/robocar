#!/usr/bin/env python3
"""One-time import of the WordPress export into Hugo page bundles.

Usage:
    python3 scripts/wp_import.py private/<export>.xml <downloaded-images-dir>

Converts published posts/pages from Gutenberg HTML to Markdown, rewrites image
URLs to local files (copied from <downloaded-images-dir>, see --list-images),
and rewrites links to motumtech.in into site-relative links.

    python3 scripts/wp_import.py private/<export>.xml --list-images
prints the image URLs (one per line) so they can be downloaded first.

Handles only the block types the site actually uses: paragraph, heading, list,
image, table, code. Anything unexpected is reported so it can be fixed by hand.
"""
import html
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}
SITE_HOSTS = {"motumtech.in", "www.motumtech.in"}
ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

# Editorial choices for this site's existing content.
SERIES = {"robocar": "Robocar"}
CATEGORY_FIXES = {"Uncategorized": "Robotics"}
EXTRA_TAGS = {"part-4-upgrading-to-raspberry-pi": ["robocar", "robotics", "raspberry-pi"]}
PAGE_RENAMES = {"privacy-policy-2": "privacy-policy"}  # old slug kept as an alias


def full_size(url: str) -> str:
    """WordPress serves resized copies like foo-1024x597.jpg; prefer the original."""
    return re.sub(r"-\d+x\d+(\.\w+)$", r"\1", url)


def local_name(url: str) -> str:
    return Path(urlparse(url).path).name


def site_link(url: str) -> str:
    u = urlparse(url)
    if u.netloc in SITE_HOSTS and "/wp-content/" not in u.path:
        return u.path or "/"
    return url


def md_escape(text: str) -> str:
    return re.sub(r"([\\`*_~$])", r"\\\1", text)


def guess_lang(code: str) -> str:
    if re.search(r"^\s*(import |from \w+ import |def |class )", code, re.M):
        return "python"
    if re.search(r"^\s*(void |#include|int \w+\s*=)", code, re.M):
        return "cpp"
    if code.lstrip().startswith(("$ ", "> ", "sudo ", "ssh ")):
        return "console"
    return "text"


class Converter(HTMLParser):
    INLINE = {"strong": "**", "b": "**", "em": "*", "i": "*"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.buf: list[str] = []
        self.stack: list[tuple[str, dict, int]] = []
        self.lists: list[list] = []  # [kind, counter]
        self.in_pre = False
        self.pre_text: list[str] = []
        self.table: list[list[str]] | None = None
        self.images: list[str] = []
        self.unknown: set[str] = set()

    # -- helpers -----------------------------------------------------------
    def flush(self, prefix: str = "") -> None:
        text = re.sub(r"[ \t\r\n]+", " ", "".join(self.buf)).strip()
        self.buf.clear()
        if text:
            self.blocks.append(prefix + text)

    # -- parser callbacks --------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.in_pre:
            return
        if tag == "pre":
            self.flush()
            self.in_pre, self.pre_text = True, []
        elif tag in ("ul", "ol"):
            self.flush()
            self.lists.append([tag, 0])
        elif tag == "li":
            self.flush()
            self.lists[-1][1] += 1
        elif tag == "table":
            self.flush()
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.table.append([])
        elif tag in ("td", "th"):
            self.buf.clear()
        elif tag == "img":
            src = full_size(a.get("src", ""))
            self.images.append(src)
            alt = (a.get("alt") or "").strip()
            alt = "" if alt.upper() == "IMAGE" else alt
            self.flush()
            self.blocks.append(f"![{alt}]({local_name(src)})")
        elif tag == "br":
            self.buf.append("  \n")
        elif tag in self.INLINE or tag in ("a", "code"):
            self.stack.append((tag, a, len(self.buf)))
        elif tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6", "figure", "tbody", "thead", "figcaption"):
            self.flush()
        else:
            self.unknown.add(tag)

    def handle_endtag(self, tag):
        if self.in_pre:
            if tag == "pre":
                self.in_pre = False
                code = "".join(self.pre_text).strip("\n")
                self.blocks.append(f"```{guess_lang(code)}\n{code}\n```")
            return
        if self.stack and self.stack[-1][0] == tag:
            _, a, start = self.stack.pop()
            inner = "".join(self.buf[start:])
            del self.buf[start:]
            if tag == "a":
                href = site_link(a.get("href", ""))
                self.buf.append(f"[{inner.strip()}]({href})" if inner.strip() else "")
            elif tag == "code":
                self.buf.append(f"`{html.unescape(inner)}`")
            elif not inner.strip():
                self.buf.append(inner)  # e.g. <strong> </strong>
            else:
                mark = self.INLINE[tag]
                lead = inner[: len(inner) - len(inner.lstrip())]
                trail = inner[len(inner.rstrip()):]
                self.buf.append(f"{lead}{mark}{inner.strip()}{mark}{trail}")
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush("#" * int(tag[1]) + " ")
        elif tag == "li":
            kind, n = self.lists[-1]
            indent = "  " * (len(self.lists) - 1)
            self.flush(indent + ("- " if kind == "ul" else f"{n}. "))
        elif tag in ("ul", "ol"):
            self.flush()
            self.lists.pop()
            self._join_list_items()
        elif tag in ("td", "th") and self.table is not None:
            cell = re.sub(r"\s+", " ", "".join(self.buf)).strip().replace("|", "\\|")
            self.buf.clear()
            self.table[-1].append(cell)
        elif tag == "table":
            self.blocks.append(self._table_md(self.table or []))
            self.table = None
        elif tag in ("p", "figcaption"):
            self.flush()

    def handle_data(self, data):
        if self.in_pre:
            self.pre_text.append(data)
        elif self.stack and self.stack[-1][0] == "code":
            self.buf.append(data)
        else:
            self.buf.append(md_escape(data))

    # -- formatting --------------------------------------------------------
    def _join_list_items(self):
        """List items were added as separate blocks; merge the trailing run into one block."""
        if self.lists:
            return  # nested list: merge when the outermost list closes
        items = []
        while self.blocks and re.match(r"^\s*(- |\d+\. )", self.blocks[-1]):
            items.insert(0, self.blocks.pop())
        self.blocks.append("\n".join(items))

    @staticmethod
    def _table_md(rows):
        if not rows:
            return ""
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        header = [re.sub(r"^\*\*(.*)\*\*$", r"\1", c) for c in rows[0]]
        lines = ["| " + " | ".join(header) + " |", "|" + "---|" * width]
        lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return "\n".join(lines)


def yaml_str(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def yaml_list(items) -> str:
    return "[" + ", ".join(yaml_str(i) for i in items) + "]"


def main():
    xml_path = Path(sys.argv[1])
    channel = ET.parse(xml_path).getroot().find("channel")
    items = [
        it for it in channel.findall("item")
        if it.findtext("wp:post_type", namespaces=NS) in ("post", "page")
        and it.findtext("wp:status", namespaces=NS) == "publish"
    ]

    if sys.argv[2] == "--list-images":
        urls = set()
        for it in items:
            conv = Converter()
            conv.feed(it.findtext("content:encoded", namespaces=NS) or "")
            urls.update(conv.images)
        print("\n".join(sorted(urls)))
        return

    images_dir = Path(sys.argv[2])
    for it in items:
        kind = it.findtext("wp:post_type", namespaces=NS)
        slug = it.findtext("wp:post_name", namespaces=NS)
        title = html.unescape(it.findtext("title") or slug)
        date = it.findtext("wp:post_date", namespaces=NS).replace(" ", "T")
        body_html = it.findtext("content:encoded", namespaces=NS) or ""

        conv = Converter()
        conv.feed(body_html)
        conv.close()
        conv.flush()
        body = "\n\n".join(b for b in conv.blocks if b)

        tags = [c.get("nicename") for c in it.findall("category") if c.get("domain") == "post_tag"]
        tags = sorted(set(tags + EXTRA_TAGS.get(slug, [])))
        cats = [CATEGORY_FIXES.get(c.text, c.text) for c in it.findall("category") if c.get("domain") == "category"]
        series = sorted({SERIES[t] for t in tags if t in SERIES})

        fm = [f"title: {yaml_str(title)}", f"date: {date}"]
        if kind == "post":
            out_dir = CONTENT / "posts" / slug
            fm.append(f"slug: {slug}")
            fm += [f"tags: {yaml_list(tags)}", f"categories: {yaml_list(cats)}"]
            if series:
                fm.append(f"series: {yaml_list(series)}")
        else:
            new_slug = PAGE_RENAMES.get(slug, slug)
            out_dir = CONTENT / new_slug
            if new_slug != slug:
                fm.append(f"aliases: [/{slug}/]")
            fm.append("showToc: false")

        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.md").write_text("---\n" + "\n".join(fm) + "\n---\n\n" + body + "\n")
        for url in conv.images:
            src = images_dir / local_name(url)
            if src.exists():
                shutil.copy2(src, out_dir / src.name)
            else:
                print(f"  MISSING image for {slug}: {url}")
        note = f"  (unhandled tags: {sorted(conv.unknown)})" if conv.unknown else ""
        print(f"{kind:4} {out_dir.relative_to(ROOT)}  images={len(conv.images)}{note}")


if __name__ == "__main__":
    main()
