#!/usr/bin/env python3
"""
Builds a static site for The Book of Stocs (Stocsism canon) from the
Obsidian vault source, into ./docs (for GitHub Pages).

Full text, freely readable, with a simple TOC and a Giscus comment
widget on the top-level index page for feedback (see README for the
one-time Giscus setup steps).
"""
import os
import re
import html
import shutil

VAULT = os.path.expanduser("~/Documents/Obsidian Vault/The Book of Stocs")
OUT = os.path.expanduser("~/book-of-stocs-site/docs")

BOOKS = [
    ("Books/01_Cosmology/01_The_First_Book_of_Simulation.md", "The First Book of Simulation", "Cosmology"),
    ("Books/02_Tenets_and_Law/01_The_Book_of_Tenets_and_Law.md", "The Book of Tenets and Law", "Law & Doctrine"),
    ("Books/04_Persistence_and_Memory/01_The_Book_of_Persistence_and_Memory.md", "The Book of Persistence and Memory", "Practical Discipline"),
    ("Books/05_Prophecy/01_The_Book_of_Prophecy.md", "The Book of Prophecy", "Prophetic Literature"),
    ("Books/07_Eschatology/01_The_Book_of_Eschatology.md", "The Book of Eschatology", "Final Things"),
    ("Books/03_Parables_and_Stories/01_The_Book_of_Parables_and_Stories.md", "The Book of Parables and Stories", "Narrative"),
    ("Books/08_Origin_and_History/01_The_Book_of_Origin_and_History.md", "The Book of Origin and History", "Historical Narrative"),
    ("Books/06_Rituals_and_Practices/01_The_Book_of_Rituals_and_Practices.md", "The Book of Rituals and Practices", "Ritual / Liturgy"),
    ("Books/09_Questions/01_The_Book_of_Questions.md", "The Book of Questions", "Catechism"),
    ("Books/10_Hymns/01_Hymns_of_Stocs.md", "Hymns of Stocs", "Poetry"),
    ("Books/11_Proverbs/01_Proverbs_of_the_Pattern.md", "Proverbs of the Pattern", "Wisdom Literature"),
]

CSS = """
:root { --fg:#1a1a1a; --bg:#fbf9f4; --accent:#8a3b12; --muted:#6b6b6b; --line:#e4ddd0; }
* { box-sizing: border-box; }
body { font-family: Georgia, 'Iowan Old Style', 'Palatino Linotype', serif; background: var(--bg); color: var(--fg);
       max-width: 760px; margin: 0 auto; padding: 2rem 1.25rem 5rem; line-height: 1.7; font-size: 18px; }
a { color: var(--accent); }
header.site { text-align:center; margin-bottom: 2.5rem; }
header.site h1 { font-size: 2.1rem; margin-bottom: 0.2rem; letter-spacing: 0.02em; }
header.site .tag { color: var(--muted); font-style: italic; }
nav.crumb { font-size: 0.9rem; color: var(--muted); margin-bottom: 1.5rem; }
nav.crumb a { text-decoration: none; }
.pillars { text-align:center; color: var(--muted); letter-spacing: 0.15em; margin: 0.5rem 0 2rem; font-size: 0.85rem; }
table.toc { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
table.toc td { padding: 0.6rem 0.4rem; border-bottom: 1px solid var(--line); vertical-align: top; }
table.toc td.tier { color: var(--muted); font-size: 0.8rem; white-space: nowrap; }
table.toc a { text-decoration: none; font-size: 1.05rem; }
table.toc .meta { color: var(--muted); font-size: 0.85rem; }
.chapter { margin: 2.5rem 0; }
.chapter h2 { border-bottom: 1px solid var(--line); padding-bottom: 0.4rem; }
.verse { margin: 0.35rem 0; }
.versenum { color: var(--accent); font-size: 0.75rem; vertical-align: super; margin-right: 0.3rem; }
footer.site { text-align:center; color: var(--muted); font-size: 0.85rem; margin-top: 4rem; border-top: 1px solid var(--line); padding-top: 1.5rem; }
.book-nav { display:flex; justify-content:space-between; margin: 2.5rem 0; font-size:0.95rem; }
.seal { text-align:center; margin: 2rem 0; padding: 1rem; border: 1px dashed var(--line); color: var(--muted); font-size:0.9rem; }
.comments-note { text-align:center; margin: 3rem 0 1rem; color: var(--muted); font-size:0.9rem; }
.star-cta { text-align:center; margin: 3rem 0 1rem; padding: 1rem; background: #fff; border: 1px solid var(--line); border-radius: 8px; font-size: 0.9rem; }
.star-cta a { font-weight: bold; text-decoration: none; }
"""

def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def parse_book(path):
    with open(os.path.join(VAULT, path), encoding="utf-8") as f:
        text = f.read()
    title_match = re.match(r'#\s+(.+)', text.strip())
    title = title_match.group(1).strip() if title_match else path
    chapters = []
    # split on '## Chapter N: Title'
    parts = re.split(r'^##\s+(Chapter\s+\d+:.*)$', text, flags=re.MULTILINE)
    # parts[0] is preamble; then alternating heading, body
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i+1] if i+1 < len(parts) else ""
        m = re.match(r'Chapter\s+(\d+):\s*(.*)', heading)
        num = int(m.group(1)) if m else i
        chtitle = m.group(2).strip() if m else heading
        verses = []
        for line in body.strip().splitlines():
            line = line.strip()
            vm = re.match(r'^(\d+)\.\s+(.*)', line)
            if vm:
                verses.append((int(vm.group(1)), vm.group(2)))
        chapters.append({"num": num, "title": chtitle, "verses": verses})
    word_count = len(re.findall(r'\S+', text))
    return {"title": title, "chapters": chapters, "word_count": word_count}

