#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path

KEYWORDS = [
    "同比", "环比", "增速", "份额", "占比", "GMV", "销售额", "抖音", "天猫", "京东", "亿元", "%", "直播", "达播", "自播"
]


def extract_pages_text(pdf: Path):
    cmd = ["pdftotext", "-enc", "UTF-8", str(pdf), "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    # pdftotext page break is form feed
    return r.stdout.split("\f")


def score_page(text: str) -> int:
    s = 0
    for k in KEYWORDS:
        if k in text:
            s += 2
    nums = len(re.findall(r"\d+\.?\d*%|\d+\.?\d*亿|\d+\.?\d*w\+|\d+\.?\d*万\+", text))
    s += min(nums, 10)
    return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pdf")
    p.add_argument("--topk", type=int, default=16)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    pdf = Path(args.pdf).expanduser().resolve()
    pages = extract_pages_text(pdf)
    scored = []
    for i, t in enumerate(pages, start=1):
        s = score_page(t)
        if s > 0:
            scored.append((s, i))
    scored.sort(reverse=True)
    picked = [i for _, i in scored[: args.topk]]

    out = Path(args.out).expanduser().resolve() if args.out else pdf.parent / "assets" / pdf.stem / "chart_pages.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"pdf": str(pdf), "pages": picked}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已选图表页 {len(picked)} 页 -> {out}")
    print("pages:", ",".join(map(str, picked)))


if __name__ == "__main__":
    main()
