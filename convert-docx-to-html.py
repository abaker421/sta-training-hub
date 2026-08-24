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

The generated pairs are defined ONCE, in the GENERATED_PAIRS constant below.
That constant is the single source of truth: a bare run converts exactly those
pairs and nothing else. Deliberately NOT restated here - a prose copy of the
list is exactly what drifts out of sync with the code.

Any other .docx in dist/files/ is skipped, loudly, with the reason printed, and
single-file mode refuses it unless --add-new-pair is passed. sta-salesforce-org-intake.docx
is download-only, linked from the hub as files/sta-salesforce-org-intake.docx, and
must NOT get an HTML page. ai-rollout-plan.docx is no longer in dist/files/ at all -
it was unpublished on 2026-08-20 because it contradicted the AI Acceptable Use Policy
on admin visibility and published a named staff roster. Its source of record is
Training Materials/Training - Admin/AI Rollout Plan.docx.

Origin: 2026-08-20. A false privacy assurance in the AUP was corrected in the
generated HTML while the .docx kept the original wording, so the fix was one
converter run from vanishing and nothing would have flagged it. This note is
the tripwire that was missing.
=============================================================================

Run this any time a source .docx is updated. The output HTML preserves
the document's colors, tables, and images (base64-inlined), wrapped in
STA brand styling for clean in-app rendering.

Requirements:
  - LibreOffice (headless mode). The binary is resolved by name, preferring
    `soffice` and falling back to `libreoffice`, then to the standard install
    locations. This is not cosmetic: Windows ships soffice.exe / soffice.com and
    has NO `libreoffice` binary at all, so a hardcoded `libreoffice` cannot run
    there no matter what is on PATH.
  - Python 3.6+

Usage:
  python3 convert-docx-to-html.py            # Convert every GENERATED_PAIRS entry
  python3 convert-docx-to-html.py FILE.docx  # Convert one known pair
  python3 convert-docx-to-html.py FILE.docx --add-new-pair
                                             # Convert a .docx that is not yet a
                                             # known pair. Then add it to
                                             # GENERATED_PAIRS or a bare run will
                                             # never refresh it again.
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

# ---------------------------------------------------------------------------
# THE single source of truth for what this script generates (input -> output).
# A bare run converts exactly these and nothing else. Anything else in
# dist/files/ is skipped with a printed reason. Add an entry here - and only
# here - when a .docx genuinely needs a served HTML page.
# ---------------------------------------------------------------------------
GENERATED_PAIRS = {
    "ai-acceptable-use-policy.docx": "ai-acceptable-use-policy.html",
    "ai-restricted-data-reference-guide.docx": "ai-restricted-data-reference-guide.html",
}

# LibreOffice binary names in preference order. Windows has no `libreoffice`.
SOFFICE_NAMES = ("soffice", "libreoffice")

