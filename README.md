# 美妆行业报告知识库（OpenClaw 本地版）

这个目录用于把你持续提供的 PDF 报告转成：
1. 可读的 Markdown 知识文档
2. 可检索的本地分块索引（jsonl）

## 目录结构

- `raw/`：新报告投递目录（推荐把新 PDF 放这里）
- `knowledge/`：自动生成的 Markdown
- `index/chunks.jsonl`：文本检索索引（按 chunk 存）
- `index/chart_cards.jsonl`：图表数值卡片索引（多模态抽取）
- `scripts/ingest_reports.py`：入库脚本
- `scripts/query_reports.py`：检索脚本
- `scripts/render_pdf_pages.py`：PDF 转页面图片（图表增强）
- `scripts/select_chart_pages.py`：自动挑选可能含图表的数据页

## 一次性初始化

```bash
cd ~/Git/美妆行业报告
python3 scripts/ingest_reports.py
```

## 日常用法

### 1) 新增报告
把 PDF 放到 `~/Git/美妆行业报告/raw/`。

### 2) 更新知识库
```bash
cd ~/Git/美妆行业报告
python3 scripts/ingest_reports.py
```

### 3) 本地检索
```bash
cd ~/Git/美妆行业报告
python3 scripts/query_reports.py "2025年护肤赛道增速和价格带变化"
```

## 备注

- 当前检索为本地 BM25（无需额外依赖），稳定可用。
- 后续可升级到向量数据库（LanceDB/FAISS）做语义检索增强。
- OpenClaw 回答时可优先读取 `knowledge/` 与 `index/chunks.jsonl` 里的内容，做到可追溯引用。
