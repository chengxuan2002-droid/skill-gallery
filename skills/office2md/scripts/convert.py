#!/usr/bin/env python3
"""
office2md - Convert Office documents and various file formats to Markdown.

Wrapper around Microsoft's markitdown library with graceful fallback handling
and cross-agent compatibility (Codex, Claude Code, OpenClaw, etc.).

Features:
  - Faithful conversion via markitdown
  - Semantic post-processing (decimal ratios → percentages, etc.)
  - Conversion report documenting all non-faithful transformations
  - Batch directory conversion
  - OCR and vision support

Supported formats (varies by installed dependencies):
  - Word (.docx, .doc), Excel (.xlsx, .xls, .csv), PowerPoint (.pptx, .ppt)
  - PDF, HTML, images (with OCR), audio/video (with whisper)
  - Jupyter Notebooks, ZIP, JSON, XML, plain text, and more

Usage:
  python3 convert.py <input_file> [output_file]
  python3 convert.py --dir <input_dir> [--output-dir <output_dir>]
  python3 convert.py --formats
  python3 convert.py --check
  python3 convert.py --version
"""

import os
import re
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

__version__ = "1.0.2"


# ── Installation helpers ──────────────────────────────────────────────────

def _pip_install(package_spec: str, quiet: bool = False) -> bool:
    """Install a package via pip. Returns True on success."""
    cmd = [sys.executable, "-m", "pip", "install"]
    if quiet:
        cmd.append("--quiet")
    cmd.append(package_spec)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception:
        return False


def ensure_markitdown():
    """
    Ensure markitdown is importable. Try installation strategies in order:
    1. Already installed (and not the 0.0.1a1 placeholder)
    2. pip install markitdown[all] from PyPI
    3. pip install markitdown from GitHub source
    """
    try:
        import markitdown as md
        if hasattr(md, "MarkItDown"):
            return md
    except ImportError:
        pass

    print("[office2md] Installing markitdown...", file=sys.stderr)

    if _pip_install("markitdown[all]"):
        try:
            import markitdown as md
            if hasattr(md, "MarkItDown"):
                print("[office2md] markitdown installed from PyPI.", file=sys.stderr)
                return md
        except ImportError:
            pass

    print("[office2md] PyPI version insufficient, trying GitHub source...", file=sys.stderr)
    if _pip_install("markitdown[all] @ git+https://github.com/microsoft/markitdown.git"):
        try:
            import markitdown as md
            if hasattr(md, "MarkItDown"):
                print("[office2md] markitdown installed from GitHub.", file=sys.stderr)
                return md
        except ImportError:
            pass

    raise RuntimeError(
        "Failed to install markitdown. Please install manually:\n"
        "  pip install markitdown[all]\n"
        "Or from source:\n"
        "  pip install 'markitdown[all] @ git+https://github.com/microsoft/markitdown.git'"
    )




# ── Native Excel fallback converter ───────────────────────────────────────
# Used when markitdown is not available but openpyxl is (or can be installed).

def _ensure_openpyxl():
    """Ensure openpyxl is importable. Returns the module or None."""
    try:
        import openpyxl
        return openpyxl
    except ImportError:
        pass

    print("[office2md] markitdown unavailable; trying openpyxl for Excel...", file=sys.stderr)
    if _pip_install("openpyxl", quiet=True):
        try:
            import openpyxl
            print("[office2md] openpyxl installed (Excel fallback).", file=sys.stderr)
            return openpyxl
        except ImportError:
            pass
    return None


