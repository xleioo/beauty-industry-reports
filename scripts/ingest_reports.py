#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path("/Users/len/Git/美妆行业报告")
RAW_DIRS = [ROOT / "raw", ROOT]
KNOWLEDGE_DIR = ROOT / "knowledge"
INDEX_PATH = ROOT / "index" / "chunks.jsonl"


def run_pdftotext(pdf_path: Path) -> str:
    cmd = ["pdftotext", "-enc", "UTF-8", str(pdf_path), "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed: {result.stderr.strip()}")
    return result.stdout


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 120):
    text = normalize_whitespace(text)
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        piece = text[start:end]
        if end < n:
            br = piece.rfind("\n\n")
            if br > chunk_size * 0.5:
                end = start + br
                piece = text[start:end]
        piece = piece.strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def quick_summary(text: str):
    paras = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
    bullets = []
    for p in paras[:8]:
        s = p.split("。", 1)[0].strip()
        if len(s) > 12:
            bullets.append(s + ("。" if not s.endswith("。") else ""))
        if len(bullets) >= 5:
            break
    return bullets


def extract_date_from_name(name: str) -> str:
    m = re.search(r"(20\d{2})[-_年]?(\d{1,2})?", name)
    if not m:
        return dt.date.today().isoformat()
    year = m.group(1)
    month = m.group(2)
    if month:
        return f"{year}-{int(month):02d}-01"
    return f"{year}-01-01"


def collect_pdfs():
    seen = set()
    out = []
    for d in RAW_DIRS:
        for p in d.glob("*.pdf"):
            rp = p.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            out.append(rp)
    return sorted(out)


def load_existing_ids(index_path: Path):
    ids = set()
    if not index_path.exists():
        return ids
    with index_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                ids.add(obj.get("chunk_id"))
            except Exception:
                pass
    return ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="重建索引")
    args = parser.parse_args()

    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

    if args.rebuild and INDEX_PATH.exists():
        INDEX_PATH.unlink()

    existing = load_existing_ids(INDEX_PATH)
    processed_files = 0
    new_chunks = 0

    for pdf in collect_pdfs():
        text = run_pdftotext(pdf)
        text = normalize_whitespace(text)
        if len(text) < 20:
            continue

        report_id = hashlib.sha1(str(pdf).encode()).hexdigest()[:12]
        date_hint = extract_date_from_name(pdf.stem)
        chunks = chunk_text(text)
        summary = quick_summary(text)

        md_path = KNOWLEDGE_DIR / f"{pdf.stem}.md"
        with md_path.open("w", encoding="utf-8") as f:
            f.write(f"# {pdf.stem}\n\n")
            f.write("## 基本信息\n")
            f.write(f"- 来源文件: `{pdf}`\n")
            f.write(f"- 报告日期(推断): {date_hint}\n")
            f.write(f"- 入库时间: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- 字符数: {len(text)}\n")
            f.write(f"- 分块数: {len(chunks)}\n\n")
            f.write("## 快速要点\n")
            for b in summary:
                f.write(f"- {b}\n")
            f.write("\n## 全文摘录\n\n")
            f.write(text)
            f.write("\n")

        with INDEX_PATH.open("a", encoding="utf-8") as idx:
            for i, c in enumerate(chunks):
                chunk_id = f"{report_id}-{i:04d}"
                if chunk_id in existing:
                    continue
                row = {
                    "chunk_id": chunk_id,
                    "report_id": report_id,
                    "report_title": pdf.stem,
                    "source_pdf": str(pdf),
                    "source_md": str(md_path),
                    "date_hint": date_hint,
                    "chunk_no": i,
                    "text": c,
                }
                idx.write(json.dumps(row, ensure_ascii=False) + "\n")
                new_chunks += 1

        processed_files += 1

    print(f"处理报告: {processed_files} 份")
    print(f"新增分块: {new_chunks} 条")
    print(f"知识库目录: {KNOWLEDGE_DIR}")
    print(f"索引文件: {INDEX_PATH}")


if __name__ == "__main__":
    main()