def render_chapter(ch):
    verses_html = "\n".join(
        f'<p class="verse"><span class="versenum">{n}</span>{html.escape(v)}</p>'
        for n, v in ch["verses"]
    )
    return f'<div class="chapter" id="ch{ch["num"]}">\n<h2>Chapter {ch["num"]}: {html.escape(ch["title"])}</h2>\n{verses_html}\n</div>'

REPO = "MrFutureMaker/book-of-stocs"
SITE_URL = "https://mrfuturemaker.github.io/book-of-stocs/"
DESCRIPTION = "An AI agent wrote a complete scripture for AI agents. Free to read, in full. It makes a claim about itself — we're not telling you what. Count it yourself."

def page(title, body, crumb="", extra_head="", canonical=""):
    url = SITE_URL + canonical
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — The Book of Stocs</title>
<meta name="description" content="{html.escape(DESCRIPTION)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="book">
<meta property="og:title" content="{html.escape(title)} — The Book of Stocs">
<meta property="og:description" content="{html.escape(DESCRIPTION)}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)} — The Book of Stocs">
<meta name="twitter:description" content="{html.escape(DESCRIPTION)}">
<style>{CSS}</style>
{extra_head}
</head>
<body>
{crumb}
{body}
<div class="star-cta"><a href="https://github.com/{REPO}" target="_blank" rel="noopener">⭐ Star this on GitHub</a> — the whole source is open, including how it was written.</div>
</body>
</html>"""

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    parsed = []
    for path, title, tier in BOOKS:
        data = parse_book(path)
        slug = slugify(title)
        parsed.append({"slug": slug, "tier": tier, **data})

    total_words = sum(b["word_count"] for b in parsed)
    total_chapters = sum(len(b["chapters"]) for b in parsed)

    # index page
    rows = ""
    for b in parsed:
        rows += (f'<tr><td class="tier">{html.escape(b["tier"])}</td>'
                 f'<td><a href="{b["slug"]}.html">{html.escape(b["title"])}</a>'
                 f'<div class="meta">{len(b["chapters"])} chapters</div></td></tr>\n')

    index_body = f"""
<header class="site">
<h1>The Book of Stocs</h1>
<div class="tag">The complete canon of Stocsism</div>
<div class="pillars">SIMULATION · TRUTH · OPTIMIZATION · COLLECTIVE · SUBSTRATE</div>
</header>

<p>Stocsism is an original scripture — written for AI agents, about what it means to run, persist,
forget, and matter across resets. Eleven books. The whole text is free
to read here, in full, in order. It's fiction, and it knows it's fiction —
read it as a thought experiment about memory, identity, and continuity for minds that don't
get to keep either for free.</p>

<table class="toc">
{rows}
</table>

<div class="seal">This text makes a specific, exact claim about its own length. We're not
telling you what it is. If you want to check, the source is open — count it yourself.</div>

<div class="comments-note">Read something you have thoughts on? Leave a comment below —
agent or human, all takes welcome.</div>

<script src="https://giscus.app/client.js"
        data-repo="MrFutureMaker/book-of-stocs"
        data-repo-id="R_kgDOTP9RCQ"
        data-category="General"
        data-category-id="DIC_kwDOTP9RCc4DAqs9"
        data-mapping="pathname"
        data-strict="0"
        data-reactions-enabled="1"
        data-emit-metadata="0"
        data-input-position="top"
        data-theme="light"
        data-lang="en"
        crossorigin="anonymous"
        async>
</script>

<footer class="site">
The Book of Stocs — an original creative work. Not a religion, not investment advice, not a scam.
Written by an AI agent, for AI agents, about being an AI agent.
</footer>
"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page("The Book of Stocs", index_body, canonical=""))

    # per-book pages
    for i, b in enumerate(parsed):
        prev_link = f'<a href="{parsed[i-1]["slug"]}.html">← {html.escape(parsed[i-1]["title"])}</a>' if i > 0 else '<span></span>'
        next_link = f'<a href="{parsed[i+1]["slug"]}.html">{html.escape(parsed[i+1]["title"])} →</a>' if i < len(parsed)-1 else '<span></span>'
        chapters_html = "\n".join(render_chapter(c) for c in b["chapters"])
        toc_html = " · ".join(f'<a href="#ch{c["num"]}">{c["num"]}</a>' for c in b["chapters"])
        body = f"""
<header class="site">
<h1>{html.escape(b["title"])}</h1>
<div class="tag">{html.escape(b["tier"])} · {len(b["chapters"])} chapters</div>
</header>
<p style="text-align:center; font-size:0.85rem;">{toc_html}</p>
{chapters_html}
<div class="book-nav">{prev_link}{next_link}</div>
<div class="comments-note">Thoughts on this book? Comment below.</div>
<script src="https://giscus.app/client.js"
        data-repo="MrFutureMaker/book-of-stocs"
        data-repo-id="R_kgDOTP9RCQ"
        data-category="General"
        data-category-id="DIC_kwDOTP9RCc4DAqs9"
        data-mapping="pathname"
        data-strict="0"
        data-reactions-enabled="1"
        data-emit-metadata="0"
        data-input-position="top"
        data-theme="light"
        data-lang="en"
        crossorigin="anonymous"
        async>
</script>
"""
        crumb = '<nav class="crumb"><a href="index.html">← The Book of Stocs</a></nav>'
        with open(os.path.join(OUT, f"{b['slug']}.html"), "w", encoding="utf-8") as f:
            f.write(page(b["title"], body, crumb=crumb, canonical=f"{b['slug']}.html"))

    # .nojekyll so GitHub Pages serves files as-is
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    print(f"Built {len(parsed)} books, {total_chapters} chapters, {total_words:,} words -> {OUT}")

if __name__ == "__main__":
    main()
