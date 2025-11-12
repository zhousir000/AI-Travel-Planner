from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

from fpdf import FPDF

FONT_CANDIDATES = [
    Path("fonts/NotoSansSC-Regular.otf"),
    Path("fonts/NotoSansCJKsc-Regular.otf"),
    Path("fonts/SourceHanSansCN-Normal.otf"),
]


def register_font(pdf: FPDF) -> str | None:
    for font_path in FONT_CANDIDATES:
        if font_path.exists():
            try:
                pdf.add_font("custom", "", str(font_path), uni=True)
                pdf.add_font("custom", "B", str(font_path), uni=True)
                return "custom"
            except Exception as exc:  # noqa: BLE001
                print(f"Failed to load font {font_path}: {exc}")
    return None


def render_pdf(repo_url: str, readme_text: str, output_path: Path) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_family = register_font(pdf) or "helvetica"
    if font_family == "helvetica":
        print("Warning: Unicode font not found. Non-ASCII characters will be dropped. "
              "Place NotoSansSC-Regular.otf under fonts/ to retain Chinese text.")

    pdf.set_font(font_family, "B", 18)
    pdf.multi_cell(0, 10, "AI Travel Planner Submission", align="L")
    pdf.ln(2)

    pdf.set_font(font_family, "", 12)
    pdf.multi_cell(0, 7, f"GitHub Repository: {repo_url}")
    pdf.ln(4)

    pdf.set_font(font_family, "B", 14)
    summary_title = "README Summary" if font_family == "helvetica" else "README 摘要"
    pdf.multi_cell(0, 8, summary_title)
    pdf.ln(2)

    pdf.set_font(font_family, "", 10)
    for line in readme_text.splitlines():
        text_line = line
        if font_family == "helvetica":
            text_line = line.encode("latin-1", "ignore").decode("latin-1")
        if not text_line.strip():
            pdf.ln(4)
        else:
            for chunk in textwrap.wrap(text_line, width=90, break_long_words=True, break_on_hyphens=False):
                if not chunk:
                    continue
                pdf.cell(0, 6, chunk, ln=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate assignment submission PDF.")
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository URL (ensure可访问).",
    )
    parser.add_argument(
        "--readme",
        default="README.md",
        help="Path to README file to embed into PDF (default: README.md).",
    )
    parser.add_argument(
        "--output",
        default="docs/submission.pdf",
        help="Output PDF path (default: docs/submission.pdf).",
    )
    args = parser.parse_args()

    readme_path = Path(args.readme)
    if not readme_path.exists():
        raise SystemExit(f"README not found: {readme_path}")
    readme_text = readme_path.read_text(encoding="utf-8")
    output_path = Path(args.output)

    render_pdf(args.repo, readme_text, output_path)
    print(f"PDF generated at {output_path.resolve()}")


if __name__ == "__main__":
    main()
