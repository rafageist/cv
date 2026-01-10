from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
SECTIONS_DIR = ROOT / "sections"
BUILD_DIR = ROOT / "build"
ASSETS_DIR = ROOT / "assets"
STYLES_DIR = ROOT / "styles"


def read_section(filename: str) -> str:
    path = SECTIONS_DIR / filename
    return path.read_text(encoding="utf-8").strip()


def read_manifest_version() -> str:
    manifest_path = ROOT / "manifest.yaml"
    if not manifest_path.is_file():
        print(
            "Missing manifest.yaml. Add a version field, e.g. version: \"2025.10.04\"",
            file=sys.stderr,
        )
        raise SystemExit(1)

    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("version:"):
            value = line.split(":", 1)[1].strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            if value:
                return value
    print("manifest.yaml is missing a valid version field.", file=sys.stderr)
    raise SystemExit(1)


def sanitize_version(version: str) -> str:
    return "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in version)


def ensure_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        print(f"Missing tool: {name}. Install it and try again.", file=sys.stderr)
        raise SystemExit(1)
    return path


def find_browser() -> Optional[Path]:
    candidates = [
        os.environ.get("EDGE_PATH"),
        os.environ.get("CHROME_PATH"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)

    for name in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return Path(found)

    return None


def configure_gtk() -> None:
    if not sys.platform.startswith("win"):
        return

    gtk_root = os.environ.get("GTK_PATH")
    if gtk_root:
        gtk_path = Path(gtk_root)
    else:
        gtk_path = Path(r"D:\apps\gtk4")
        if not gtk_path.exists():
            return

    gtk_bin = gtk_path / "bin"
    if not gtk_bin.is_dir():
        return

    original_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{gtk_bin}{os.pathsep}{original_path}"
    os.environ["GI_TYPELIB_PATH"] = str(gtk_path / "lib" / "girepository-1.0")
    os.environ["XDG_DATA_DIRS"] = str(gtk_path / "share")

    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(gtk_bin))


def can_use_weasyprint() -> bool:
    return shutil.which("weasyprint") is not None


def render_pdf_with_weasyprint(html_path: Path, pdf_path: Path) -> None:
    configure_gtk()
    ensure_tool("weasyprint")
    weasy_cmd = ["weasyprint", str(html_path), str(pdf_path)]
    subprocess.run(weasy_cmd, check=True)


def render_pdf_with_playwright(html_path: Path, pdf_path: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        print(
            "Playwright is not installed. Run: pip install playwright",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    html_uri = html_path.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_uri, wait_until="load")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            display_header_footer=False,
        )
        browser.close()


def run_chromium_print(
    browser: Path, html_path: Path, pdf_path: Path, headless_arg: str
) -> None:
    html_uri = html_path.resolve().as_uri()
    cmd = [
        str(browser),
        headless_arg,
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--print-to-pdf-no-header",
        f"--print-to-pdf={pdf_path}",
        html_uri,
    ]
    subprocess.run(cmd, check=True)


def make_temp_pdf_path(pdf_path: Path) -> Path:
    handle, name = tempfile.mkstemp(
        prefix=f"{pdf_path.stem}_", suffix=pdf_path.suffix, dir=str(pdf_path.parent)
    )
    os.close(handle)
    return Path(name)


def finalize_pdf(temp_pdf: Path, pdf_path: Path) -> None:
    try:
        temp_pdf.replace(pdf_path)
    except OSError:
        print(
            f"PDF generated at {temp_pdf} but could not overwrite {pdf_path}. "
            "Close the PDF and rerun to replace it.",
            file=sys.stderr,
        )
        raise SystemExit(1)


def render_pdf_with_chromium(html_path: Path, pdf_path: Path) -> None:
    browser = find_browser()
    if browser is None:
        print(
            "Missing Edge/Chrome. Set EDGE_PATH or CHROME_PATH, or install a browser.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    temp_pdf = make_temp_pdf_path(pdf_path)

    try:
        run_chromium_print(browser, html_path, temp_pdf, "--headless=old")
        finalize_pdf(temp_pdf, pdf_path)
        return
    except subprocess.CalledProcessError:
        pass

    with tempfile.TemporaryDirectory() as temp_dir:
        html_uri = html_path.resolve().as_uri()
        cmd = [
            str(browser),
            "--headless",
            "--disable-gpu",
            "--allow-file-access-from-files",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--user-data-dir",
            temp_dir,
            "--print-to-pdf-no-header",
            f"--print-to-pdf={temp_pdf}",
            html_uri,
        ]
        try:
            subprocess.run(cmd, check=True)
            finalize_pdf(temp_pdf, pdf_path)
            return
        except subprocess.CalledProcessError:
            pass

    try:
        render_pdf_with_playwright(html_path, temp_pdf)
        finalize_pdf(temp_pdf, pdf_path)
        return
    except SystemExit:
        raise
    except Exception as exc:
        print(f"Playwright PDF failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def main() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    left = read_section("left.md")
    middle = read_section("middle.md")
    right = read_section("right.md")
    right = right.replace("{{LAST_UPDATED}}", date.today().isoformat())

    content = f"""::: {{.page}}
::: {{.cv}}
::: {{.cv-grid}}
::: {{.col-left}}
{left}
:::
::: {{.col-middle}}
{middle}
:::
::: {{.col-right}}
{right}
:::
:::
:::
:::
"""

    (BUILD_DIR / "cv.md").write_text(content, encoding="utf-8")

    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, BUILD_DIR / "assets", dirs_exist_ok=True)
    if STYLES_DIR.exists():
        shutil.copytree(STYLES_DIR, BUILD_DIR / "styles", dirs_exist_ok=True)

    ensure_tool("pandoc")

    pandoc_cmd = [
        "pandoc",
        str(BUILD_DIR / "cv.md"),
        "--from",
        "markdown+fenced_divs+bracketed_spans+raw_html",
        "--to",
        "html",
        "--standalone",
        "--css",
        "styles/cv.css",
        "--output",
        str(BUILD_DIR / "cv.html"),
    ]
    subprocess.run(pandoc_cmd, check=True)

    html_path = BUILD_DIR / "cv.html"
    version = sanitize_version(read_manifest_version())
    pdf_name = f"Rafael_Rodriguez_Senior_Software_Engineer_{version}.pdf"
    pdf_path = BUILD_DIR / pdf_name

    if sys.platform.startswith("win"):
        if can_use_weasyprint():
            try:
                render_pdf_with_weasyprint(html_path, pdf_path)
                print(f"Generated {pdf_path}")
                return
            except subprocess.CalledProcessError:
                pass
        render_pdf_with_chromium(html_path, pdf_path)
    else:
        render_pdf_with_weasyprint(html_path, pdf_path)

    print(f"Generated {pdf_path}")


if __name__ == "__main__":
    main()