def _native_convert_xlsx(file_path: str) -> str:
    """
    Convert an .xlsx file to Markdown using openpyxl (native fallback).
    Each worksheet becomes a section with a heading and a Markdown table.
    Merged cells are flattened to the top-left value.
    """
    openpyxl_mod = _ensure_openpyxl()
    if openpyxl_mod is None:
        raise RuntimeError(
            "Neither markitdown nor openpyxl is available for Excel conversion."
        )

    wb = openpyxl_mod.load_workbook(file_path, data_only=True)
    output_parts = []

    for sheet_idx, sheet_name in enumerate(wb.sheetnames, 1):
        ws = wb[sheet_name]
        output_parts.append(f"# Sheet {sheet_idx}: {sheet_name}")
        output_parts.append("")

        # Determine the actual data range
        max_row = ws.max_row or 0
        max_col = ws.max_column or 0

        if max_row == 0 or max_col == 0:
            output_parts.append("*(空工作表 / Empty sheet)*")
            output_parts.append("")
            continue

        # Build merged cell map for fast lookup
        merged_map = {}
        for merged_range in ws.merged_cells.ranges:
            min_row_r = merged_range.min_row
            min_col_r = merged_range.min_col
            max_row_r = merged_range.max_row
            max_col_r = merged_range.max_col
            top_left_val = ws.cell(row=min_row_r, column=min_col_r).value
            for r in range(min_row_r, max_row_r + 1):
                for c in range(min_col_r, max_col_r + 1):
                    merged_map[(r, c)] = str(top_left_val) if top_left_val is not None else ""

        # Determine first non-empty and last non-empty column
        _first_col = max_col + 1
        _last_col = 0
        for row_idx in range(1, max_row + 1):
            for col_idx in range(1, max_col + 1):
                key = (row_idx, col_idx)
                if key in merged_map:
                    _val = merged_map[key]
                else:
                    _v = ws.cell(row=row_idx, column=col_idx).value
                    _val = str(_v) if _v is not None else ""
                if _val.strip():
                    if col_idx < _first_col:
                        _first_col = col_idx
                    if col_idx > _last_col:
                        _last_col = col_idx

        if _last_col == 0:
            output_parts.append("*(无数据 / No data)*")
            output_parts.append("")
            continue

        col_offset = _first_col - 1
        num_cols = _last_col - _first_col + 1



        # Collect all rows (using trimmed column range)
        rows_data = []
        for row_idx in range(1, max_row + 1):
            row_vals = []
            for col_idx in range(_first_col, _last_col + 1):
                key = (row_idx, col_idx)
                if key in merged_map:
                    row_vals.append(merged_map[key])
                else:
                    cell = ws.cell(row=row_idx, column=col_idx)
                    val = cell.value
                    if val is None:
                        row_vals.append("")
                    else:
                        row_vals.append(str(val))
            rows_data.append(row_vals)

        # Trim trailing empty rows
        while rows_data and all(v.strip() == "" for v in rows_data[-1]):
            rows_data.pop()
        # Trim leading empty rows
        while rows_data and all(v.strip() == "" for v in rows_data[0]):
            rows_data.pop(0)

        if not rows_data:
            output_parts.append("*(无数据 / No data)*")
            output_parts.append("")
            continue

        # Find header row (first non-empty row)
        # We treat all rows as data rows and render a table.
        # First row is used as header if it looks like one (non-numeric, mostly strings)
        first_row = rows_data[0]
        non_empty = [v for v in first_row if v.strip()]

        # Build Markdown table
        # Pad rows to uniform length (should already be uniform, but just in case)
        padded = []
        for r in rows_data:
            padded.append(r + [""] * (num_cols - len(r)))

        # Trim trailing empty columns (find actual rightmost non-empty)
        def _rightmost_nonempty(rows):
            rightmost = 0
            for r in rows:
                for i in range(len(r) - 1, -1, -1):
                    if r[i].strip():
                        if i + 1 > rightmost:
                            rightmost = i + 1
                        break
            return rightmost

        _rm = _rightmost_nonempty(padded)
        if _rm > 0 and _rm < num_cols:
            padded = [r[:_rm] for r in padded]
            num_cols = _rm

        # Detect rows that are effectively a single merged title
        # (all non-empty cells have the same value) and emit as text instead
        def _is_merged_title(row):
            nonempty = [v.strip() for v in row if v.strip()]
            if len(nonempty) <= 1:
                return False
            return all(v == nonempty[0] for v in nonempty)

        # Escape pipes in cell content
        def _escape(val):
            return val.replace("|", "\\|").replace("\n", " ")

        # Render: separate title rows from table rows
        table_rows = []
        title_texts = []
        for row in padded:
            if _is_merged_title(row):
                for v in row:
                    if v.strip():
                        title_texts.append(v.strip())
                        break
            else:
                table_rows.append(row)

        # Emit title rows as plain text
        for t in title_texts:
            output_parts.append(t)
            output_parts.append("")

        if not table_rows:
            output_parts.append("*(无表格数据 / No tabular data)*")
            output_parts.append("")
            continue

        header = table_rows[0]
        data_rows = table_rows[1:]

        header_cells = [_escape(c) for c in header]
        output_parts.append("| " + " | ".join(header_cells) + " |")
        output_parts.append("| " + " | ".join(["---"] * num_cols) + " |")

        for row in data_rows:
            cells = [_escape(c) for c in row]
            output_parts.append("| " + " | ".join(cells) + " |")

        output_parts.append("")

    wb.close()
    return "\n".join(output_parts)

