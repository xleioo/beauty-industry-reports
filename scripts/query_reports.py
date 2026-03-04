#!/usr/bin/env python3
import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

TEXT_INDEX_PATH = Path("/Users/len/Git/美妆行业报告/index/chunks.jsonl")
CHART_INDEX_PATH = Path("/Users/len/Git/美妆行业报告/index/chart_cards.jsonl")


def tokenize(text: str):
    text = text.lower()
    zh = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    en = re.findall(r"[a-z0-9\-\.\+%]+", text)
    return zh + en


def load_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def row_to_text(row: dict, mode: str) -> str:
    if mode == "text":
        return row.get("text", "")
    # chart
    parts = [row.get("chart_title", ""), row.get("key_takeaway", "")]
    for m in row.get("metrics", [])[:12]:
        parts.append(
            " ".join(
                [
                    str(m.get("name", "")),
                    str(m.get("value", "")),
                    str(m.get("unit", "")),
                    str(m.get("time_scope", "")),
                ]
            )
        )
    return " ".join(parts)


def build_bm25(rows, mode: str):
    docs = [tokenize(row_to_text(r, mode)) for r in rows]
    N = len(docs)
    if N == 0:
        return docs, [], {}, 0.0
    df = Counter()
    lens = []
    for d in docs:
        lens.append(len(d))
        for t in set(d):
            df[t] += 1
    avgdl = sum(lens) / max(1, len(lens))
    idf = {t: math.log(1 + (N - n + 0.5) / (n + 0.5)) for t, n in df.items()}
    tf = [Counter(d) for d in docs]
    return docs, tf, idf, avgdl


def bm25_score(query_tokens, tf_doc, doc_len, idf, avgdl, k1=1.5, b=0.75):
    score = 0.0
    for t in query_tokens:
        if t not in tf_doc:
            continue
        tf = tf_doc[t]
        denom = tf + k1 * (1 - b + b * doc_len / max(1e-9, avgdl))
        score += idf.get(t, 0) * (tf * (k1 + 1) / max(1e-9, denom))
    return score


def search_rows(rows, mode: str, query: str, topk: int):
    docs, tf_all, idf, avgdl = build_bm25(rows, mode)
    q_tokens = tokenize(query)
    hits = []
    for i, row in enumerate(rows):
        s = bm25_score(q_tokens, tf_all[i], len(docs[i]), idf, avgdl)
        if s > 0:
            hits.append((s, row))
    hits.sort(key=lambda x: x[0], reverse=True)
    return hits[:topk]


def _normalize_tags(tags):
    if tags is None:
        return []
    if isinstance(tags, str):
        return [tags]
    if isinstance(tags, list):
        return [t for t in tags if isinstance(t, str)]
    return []


def filter_rows_by_tags(rows, tags):
    if not tags:
        return rows
    wanted = {t.lower() for t in tags}
    out = []
    for row in rows:
        row_tags = {t.lower() for t in _normalize_tags(row.get("tags"))}
        if row_tags & wanted:
            out.append(row)
    return out


def print_text_hits(query: str, hits):
    by_report = defaultdict(list)
    for s, row in hits:
        by_report[row.get("report_title", "未知报告")].append((s, row))

    print(f"问题: {query}\n")
    print("## 文本证据")
    for title, items in by_report.items():
        best = items[0][1]
        print(f"### {title}")
        print(f"来源: {best.get('source_pdf','-')}")
        for _, it in items[:3]:
            snippet = it.get("text", "").replace("\n", " ")
            if len(snippet) > 220:
                snippet = snippet[:220] + "..."
            print(f"- [chunk {it.get('chunk_no','?')}] {snippet}")
        print()


def print_chart_hits(hits):
    print("## 图表证据")
    if not hits:
        print("- 暂无图表命中（可先完成图表增强落库）。\n")
        return

    for s, row in hits:
        print(f"### {row.get('chart_title','(未命名图表)')} · {row.get('page','?')}")
        print(f"来源: {row.get('source_pdf','-')}")
        for m in row.get("metrics", [])[:3]:
            print(
                f"- {m.get('name','指标')}: {m.get('value','')} {m.get('unit','')} "
                f"({m.get('time_scope','')})"
            )
        print(f"- 解读: {row.get('key_takeaway','')}")
        print(f"- 置信度: {row.get('confidence','中')}\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("query", help="查询问题")
    p.add_argument("--topk", type=int, default=8, help="文本检索返回条数")
    p.add_argument("--chart-topk", type=int, default=5, help="图表检索返回条数")
    p.add_argument("--tag", action="append", default=[], help="按标签过滤，可重复：--tag lulu --tag x")
    args = p.parse_args()

    text_rows = load_jsonl(TEXT_INDEX_PATH)
    chart_rows = load_jsonl(CHART_INDEX_PATH)

    if args.tag:
        text_rows = filter_rows_by_tags(text_rows, args.tag)
        chart_rows = filter_rows_by_tags(chart_rows, args.tag)

    if not text_rows and not chart_rows:
        print("索引为空，请先运行入库流程。")
        return

    text_hits = search_rows(text_rows, "text", args.query, args.topk) if text_rows else []
    chart_hits = search_rows(chart_rows, "chart", args.query, args.chart_topk) if chart_rows else []

    if not text_hits and not chart_hits:
        print("没有命中相关内容。")
        return

    if text_hits:
        print_text_hits(args.query, text_hits)
    else:
        print(f"问题: {args.query}\n\n## 文本证据\n- 暂无文本命中。\n")

    print_chart_hits(chart_hits)


if __name__ == "__main__":
    main()
