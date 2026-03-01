#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pdf")
    p.add_argument("--out", default=None)
    p.add_argument("--dpi", type=int, default=180)
    args = p.parse_args()

    pdf = Path(args.pdf).expanduser().resolve()
    if not pdf.exists():
        raise SystemExit(f"PDF not found: {pdf}")

    out_dir = Path(args.out).expanduser().resolve() if args.out else pdf.parent / "assets" / pdf.stem / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix = out_dir / "page"
    cmd = [
        "pdftoppm",
        "-png",
        "-r",
        str(args.dpi),
        str(pdf),
        str(prefix),
    ]
    subprocess.run(cmd, check=True)
    print(f"渲染完成: {out_dir}")


if __name__ == "__main__":
    main()