# ── Semantic post-processing ──────────────────────────────────────────────

# Keywords that indicate a column/header is a ratio/percentage/progress field
# (Chinese and English)
RATIO_KEYWORDS = [
    # Chinese - 占比/比例类
    "占比", "比重", "比例", "比率", "份额", "百分比", "百分率",
    "占营收比", "占收入比", "占成本比", "占费用比", "占利润比",
    "占总资产比", "占净资产比", "占负债比", "占权益比",
    "占销售额比", "占营业额比", "占市场比", "占行业比",
    # Chinese - 完成率/进度类
    "完成率", "完成度", "完成比例", "完成进度", "完工比例", "完工进度",
    "达成率", "达成度", "达成比例", "执行率", "执行度", "执行比例",
    "进度", "进展", "推进率", "推进度",
    # Chinese - 增长率/变化率类
    "增长率", "增速", "增幅", "涨幅", "降幅", "跌幅",
    "同比", "环比", "年增长率", "月增长率", "季度增长率",
    "同比增长率", "环比增长率", "年增幅", "月增幅",
    # Chinese - 率类指标（财务/运营）
    "利润率", "毛利率", "净利率", "营业利润率", "净利润率",
    "收益率", "回报率", "投资回报率", "roi", "资产收益率", "roa", "净资产收益率", "roe",
    "转化率", "点击率", "打开率", "复购率", "留存率", "流失率", " churn",
    "通过率", "失败率", "成功率", "准确率", "正确率", "错误率", "命中率",
    "覆盖率", "渗透率", "市场占有率", "市场份额",
    "周转率", "周转天数", "存货周转率", "应收账款周转率",
    "负债率", "资产负债率", "负债比率", "杠杆率",
    "流动性比率", "速动比率", "流动比率",
    "利率", "税率", "折扣率", "折旧率", "摊销率",
    "增长率", "下降率", "上升率", "变化率",
    "占比%", "占比 %", "比例%", "比率%",
    # Chinese - 特殊业务场景
    "应收账款占营收比", "存货占资产比", "现金占总资产比",
    "研发投入占收入比", "研发费用占比", "人力成本占比",
    "运营成本占比", "销售费用占比", "管理费用占比",
    "实际完工比例", "计划完工比例", "累计完工比例",
    "收入确认比例", "收入完成率", "预算完成率",
    # English - ratio/percentage
    "ratio", "rate", "percentage", "percent", "proportion", "share",
    "growth rate", "growth", "increase rate", "decrease rate",
    "completion rate", "completion ratio", "progress",
    "conversion rate", "click-through rate", "ctr",
    "retention rate", "churn rate", "turnover rate",
    "accuracy rate", "error rate", "success rate", "failure rate",
    "coverage rate", "penetration rate", "market share",
    "profit margin", "gross margin", "net margin", "operating margin",
    "return on investment", "roi", "return on assets", "roa",
    "return on equity", "roe", "internal rate of return", "irr",
    "debt ratio", "debt-to-equity", "leverage ratio",
    "current ratio", "quick ratio", "liquidity ratio",
    "interest rate", "tax rate", "discount rate", "depreciation rate",
    "inventory turnover", "receivables turnover", "asset turnover",
    "year-over-year", "yoy", "month-over-month", "mom",
    "quarter-over-quarter", "qoq",
]

# Patterns for detecting ratio-like context: "X of Y", "X/Y" where both are numbers
RATIO_CONTEXT_PATTERNS = [
    re.compile(r"(\d+\.?\d*)\s*/\s*(\d+\.?\d*)"),  # e.g., "3/5" or "0.5/1"
]


class ConversionChange:
    """Represents a single non-faithful change made during post-processing."""

    def __init__(self, category: str, location: str, original: str,
                 transformed: str, reason: str, risk_level: str = "low"):
        self.category = category        # e.g., "decimal_to_percentage"
        self.location = location        # e.g., "Table 2, row 3, '占比' column"
        self.original = original        # original text snippet
        self.transformed = transformed  # transformed text snippet
        self.reason = reason            # why the change was made
        self.risk_level = risk_level    # "low", "medium", "high"

    def to_dict(self):
        return {
            "category": self.category,
            "location": self.location,
            "original": self.original,
            "transformed": self.transformed,
            "reason": self.reason,
            "risk_level": self.risk_level,
        }


