# CV PDF Build

This repo builds a one-page PDF CV from Markdown using Pandoc and a PDF renderer.

## Structure
- `sections/left.md` - photo, name, bio, contact, QR
- `sections/middle.md` - work experience, education, events, languages
- `sections/right.md` - skills and last updated placeholder
- `styles/cv.css` - layout and typography
- `assets/` - images (profile, QR)
- `manifest.yaml` - manual version used in the PDF file name
- `scripts/build_cv.py` - build pipeline

## Build
Requirements:
- Pandoc
- Python 3.11+

Linux (GitHub Actions uses this path):
```bash
python scripts/build_cv.py
```

Windows:
```powershell
python scripts/build_cv.py
```

Notes:
- On Windows, the script prefers WeasyPrint if available (and GTK is configured).
  If WeasyPrint fails, it falls back to Edge/Chrome, then Playwright if installed.
- To use WeasyPrint on Windows, set `GTK_PATH` to your GTK root and install
  WeasyPrint (`pip install weasyprint`).

## Output
The PDF is created in `build/` with this name:
`Rafael_Rodriguez_Senior_Software_Engineer_<version>.pdf`

The version comes from `manifest.yaml`:
```yaml
version: "2025.10.04"
```

## Updating content
- Edit Markdown in `sections/`.
- Update styles in `styles/cv.css`.
- Replace images in `assets/`.
- Update `manifest.yaml` when you want a new output filename.

The "Last updated" date is set dynamically at build time.

## GitHub Actions
Workflow: `.github/workflows/build-cv.yml`
- Builds on push to `main` and on manual run.
- Uploads the PDF as an artifact.
- If a tag starts with `v`, it creates a GitHub Release with the PDF attached.
