"""Archive manifest: one row per source PDF with archival metadata.

Metadata was read from each document's title pages. `status` separates
published plans from drafts / working files; `source` records whether the PDF
is a scan (needs OCR) or born-digital (already has a text layer).
"""
import csv
import re

import pymupdf

from .config import DATA, DOCUMENTS_CSV

# doc_id, relative path, year, title, status, first_content_page (1-based)
_DOCS = [
    ("1948_physical_dev_report", "1948/report-committee-physical-dev-1948.pdf", 1948,
     "Report of the Trustees' Committee on the Physical Development of the University", "final", 2),
    ("1961_dev_plan_taubin", "1961/UPJ9.4_57_21.pdf", 1961,
     "University of Pennsylvania Development Plan, March 1961 edition (Taubin desk copy with revisions)", "draft", 2),
    ("1961_dev_plan", "1961/UPLND-196103-University of Pennsylvania Development Plan.pdf", 1961,
     "University of Pennsylvania Development Plan (Report to the President, March 1961)", "final", 1),
    ("1963_dev_plan_taubin", "1963/UPJ9.4_57_31.pdf", 1963,
     "University of Pennsylvania Development Plan, 1963 (Taubin file copy)", "final", 2),
    ("1963_dev_plan", "1963/UPLND-196302-University of Pennsylvania Development Plan.pdf", 1963,
     "University of Pennsylvania Development Plan (for City Planning Commission, February 1963)", "final", 1),
    ("1966_campus_dev_plan_ua", "1966/UPJ9.4_103_32.pdf", 1966,
     "Campus Development Plan, 1966 (University Architect records copy)", "final", 2),
    ("1966_campus_dev_plan", "1966/UPLND-1966-Campus Development Plan.pdf", 1966,
     "University of Pennsylvania Campus Development Plan (third edition, April 1966)", "final", 1),
    ("1977_landscape_dev_plan", "1977/Landscape Development Plan February 1977.pdf", 1977,
     "Landscape Development Plan (Center for Environmental Design, February 1977)", "final", 1),
    ("1978_framework_campus_planning", "1978/UPLND-197812-A Framework For Campus Planning.pdf", 1978,
     "A Framework for Campus Planning (Davis & Brody Associates, 1978-79)", "draft", 1),
    ("1979_campus_dev_plan_interim", "1979/UPJ9.4_58_18.pdf", 1979,
     "University of Pennsylvania Development Plan, Interim Report (October 1979)", "draft", 2),
    ("1981_campus_dev_plan_reports", "1981-1982/UPJ9.4_103_33.pdf", 1982,
     "Campus Development Plan, 1981-82 Reports", "final", 2),
    ("1982_campus_dev_plan_reports", "1982-1983/UPJ9.4_58_20.pdf", 1983,
     "Campus Development Plan, 1982-83 Reports", "final", 2),
    ("1983_campus_dev_plan_reports", "1983-1984/UPJ9.4_58_21.pdf", 1984,
     "Campus Development Plan, 1983-84 Reports", "final", 1),
    ("1987_campus_master_plan_draft", "1987/UPJ9.4_59_02.pdf", 1987,
     "Campus Master Plan draft and correspondence (1987)", "draft", 2),
    ("1992_master_land_use_plan", "1992/UPLND-199210-Master Land Use Plan.pdf", 1992,
     "Master Land Use Plan, preliminary (Venturi, Scott Brown and Associates, October 1992)", "draft", 1),
    ("1998_campus_dev_plan_brief", "1998/UPJ9.4_104_07.pdf", 1998,
     "Campus Development Plan, Executive Brief 1998", "final", 2),
    ("1998_campus_dev_master_plan", "1998/UPLND-199804-1998 Campus Development Master Plan.pdf", 1998,
     "Campus Development Master Plan, Executive Brief (draft 04-27-98)", "draft", 1),
    ("2006_penn_connects", "2006/Penn Connects A Vision for the Future 2006.pdf", 2006,
     "Penn Connects: A Vision for the Future", "final", 1),
    ("2012_penn_connects_2", "2012/Penn Connects 2.0 2012.pdf", 2012,
     "Penn Connects 2.0", "final", 1),
]

# Second scans of a plan that is already in the archive. Measured on the prose
# blocks, 93-99% of each text is also in its twin. They stay in the corpus
# (the benchmark sampled them as separate scans) but are left out of the
# analysis so a year is not counted twice. The library (UPLND) copy is the one
# kept: the 1961 Taubin desk copy holds the plan twice, and the 1966 University
# Architect scan lost whole lines in the OCR benchmark.
DUPLICATE_OF = {
    "1961_dev_plan_taubin": "1961_dev_plan",
    "1963_dev_plan_taubin": "1963_dev_plan",
    "1966_campus_dev_plan_ua": "1966_campus_dev_plan",
}


def report_id(doc_id: str) -> str:
    """The unit of analysis. Penn Connects 3.0 was published as many small
    PDFs; together they are one report. Every other document is its own."""
    return "2018_penn_connects_3" if doc_id.startswith("2018_") else doc_id


FIELDS = ["doc_id", "path", "year", "title", "status", "source", "n_pages",
          "first_content_page"]


# Everything before 2000 is a scan (the 1948 report carries an old embedded OCR
# layer of unknown quality, so it is still treated as a scan). Penn Connects
# (2006 onward) is born-digital and keeps its own text layer.
def _source(year: int) -> str:
    return "scan" if year < 2000 else "born_digital"


def build() -> list[dict]:
    rows = []
    listed = set()
    for doc_id, rel, year, title, status, first in _DOCS:
        with pymupdf.open(DATA / rel) as doc:
            rows.append(dict(doc_id=doc_id, path=rel, year=year, title=title, status=status,
                             source=_source(year),
                             n_pages=len(doc), first_content_page=first))
        listed.add(rel)
    # Penn Connects 3.0 (2018) is published as many small born-digital PDFs.
    for pdf in sorted((DATA / "2018").glob("*.pdf")):
        with pymupdf.open(pdf) as doc:
            rows.append(dict(doc_id="2018_" + re.sub(r"(_\d)+$", "", pdf.stem).replace("-", "_"),
                             path=f"2018/{pdf.name}", year=2018,
                             title=f"Penn Connects 3.0: {pdf.stem}", status="final",
                             source="born_digital", n_pages=len(doc), first_content_page=1))
        listed.add(f"2018/{pdf.name}")
    missing = {str(p.relative_to(DATA)) for p in DATA.rglob("*.pdf")} - listed
    if missing:
        raise SystemExit(f"PDFs without metadata, add them to documents.py: {sorted(missing)}")
    DOCUMENTS_CSV.parent.mkdir(exist_ok=True)
    with open(DOCUMENTS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


def load() -> list[dict]:
    if not DOCUMENTS_CSV.exists():
        return build()
    with open(DOCUMENTS_CSV) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("year", "n_pages", "first_content_page"):
            r[k] = int(r[k])
        r["report"] = report_id(r["doc_id"])
        r["duplicate_of"] = DUPLICATE_OF.get(r["doc_id"], "")
    return rows


if __name__ == "__main__":
    rows = build()
    scans = [r for r in rows if r["source"] == "scan"]
    print(f"{len(rows)} documents ({len(scans)} scans, "
          f"{sum(r['n_pages'] for r in scans)} scanned pages) -> {DOCUMENTS_CSV}")