def _is_ratio_header(text: str) -> bool:
    """Check if a header/label text indicates a ratio/percentage field."""
    text_lower = text.lower().strip()
    
    # Check against keyword list
    for kw in RATIO_KEYWORDS:
        if kw.lower() in text_lower:
            return True
    
    # Pattern matching for Chinese "X占Y比" structures
    if re.search(r'[\u4e00-\u9fa5]+占[\u4e00-\u9fa5]+比', text):
        return True
    
    # Pattern matching for "X率" where X is Chinese characters
    if re.search(r'[\u4e00-\u9fa5]{2,}率', text):
        return True
    
    # Pattern matching for "X度" (degree/completion)
    if re.search(r'[\u4e00-\u9fa5]{2,}度', text):
        return True
    
    # Pattern matching for English "X rate", "X ratio", "X percentage"
    if re.search(r'\b\w+\s+(rate|ratio|percentage|percent|proportion)\b', text_lower):
        return True
    
    return False


def _looks_like_decimal_ratio(value_str: str) -> bool:
    """Check if a string looks like a decimal ratio between 0 and 1 (or -1 and 1)."""
    try:
        v = float(value_str.strip())
    except (ValueError, AttributeError):
        return False
    # Must be between -1 and 1, and not a whole number like 0 or 1
    # (whole numbers are ambiguous — could be counts)
    if -1.0 <= v <= 1.0 and v != 0 and v != 1 and v != -1:
        # Additional heuristic: must have decimal point
        if "." in value_str.strip():
            return True
    return False


def _decimal_to_percentage(value_str: str) -> str:
    """Convert a decimal ratio string to a percentage string.

    Preserves the number of decimal places in the percentage output.
    E.g., "0.23" → "23%", "0.125" → "12.5%", "-0.05" → "-5%"
    """
    v = float(value_str.strip())
    pct = v * 100

    # Count decimal places in the input to determine output precision
    stripped = value_str.strip()
    if "." in stripped:
        decimals = len(stripped.split(".")[-1])
    else:
        decimals = 0

    # Percentage typically has 0-2 decimal places for readability
    # but we try to preserve significance
    pct_decimals = max(0, decimals - 2) if v != 0 else decimals

    if pct_decimals > 0:
        return f"{pct:.{pct_decimals}f}%"
    else:
        return f"{round(pct)}%"


