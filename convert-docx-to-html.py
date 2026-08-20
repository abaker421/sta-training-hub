#!/usr/bin/env python3
"""
Convert .docx files in dist/files/ into styled HTML files in dist/docs/.

=============================================================================
EVERY FILE THIS SCRIPT WRITES IS GENERATED. DO NOT HAND-EDIT THE OUTPUT.
=============================================================================
The HTML in dist/docs/ produced by this script is overwritten on the next run.
A correction made directly to one of those .html files disappears silently -
no error, no warning, and the page goes back to saying whatever the .docx
says. Edit the .docx in dist/files/ and re-run this script instead.

Current generated pairs (input -> output):
  dist/files/ai-acceptable-use-policy.docx        -> dist/docs/ai-acceptable-use-policy.html
  dist/files/ai-restricted-data-reference-guide.docx
                                                  -> dist/docs/ai-restricted-data-reference-guide.html
  dist/files/ai-rollout-plan.docx                 -> dist/docs/ai-rollout-plan.html
  dist/files/sta-salesforce-org-intake.docx       -> dist/docs/sta-salesforce-org-intake.html

Origin: 2026-08-20. A false privacy assurance in the AUP was corrected in the
generated HTML while the .docx kept the original wording, so the fix was one
converter run from vanishing and nothing would have flagged it. This note is
the tripwire that was missing.
=============================================================================

Run this any time a source .docx is updated. The output HTML preserves
the document's colors, tables, and images (base64-inlined), wrapped in
STA brand styling for clean in-app rendering.

Requirements:
  - LibreOffice (headless mode)
  - Python 3.6+

Usage:
  python3 convert-docx-to-html.py            # Convert all .docx in dist/files/
  python3 convert-docx-to-html.py FILE.docx  # Convert a single file
"""

import subprocess
import base64
import re
import os
import shutil
import sys
import tempfile
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent
SRC_DIR = HUB_ROOT / "dist" / "files"
DEST_DIR = HUB_ROOT / "dist" / "docs"

# STA brand wrapper - applied to every converted doc
WRAPPER_CSS = """
<style>
  :root {
    --sta-navy: #1A1A2E;
    --sta-blue: #004b8d;
    --sta-light-blue: #006098;
    --sta-green: #6bc04b;
    --sta-text: #1f2d3d;
    --sta-muted: #5c6b7a;
    --sta-bg: #f6f7f9;
    --sta-border: #e0e6ed;
  }
  html, body {
    margin: 0;
    padding: 0;
    background: var(--sta-bg);
    color: var(--sta-text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.55;
  }
  .doc-shell {
    max-width: 900px;
    margin: 24px auto;
    background: #fff;
    padding: 48px 56px;
    box-shadow: 0 2px 12px rgba(26,26,46,0.08);
    border-radius: 8px;
  }
  .doc-shell h1, .doc-shell h2, .doc-shell h3, .doc-shell h4 {
    color: var(--sta-blue);
    font-family: Arial, sans-serif;
  }
  .doc-shell h1 { font-size: 22px; margin-top: 28px; margin-bottom: 12px; }
  .doc-shell h2 { font-size: 17px; margin-top: 22px; margin-bottom: 10px; }
  .doc-shell h3 { font-size: 15px; margin-top: 18px; margin-bottom: 8px; }
  .doc-shell p { margin: 8px 0; }
  .doc-shell a { color: var(--sta-light-blue); }
  .doc-shell table { border-collapse: collapse; margin: 12px 0; max-width: 100%; }
  .doc-shell table td, .doc-shell table th { border: 1px solid #cccccc; padding: 8px 10px; vertical-align: top; }
  .doc-shell img { max-width: 100%; height: auto; }
  .doc-shell ul, .doc-shell ol { margin: 8px 0 8px 24px; padding-left: 0; }
  .doc-shell li { margin: 4px 0; }
  .doc-shell td[bgcolor] { color: inherit; }
  .doc-shell font[color="#ffffff"] { color: #fff !important; }
  .doc-shell div[title="header"], .doc-shell div[title="footer"] { margin: 0; padding: 0; }
  @media (max-width: 700px) {
    .doc-shell { margin: 0; padding: 20px 18px; border-radius: 0; box-shadow: none; }
  }
</style>
"""


def inline_images(html_content, work_dir):
    """Replace <img src='localfile.jpg'> with base64 data URIs so each
    output HTML is fully self-contained."""
    def replace_img(match):
        full_tag = match.group(0)
        src_match = re.search(r'src="([^"]+)"', full_tag)
        if not src_match:
            return full_tag
        src = src_match.group(1)
        img_path = work_dir / src
        if not img_path.exists():
            return full_tag
        ext = img_path.suffix.lower()
        mime = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
        }.get(ext, 'application/octet-stream')
        with open(img_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        return full_tag.replace(src, f'data:{mime};base64,{b64}')
    return re.sub(r'<img[^>]+>', replace_img, html_content)


def convert_one(filename):
    """Convert a single .docx file to styled HTML. Returns output path or None."""
    print(f"\n=== {filename} ===")
    src_file = SRC_DIR / filename
    if not src_file.exists():
        print(f"  FAIL: source file not found at {src_file}")
        return None

    with tempfile.TemporaryDirectory(prefix="docx-convert-") as tmp:
        work_dir = Path(tmp)
        shutil.copy2(src_file, work_dir / filename)

        result = subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'html',
             '--outdir', str(work_dir), str(work_dir / filename)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  FAIL: libreoffice returned {result.returncode}")
            print(f"  stderr: {result.stderr}")
            return None

        html_basename = filename.replace('.docx', '.html')
        html_file = work_dir / html_basename
        if not html_file.exists():
            print(f"  FAIL: no HTML produced")
            return None

        html = html_file.read_text(encoding='utf-8')

        # Preserve the LibreOffice <style> block (it has the h1/h2/td colors etc.)
        head_style_match = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
        lo_style = head_style_match.group(1) if head_style_match else ''

        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
        if not body_match:
            print(f"  FAIL: no <body> in output")
            return None
        body_content = body_match.group(1)

        body_content = inline_images(body_content, work_dir)

        title = filename.replace('.docx', '').replace('-', ' ').title()
        final = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{WRAPPER_CSS}
<style>
/* preserved from source */
{lo_style}
</style>
</head>
<body>
<div class="doc-shell">
{body_content}
</div>
</body>
</html>
"""

        out_path = DEST_DIR / html_basename
        out_path.write_bytes(final.encode('utf-8'))
        print(f"  OK -> {out_path.name} ({len(final):,} bytes)")
        return out_path


def main():
    if not shutil.which('libreoffice'):
        print("ERROR: libreoffice not found in PATH. Install it or run this in the workspace shell.")
        sys.exit(1)
    if not SRC_DIR.exists():
        print(f"ERROR: source folder not found: {SRC_DIR}")
        sys.exit(1)
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        # single-file mode
        targets = [sys.argv[1]]
    else:
        targets = sorted(f.name for f in SRC_DIR.iterdir() if f.suffix.lower() == '.docx')

    if not targets:
        print("No .docx files to convert.")
        return

    results = []
    for f in targets:
        r = convert_one(f)
        if r:
            results.append(r)

    print(f"\n=== Summary ===")
    print(f"Converted: {len(results)}/{len(targets)}")
    print("\nNext step: sync source to dist if the app was edited too:")
    print('  cp "STA-Training-Hub.html" "dist/index.html"')
    print("\nThen redeploy (git push, or drag dist/ to Cloudflare Pages).")


if __name__ == "__main__":
    main()