# Checked only when neither name is on PATH.
SOFFICE_FALLBACK_PATHS = (
    r"C:\Program Files\LibreOffice\program\soffice.com",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.com",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/usr/bin/libreoffice",
    "/usr/local/bin/soffice",
    "/usr/local/bin/libreoffice",
    "/snap/bin/libreoffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)


def find_soffice():
    """Return a runnable LibreOffice binary path, or None. Prefers `soffice`."""
    for name in SOFFICE_NAMES:
        found = shutil.which(name)
        if found:
            return found
    for path in SOFFICE_FALLBACK_PATHS:
        if os.path.isfile(path):
            return path
    return None


def soffice_not_found_message():
    """Error text naming every location that was checked."""
    lines = ["ERROR: no LibreOffice binary found. Checked all of the following.", ""]
    lines.append("On PATH, by name:")
    lines += ["    %s" % n for n in SOFFICE_NAMES]
    lines.append("")
    lines.append("Then these locations:")
    lines += ["    %s" % p for p in SOFFICE_FALLBACK_PATHS]
    lines += [
        "",
        "Install LibreOffice, or add its program directory to PATH:",
        "    Windows:       winget install TheDocumentFoundation.LibreOffice",
        "                   (installs soffice.exe / soffice.com - there is no",
        "                    'libreoffice' binary on Windows)",
        "    Debian/Ubuntu: apt install libreoffice",
        "    macOS:         brew install --cask libreoffice",
    ]
    return "\n".join(lines)


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


def convert_one(filename, soffice, out_name=None):
    """Convert a single .docx file to styled HTML. Returns output path or None.

    `soffice` is the resolved LibreOffice binary. `out_name` is the destination
    filename from GENERATED_PAIRS; it falls back to the input stem for a
    --add-new-pair run."""
    print(f"\n=== {filename} ===")
    src_file = SRC_DIR / filename
    if not src_file.exists():
        print(f"  FAIL: source file not found at {src_file}")
        return None

    with tempfile.TemporaryDirectory(prefix="docx-convert-") as tmp:
        work_dir = Path(tmp)
        shutil.copy2(src_file, work_dir / filename)

        result = subprocess.run(
            [soffice, '--headless', '--convert-to', 'html',
             '--outdir', str(work_dir), str(work_dir / filename)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  FAIL: libreoffice returned {result.returncode}")
            print(f"  stderr: {result.stderr}")
            return None

        # LibreOffice names its output after the input stem; the published
        # filename comes from GENERATED_PAIRS and need not match.
        html_basename = filename.replace('.docx', '.html')
        out_basename = out_name or html_basename
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

        out_path = DEST_DIR / out_basename
        out_path.write_bytes(final.encode('utf-8'))
        print(f"  OK -> {out_path.name} ({len(final):,} bytes)")
        return out_path


def main():
    soffice = find_soffice()
    if not soffice:
        print(soffice_not_found_message())
        sys.exit(1)
    print(f"LibreOffice: {soffice}")

    if not SRC_DIR.exists():
        print(f"ERROR: source folder not found: {SRC_DIR}")
        sys.exit(1)
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    args = list(sys.argv[1:])
    add_new_pair = '--add-new-pair' in args
    if add_new_pair:
        args.remove('--add-new-pair')

    if args:
        # single-file mode
        name = args[0]
        if name not in GENERATED_PAIRS and not add_new_pair:
            print(f"\nREFUSED: {name} is not a generated pair.")
            print("\nGENERATED_PAIRS currently defines:")
            for src, dest in sorted(GENERATED_PAIRS.items()):
                print(f"    {src}  ->  {dest}")
            print(f"\n{name} has no HTML page by design - it is download-only, or new.")
            print("Publishing one would put an unintended page in dist/docs/.")
            print("\nIf it genuinely needs a page, re-run with --add-new-pair:")
            print(f"    python3 convert-docx-to-html.py {name} --add-new-pair")
            sys.exit(1)
        targets = [name]
    else:
        targets = sorted(GENERATED_PAIRS)
        skipped = sorted(f.name for f in SRC_DIR.iterdir()
                         if f.suffix.lower() == '.docx' and f.name not in GENERATED_PAIRS)
        for s in skipped:
            print(f"SKIP {s} - not in GENERATED_PAIRS, so it has no HTML page by design.")

    if not targets:
        print("No .docx files to convert.")
        return

    results = []
    for f in targets:
        r = convert_one(f, soffice, GENERATED_PAIRS.get(f))
        if r:
            results.append(r)
        if add_new_pair and f not in GENERATED_PAIRS and r:
            print(f"\n  REMINDER: {f} is not in GENERATED_PAIRS.")
            print(f"            Add \"{f}\": \"{r.name}\" to that constant, or a bare")
            print("            run will never refresh this page and it will go stale.")

    print(f"\n=== Summary ===")
    print(f"Converted: {len(results)}/{len(targets)}")
    print("\nNext step: sync source to dist if the app was edited too:")
    print('  cp "STA-Training-Hub.html" "dist/index.html"')
    print("\nThen redeploy (git push, or drag dist/ to Cloudflare Pages).")


if __name__ == "__main__":
    main()
