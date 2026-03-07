# CV PDF Build

This repository contains my personal CV, built as a reproducible
one-page PDF from Markdown using Pandoc and a controlled HTML-to-PDF
pipeline. The goal is consistency, versioning, and CI-based builds,
treating the CV as a technical artifact rather than a static document.

The layout and content are intentionally kept minimal and editorial,
focused on clarity and senior engineering roles.

---

## Structure

- `sections/left.md` – photo, name, bio, contact, QR  
- `sections/middle.md` – work experience, education, events, languages  
- `sections/right.md` – skills and last-updated placeholder  
- `styles/cv.css` – layout and typography  
- `assets/` – images (profile photo, QR code, etc.)  
- `manifest.yaml` – manual version used in the PDF file name  
- `scripts/build_cv.py` – build pipeline (Markdown → HTML → PDF)

---

## Build

### Requirements
- Pandoc
- Python 3.11+

### Linux (used by GitHub Actions)
```bash
python scripts/build_cv.py