def post_process_markdown(markdown_text: str, semantic: bool = True) -> tuple:
    """
    Apply semantic post-processing to Markdown text.

    Args:
        markdown_text: The raw converted Markdown.
        semantic: Whether to enable semantic transformations.

    Returns:
        (processed_text, list_of_changes)
    """
    changes = []

    if not semantic:
        return markdown_text, changes

    lines = markdown_text.split("\n")
    processed_lines = list(lines)
    current_table_headers = []
    in_table = False
    table_start_line = -1
    table_name = ""
    table_counter = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect table start (markdown table header row followed by separator)
        if "|" in stripped and i + 1 < len(lines) and re.match(
                r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", lines[i + 1]):
            in_table = True
            table_counter += 1
            table_start_line = i
            # Look back for a heading that names the table
            for j in range(i - 1, max(i - 5, -1), -1):
                if lines[j].strip().startswith("#"):
                    table_name = lines[j].strip().lstrip("#").strip()
                    break
            if not table_name:
                table_name = f"Table {table_counter}"
            # Parse headers
            current_table_headers = [
                h.strip() for h in stripped.strip("|").split("|")
            ]
            continue

        # Table separator row
        if in_table and re.match(
                r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", stripped):
            continue

        # End of table (blank line or non-table line)
        if in_table and (not stripped or "|" not in stripped):
            in_table = False
            current_table_headers = []
            continue

        # Process table data rows
        if in_table and "|" in stripped and current_table_headers:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            row_num = i - table_start_line - 1  # -1 for separator row
            modified = False
            new_cells = list(cells)

            for col_idx, (header, cell) in enumerate(
                    zip(current_table_headers, cells)):
                if _is_ratio_header(header) and _looks_like_decimal_ratio(cell):
                    original_val = cell
                    new_val = _decimal_to_percentage(cell)
                    new_cells[col_idx] = new_val
                    modified = True
                    changes.append(ConversionChange(
                        category="decimal_to_percentage",
                        location=f"{table_name}, row {row_num}, column '{header}'",
                        original=original_val,
                        transformed=new_val,
                        reason=f"Column '{header}' identified as a ratio/percentage field; "
                               f"decimal value {original_val} is more readable as percentage.",
                        risk_level="medium",  # could be wrong if the value is actually not a ratio
                    ))

            if modified:
                # Reconstruct the table row
                # Preserve original padding style by rebuilding the row
                processed_lines[i] = "| " + " | ".join(new_cells) + " |"

    # Also handle inline patterns: "X%", "占比: 0.5", etc.
    # Pattern: label (ratio keyword) + colon/separator + decimal
    inline_pattern = re.compile(
        r"([\u4e00-\u9fa5A-Za-z\s]{2,30}?[:：]\s*)"  # label with colon
        r"(-?\d+\.\d+)"                               # decimal value
        r"(\s|$|\)|\]|,|，)"                          # delimiter
    )

    # We do a second pass for inline conversions that are clearly ratio context
    text_joined = "\n".join(processed_lines)
    inline_changes = []

    def _inline_replace(match):
        label_part = match.group(1)
        value = match.group(2)
        tail = match.group(3)

        # Check if label contains ratio keywords
        label_text = label_part.rstrip("：:").strip()
        if _is_ratio_header(label_text) and _looks_like_decimal_ratio(value):
            new_val = _decimal_to_percentage(value)
            inline_changes.append(ConversionChange(
                category="decimal_to_percentage",
                location=f"Inline: '{label_text}'",
                original=value,
                transformed=new_val,
                reason=f"Field '{label_text}' identified as ratio field; "
                       f"decimal value converted to percentage for readability.",
                risk_level="medium",
            ))
            return label_part + new_val + tail
        return match.group(0)

    text_joined = inline_pattern.sub(_inline_replace, text_joined)
    changes.extend(inline_changes)

    return text_joined, changes


# ── Conversion report generation ──────────────────────────────────────────

def generate_report(input_path: str, output_path: str,
                    changes: list, steps: list,
                    conversion_time: float,
                    raw_length: int,
                    processed_length: int) -> str:
    """
    Generate a conversion report in Markdown format.

    Args:
        input_path: Path to the source file.
        output_path: Path to the output Markdown file.
        changes: List of ConversionChange objects.
        steps: List of (step_name, description) tuples.
        conversion_time: Time taken in seconds.
        raw_length: Character length of raw conversion output.
        processed_length: Character length of post-processed output.

    Returns:
        Markdown string of the report.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    input_name = os.path.basename(input_path)
    output_name = os.path.basename(output_path) if output_path else "(stdout)"

    # Categorize changes by risk level
    high_risk = [c for c in changes if c.risk_level == "high"]
    medium_risk = [c for c in changes if c.risk_level == "medium"]
    low_risk = [c for c in changes if c.risk_level == "low"]

    report = []
    report.append(f"# 转换说明文档 / Conversion Report")
    report.append("")
    report.append(f"- **工具**: office2md v{__version__}")
    report.append(f"- **源文件**: `{input_name}`")
    report.append(f"- **输出文件**: `{output_name}`")
    report.append(f"- **转换时间**: {now}")
    report.append(f"- **耗时**: {conversion_time:.2f}s")
    report.append(f"- **原始转换字数**: {raw_length} 字符")
    report.append(f"- **处理后字数**: {processed_length} 字符")
    report.append(f"- **语义修改数**: {len(changes)} 处")
    report.append("")

    # Key steps
    report.append("## 转换关键步骤")
    report.append("")
    for idx, (step_name, step_desc) in enumerate(steps, 1):
        report.append(f"{idx}. **{step_name}** — {step_desc}")
    report.append("")

    # Non-faithful transformations
    report.append("## 非忠实转换内容")
    report.append("")
    if not changes:
        report.append("本次转换未进行任何非忠实修改，输出为忠实转换结果。")
        report.append("")
    else:
        report.append(
            f"本次转换共进行了 **{len(changes)}** 处语义层面的非忠实修改，"
            f"目的是提升 Markdown 的可读性和实用性。"
        )
        report.append("")
        report.append("| # | 类别 | 位置 | 原值 | 转换后 | 原因 | 风险 |")
        report.append("|---|------|------|------|--------|------|------|")
        for idx, c in enumerate(changes, 1):
            risk_label = {
                "high": "🔴 高",
                "medium": "🟡 中",
                "low": "🟢 低",
            }.get(c.risk_level, c.risk_level)
            report.append(
                f"| {idx} | {c.category} | {c.location} | `{c.original}` | "
                f"`{c.transformed}` | {c.reason} | {risk_label} |"
            )
        report.append("")

    # Risk assessment
    report.append("## 风险提示与复核建议")
    report.append("")

    if not changes:
        report.append("无风险项。输出为忠实转换，可直接使用。")
    else:
        if high_risk:
            report.append("### 🔴 高风险（强烈建议人工复核）")
            report.append("")
            for c in high_risk:
                report.append(f"- **{c.location}**: `{c.original}` → `{c.transformed}` — {c.reason}")
            report.append("")

        if medium_risk:
            report.append("### 🟡 中等风险（建议快速复核）")
            report.append("")
            for c in medium_risk:
                report.append(f"- **{c.location}**: `{c.original}` → `{c.transformed}` — {c.reason}")
            report.append("")

        if low_risk:
            report.append("### 🟢 低风险（通常无需复核）")
            report.append("")
            for c in low_risk:
                report.append(f"- **{c.location}**: `{c.original}` → `{c.transformed}` — {c.reason}")
            report.append("")

        report.append("### 通用建议")
        report.append("")
        report.append(
            "- 数值类转换基于列名/标签的语义推断，可能存在误判。"
            "若某列的值并非比率但被识别为比率，请忽略该转换。"
        )
        report.append(
            "- 百分比小数位数根据原小数精度推断，商务报告中建议统一保留 1-2 位小数。"
        )
        report.append(
            "- 表格结构复杂时（合并单元格、嵌套表），行号定位可能偏差，"
            "请以列名和内容匹配为准。"
        )

    report.append("")
    report.append("---")
    report.append(f"*Generated by office2md v{__version__}*")

    return "\n".join(report)


# ── Core conversion functions ─────────────────────────────────────────────

def convert_file(input_path: str, output_path: str = None,
                 semantic: bool = True, report: bool = True,
                 **kwargs) -> tuple:
    """
    Convert a single file to Markdown.

    Args:
        input_path: Path to the input file or URL.
        output_path: Optional path to write the Markdown output.
        semantic: Whether to apply semantic post-processing (default: True).
        report: Whether to generate a conversion report (default: True).
        **kwargs: Additional keyword arguments for MarkItDown constructor.

    Returns:
        (markdown_text, report_text_or_None, changes_list)
    """
    steps = []
    start_time = time.time()

    # Step 1: Faithful conversion
    # Determine file extension for fallback routing
    _ext = os.path.splitext(input_path)[1].lower() if not input_path.startswith(("http://", "https://")) else ""

    md = None
    _used_fallback = False
    _fallback_reason = ""

    try:
        md = ensure_markitdown()
        steps.append(("忠实转换", "使用 markitdown 库将源文件转换为原始 Markdown"))
    except RuntimeError as e:
        # markitdown not available; check if we can use a native fallback
        if _ext in (".xlsx", ".xls", ".csv"):
            _used_fallback = True
            _fallback_reason = "markitdown 不可用，使用 openpyxl 本地转换器（Excel fallback）"
            steps.append(("忠实转换", _fallback_reason))
        else:
            raise e

    if _used_fallback:
        # Native fallback converters
        if _ext in (".xlsx", ".xls"):
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            raw_markdown = _native_convert_xlsx(input_path)
        elif _ext == ".csv":
            # CSV fallback using Python stdlib
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            import csv as _csv
            with open(input_path, "r", encoding="utf-8-sig") as f:
                reader = _csv.reader(f)
                rows = list(reader)
            if rows:
                header = rows[0]
                data = rows[1:]
                lines = []
                lines.append("| " + " | ".join(header) + " |")
                lines.append("| " + " | ".join(["---"] * len(header)) + " |")
                for row in data:
                    lines.append("| " + " | ".join(row) + " |")
                raw_markdown = "\n".join(lines)
            else:
                raw_markdown = ""
        else:
            raise RuntimeError(f"No fallback converter available for {_ext} files")
    else:
        init_kwargs = {}
        for key in ("enable_ocr", "ocr_engine", "enable_vision", "gpt_model"):
            if key in kwargs and kwargs[key] is not None:
                init_kwargs[key] = kwargs[key]

        converter = md.MarkItDown(**init_kwargs)

        if input_path.startswith(("http://", "https://")):
            result = converter.convert(url=input_path)
        else:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            result = converter.convert(input_path)

        raw_markdown = result.text_content if hasattr(result, "text_content") else str(result)
    raw_length = len(raw_markdown)

    # Step 2: Semantic post-processing
    changes = []
    if semantic:
        steps.append(("语义后处理", "基于列名/标签的语义识别，将小数量值的比率字段转换为百分数"))
        processed_markdown, changes = post_process_markdown(raw_markdown, semantic=True)
    else:
        processed_markdown = raw_markdown
        steps.append(("语义后处理", "已禁用（忠实模式），不进行非忠实转换"))

    processed_length = len(processed_markdown)
    conversion_time = time.time() - start_time

    # Step 3: Generate report
    report_text = None
    if report and output_path:
        steps.append(("生成转换报告", "记录转换步骤、非忠实修改项及风险提示"))
        report_text = generate_report(
            input_path=input_path,
            output_path=output_path,
            changes=changes,
            steps=steps,
            conversion_time=conversion_time,
            raw_length=raw_length,
            processed_length=processed_length,
        )

    # Write output
    if output_path:
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(processed_markdown)
        print(f"[office2md] Converted: {input_path} -> {output_path}", file=sys.stderr)

        # Write report alongside output
        if report_text:
            base, ext = os.path.splitext(output_path)
            report_path = f"{base}.report.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"[office2md] Report: {report_path}", file=sys.stderr)

    return processed_markdown, report_text, changes


def convert_directory(input_dir: str, output_dir: str = None,
                      recursive: bool = True, semantic: bool = True,
                      report: bool = True, **kwargs) -> list:
    """
    Convert all supported files in a directory to Markdown.

    Returns:
        List of dicts with keys: input, output, success, changes_count, report_path
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    output_dir = Path(output_dir) if output_dir else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    skip_extensions = {
        ".md", ".py", ".js", ".ts", ".go", ".rs", ".c", ".cpp", ".h",
        ".css", ".scss", ".less", ".map",
    }

    results = []
    glob_pattern = "**/*" if recursive else "*"

    for file_path in sorted(input_dir.glob(glob_pattern)):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() in skip_extensions:
            continue
        # Skip report files
        if file_path.name.endswith(".report.md"):
            continue
        if file_path.name.startswith("."):
            continue

        rel_path = file_path.relative_to(input_dir)
        out_path = output_dir / rel_path.with_suffix(".md")

        try:
            _, _, changes = convert_file(
                str(file_path), str(out_path),
                semantic=semantic, report=report, **kwargs,
            )
            report_path = str(out_path).replace(".md", ".report.md") if report else None
            results.append({
                "input": str(file_path),
                "output": str(out_path),
                "success": True,
                "changes_count": len(changes),
                "report_path": report_path,
            })
        except Exception as e:
            print(f"[office2md] Skipping {file_path}: {e}", file=sys.stderr)
            results.append({
                "input": str(file_path),
                "output": None,
                "success": False,
                "changes_count": 0,
                "report_path": None,
                "error": str(e),
            })

    return results


# ── Environment info ──────────────────────────────────────────────────────

def check_environment() -> dict:
    global __version__
    """Check what's available in the current environment."""
    info = {
        "office2md_version": __version__,
        "python_version": sys.version,
        "markitdown_installed": False,
        "markitdown_version": None,
        "supported_formats": [
            ".docx", ".doc", ".xlsx", ".xls", ".csv", ".pptx", ".ppt",
            ".pdf", ".html", ".htm", ".json", ".xml", ".ipynb", ".zip",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",
            ".mp3", ".mp4", ".wav", ".mpga", ".mpeg",
            ".txt", ".rtf", ".yaml", ".yml",
        ],
    }

    try:
        import markitdown as md
        if hasattr(md, "MarkItDown"):
            info["markitdown_installed"] = True
            try:
                from markitdown.__about__ import __version__
                info["markitdown_version"] = __version__
            except ImportError:
                info["markitdown_version"] = "unknown"
    except ImportError:
        pass

    return info


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert Office documents and files to Markdown (wrapper for markitdown).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 convert.py document.docx
  python3 convert.py document.docx output.md
  python3 convert.py report.pdf -o report.md
  python3 convert.py --dir ./docs --output-dir ./docs-md
  python3 convert.py https://example.com/page.html
  python3 convert.py image.png --ocr
  python3 convert.py data.xlsx --no-semantic      # faithful-only mode
  python3 convert.py --check
  python3 convert.py --formats
  python3 convert.py --version
""",
    )
    parser.add_argument("input", nargs="?", help="Input file path or URL")
    parser.add_argument("output", nargs="?", help="Output Markdown file path (positional)")
    parser.add_argument("-o", "--output", dest="output_opt", help="Output Markdown file path")
    parser.add_argument("--dir", help="Convert all files in a directory")
    parser.add_argument("--output-dir", help="Output directory for batch conversion")
    parser.add_argument("--no-recursive", action="store_true",
                        help="Don't recurse into subdirectories in batch mode")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR for image files")
    parser.add_argument("--ocr-engine", choices=["tesseract", "azure"],
                        help="OCR engine to use (tesseract or azure)")
    parser.add_argument("--vision", action="store_true",
                        help="Enable vision model for image understanding")
    parser.add_argument("--gpt-model", help="OpenAI model name for vision/complex tasks")
    parser.add_argument("--no-semantic", action="store_true",
                        help="Disable semantic post-processing (faithful conversion only)")
    parser.add_argument("--no-report", action="store_true",
                        help="Don't generate a conversion report")
    parser.add_argument("--check", action="store_true",
                        help="Check environment and markitdown availability")
    parser.add_argument("--formats", action="store_true", help="List supported file formats")
    parser.add_argument("--version", action="store_true", help="Show office2md version")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if args.version:
        print(f"office2md v{__version__}")
        return 0

    if args.check:
        info = check_environment()
        if args.json:
            print(json.dumps(info, indent=2, default=str))
        else:
            print(f"office2md: v{info['office2md_version']}")
            print(f"Python: {info['python_version'].split()[0]}")
            print(f"markitdown installed: {info['markitdown_installed']}")
            if info["markitdown_version"]:
                print(f"markitdown version: {info['markitdown_version']}")
        return 0

    if args.formats:
        info = check_environment()
        if args.json:
            print(json.dumps({"formats": info["supported_formats"]}, indent=2))
        else:
            print("Supported formats:")
            for fmt in info["supported_formats"]:
                print(f"  {fmt}")
            print("\nNote: Actual format support depends on installed dependencies.")
            print("Run with --check to see what's available.")
        return 0

    if not args.input and not args.dir:
        parser.print_help()
        return 1

    semantic = not args.no_semantic
    report = not args.no_report

    kwargs = {}
    if args.ocr:
        kwargs["enable_ocr"] = True
    if args.ocr_engine:
        kwargs["ocr_engine"] = args.ocr_engine
    if args.vision:
        kwargs["enable_vision"] = True
    if args.gpt_model:
        kwargs["gpt_model"] = args.gpt_model

    output_path = args.output_opt or args.output

    try:
        if args.dir:
            results = convert_directory(
                args.dir, args.output_dir,
                recursive=not args.no_recursive,
                semantic=semantic, report=report,
                **kwargs,
            )
            if args.json:
                print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                success = sum(1 for r in results if r["success"])
                total = len(results)
                total_changes = sum(r["changes_count"] for r in results)
                print(f"\nConverted {success}/{total} files, "
                      f"{total_changes} semantic changes total.", file=sys.stderr)
            return 0 if all(r["success"] for r in results) else 1
        else:
            markdown, report_text, changes = convert_file(
                args.input, output_path,
                semantic=semantic, report=report,
                **kwargs,
            )
            if not output_path:
                print(markdown)
                if report_text:
                    print("\n\n---\n\n")
                    print(report_text)
            elif args.json:
                print(json.dumps({
                    "input": args.input,
                    "output": output_path,
                    "changes_count": len(changes),
                    "changes": [c.to_dict() for c in changes],
                    "report_path": output_path.replace(".md", ".report.md") if report else None,
                }, indent=2, ensure_ascii=False))
            return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
