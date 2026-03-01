# 图表增强版（GPT-5.2 多模态）

## 目标
在原有文本检索基础上，新增“图表读数卡片”，尽量保留 PDF 图表中的关键数字。

## 流程
1. 渲染 PDF 每页为图片
2. 自动挑选可能是图表的页面
3. 用 GPT-5.2 多模态分析这些页面，产出结构化“图表数值卡片”
4. 合并到 `knowledge/*.md` 与 `index/chunks.jsonl`

## 命令
```bash
cd ~/Git/美妆行业报告
python3 scripts/render_pdf_pages.py "2025年度UCO美妆行业报告.pdf"
python3 scripts/select_chart_pages.py "2025年度UCO美妆行业报告.pdf" --topk 16
```

随后由 OpenClaw 代理使用 `openai-codex/gpt-5.2` + 图像输入分析 `assets/<报告名>/pages/` 中选定页。

## 输出建议格式
每页至少提取：
- 图表标题
- 指标名
- 数值
- 口径/时间范围
- 趋势解读
- 置信度（高/中/低）
- 原页码
