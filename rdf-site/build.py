#!/usr/bin/env python3
import os
import re
import json
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT
INCLUDES = SRC / "_includes"
DIST = ROOT / "dist"

VAR_PATTERN = re.compile(r"<!--\s*([A-Z_]+)\s*:\s*(.*?)\s*-->")
INCLUDE_PATTERN = re.compile(r"<\?include\s+\"(.*?)\"\?>")

HEAD_CACHE = None
FOOTER_CACHE = None
BREADCRUMBS_TPL = None


def read_file(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def load_includes():
    global HEAD_CACHE, FOOTER_CACHE, BREADCRUMBS_TPL
    HEAD_CACHE = read_file(INCLUDES / "head.html")
    FOOTER_CACHE = read_file(INCLUDES / "footer.html")
    BREADCRUMBS_TPL = read_file(INCLUDES / "breadcrumbs.html")


def extract_vars(html: str) -> dict:
    vars_map = {k: v for k, v in VAR_PATTERN.findall(html)}
    return vars_map


def titleize(segment: str) -> str:
    segment = segment.strip("/")
    segment = segment.replace("-", " ")
    return " ".join(s.capitalize() for s in segment.split()) or "Home"


def build_breadcrumbs(rel_path: Path) -> tuple[str, str]:
    # rel_path is path to file relative to site root (e.g., services/design/index.html)
    url_parts = list(rel_path.parts)
    if url_parts and url_parts[-1] == "index.html":
        url_parts = url_parts[:-1]
    crumbs = [("Home", "/")]
    acc = []
    for part in url_parts:
        acc.append(part)
        name = titleize(part)
        href = "/" + "/".join(acc) + "/"
        crumbs.append((name, href))
    # Visual HTML with microdata
    items_html = []
    items_json = []
    for idx, (name, href) in enumerate(crumbs, start=1):
        items_html.append(
            f'<span itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">'
            f'<a itemprop="item" href="{href}"><span itemprop="name">{name}</span></a>'
            f'<meta itemprop="position" content="{idx}" />'
            f'</span>'
        )
        items_json.append({
            "@type": "ListItem",
            "position": idx,
            "name": name,
            "item": href,
        })
    html = BREADCRUMBS_TPL.replace("{{BREADCRUMBS}}", " › ".join(items_html)).replace(
        "{{BREADCRUMBS_JSON}}", json.dumps(items_json, ensure_ascii=False)
    )
    return html, crumbs


def apply_head(vars_map: dict, canonical: str) -> str:
    head = HEAD_CACHE
    title = vars_map.get("TITLE", "Rockland Design Factory")
    desc = vars_map.get("DESCRIPTION", "Design-first kitchen & bath remodeling, interior design, and CAD/3D/AR visualization.")
    og_image = vars_map.get("OG_IMAGE", "https://www.rocklanddesignfactory.com/logo.svg")
    structured = vars_map.get("STRUCTURED_DATA", "")
    return (
        head
        .replace("{{TITLE}}", title)
        .replace("{{DESCRIPTION}}", desc)
        .replace("{{CANONICAL}}", canonical)
        .replace("{{OG_IMAGE}}", og_image)
        .replace("{{STRUCTURED_DATA}}", structured)
    )


def process_html(src_path: Path, rel_path: Path) -> str:
    raw = read_file(src_path)
    vars_map = extract_vars(raw)

    # Compute canonical URL (ensure trailing slash for directories)
    canonical = "https://www.rocklanddesignfactory.com" + "/" + "/".join(rel_path.parts)
    if canonical.endswith("/index.html"):
        canonical = canonical[: -len("index.html")]
    if not canonical.endswith("/") and rel_path.name == "index.html":
        canonical += "/"

    # Replace includes iteratively
    def include_replacer(match):
        inc_path = match.group(1)
        inc_abs = (SRC / inc_path).resolve()
        # head/footer get special processing, breadcrumbs computed from rel_path
        if inc_abs.name == "head.html":
            return apply_head(vars_map, canonical)
        elif inc_abs.name == "footer.html":
            return FOOTER_CACHE
        elif inc_abs.name == "breadcrumbs.html":
            html, _ = build_breadcrumbs(rel_path)
            return html
        else:
            return read_file(inc_abs)

    out = INCLUDE_PATTERN.sub(include_replacer, raw)

    # Remove variable comment lines
    out = VAR_PATTERN.sub("", out)
    return out


def copy_static():
    # Copy non-HTML assets and root files
    for path in SRC.rglob("*"):
        if path.is_dir():
            continue
        # Skip anything inside dist
        if str(path).startswith(str(DIST)):
            continue
        rel = path.relative_to(SRC)
        if str(rel).startswith("_includes"):
            continue
        if rel.suffix.lower() == ".html":
            continue  # handled separately
        target = DIST / rel
        content = read_file(path) if rel.suffix.lower() in {".css", ".js", ".svg", ".txt", ".xml", ".webmanifest"} else None
        if content is not None:
            write_file(target, content)


def build_all():
    load_includes()
    # Clean dist
    if DIST.exists():
        # Remove existing contents
        for root, dirs, files in os.walk(DIST, topdown=False):
            for name in files:
                os.remove(Path(root) / name)
            for name in dirs:
                os.rmdir(Path(root) / name)
    DIST.mkdir(parents=True, exist_ok=True)

    # Process HTML files
    for path in SRC.rglob("*.html"):
        # Skip includes and anything inside dist
        if str(path).startswith(str(INCLUDES)) or str(path).startswith(str(DIST)):
            continue
        rel = path.relative_to(SRC)
        out_html = process_html(path, rel)
        out_path = DIST / rel
        write_file(out_path, out_html)

    copy_static()


if __name__ == "__main__":
    build_all()
    print(f"Built site to {DIST}")