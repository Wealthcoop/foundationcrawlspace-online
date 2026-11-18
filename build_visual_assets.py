#!/usr/bin/env python3
"""
Builds high-resolution JPEG data chart visuals (1200x700), injects 32-field EXIF GPS + XMP + IPTC
super-metadata via geo_asset_pipeline, creates the Companion Geo-Authority PDF via reportlab,
and archives all assets to Archive.org.
"""

import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PARENT_DIR))

from geo_asset_pipeline.metadata_injector import inject_image_metadata, verify_image_metadata
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from superstack_engine.archive_uploader import upload_file_to_archive_org

DOMAIN = "https://foundationcrawlspace.online"
PDF_NAME = "california-foundation-crawlspace-drainage-benchmarks-2026.pdf"
PDF_URL = f"{DOMAIN}/assets/{PDF_NAME}"
PDF_PATH = ASSETS_DIR / PDF_NAME

CHART1_NAME = "sacramento-foundation-repair-cost-cslb-benchmarks.jpg"
CHART2_NAME = "greater-sacramento-contractor-coverage-tiers.jpg"

DIR_BUSINESS = {
    "name": "Foundation & Crawlspace Directory",
    "legal_name": "Gold Standard Assets LLC",
    "website": DOMAIN,
    "street_address": "705 Gold Lake Dr Ste 250",
    "city": "Folsom",
    "state": "CA",
    "country": "US",
    "phone": "+19169941999",
    "display_phone": "(916) 994-1999",
    "email": "goldstandardaiagency@gmail.com",
    "cid": "7895656689241912038",
    "cid_url": "https://maps.google.com/?cid=7895656689241912038",
}


def load_font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_cost_cslb_chart(tmp_path: Path):
    w, h = 1200, 700
    img = Image.new("RGB", (w, h), (11, 37, 69))
    d = ImageDraw.Draw(img)

    # Top accent band & inner panel
    d.rectangle([0, 0, w, 10], fill=(217, 119, 6))
    d.rounded_rectangle([40, 36, w - 40, h - 36], radius=16, fill=(15, 48, 88), outline=(56, 189, 248), width=2)

    f_tag = load_font(18, bold=True)
    f_title = load_font(34, bold=True)
    f_sub = load_font(20, bold=False)
    f_lbl = load_font(21, bold=True)
    f_val = load_font(20, bold=True)
    f_note = load_font(16, bold=False)

    d.text((75, 58), "CALIFORNIA GREATER SACRAMENTO HOMEOWNER & LICENSING BENCHMARKS (2026)", font=f_tag, fill=(251, 191, 36))
    d.text((75, 92), "Foundation Repair, Crawlspace & French Drain Cost vs. CSLB Bonds", font=f_title, fill=(255, 255, 255))
    d.text((75, 138), "Regional cost baselines compared against mandatory California CSLB contractor bond requirements", font=f_sub, fill=(203, 213, 225))

    bars = [
        ("French Drains & Vapor Liners", "$2,500 - $6,000", 0.24, (56, 189, 248), "CA Dept. of Water Resources runoff guidelines"),
        ("20-Mil Crawlspace Encapsulation", "$4,500 - $12,500", 0.50, (34, 197, 94), "Moisture barrier + rim joist seal + dehumidifier"),
        ("Structural Push Piers / Underpinning", "$6,000 - $25,000+", 0.92, (245, 158, 11), "CA Geological Survey expansive clay stabilization"),
        ("Mandatory CA Contractor Bond", "$25,000 Bond Required", 0.92, (168, 85, 247), "CSLB B&P Code 7071.6 ($100k LLC extra worker bond)"),
    ]

    y = 205
    bar_x = 430
    bar_max_w = 660
    for label, val_txt, pct, col, sub in bars:
        d.text((75, y), label, font=f_lbl, fill=(255, 255, 255))
        d.text((75, y + 28), sub, font=f_note, fill=(148, 163, 184))
        d.rounded_rectangle([bar_x, y + 4, bar_x + bar_max_w, y + 46], radius=8, fill=(8, 28, 54))
        bw = int(bar_max_w * pct)
        d.rounded_rectangle([bar_x, y + 4, bar_x + bw, y + 46], radius=8, fill=col)
        d.text((bar_x + 16, y + 13), val_txt, font=f_val, fill=(255, 255, 255))
        y += 98

    d.line([(75, h - 98), (w - 75, h - 98)], fill=(51, 85, 128), width=2)
    d.text((75, h - 80), "Sources: California CSLB (cslb.ca.gov, B&P Code 7071.6) | CA Geological Survey (conservation.ca.gov/cgs) | CA Water Resources (water.ca.gov)", font=f_note, fill=(203, 213, 225))
    d.text((75, h - 55), "Compiled by Foundation & Crawlspace Directory (foundationcrawlspace.online) | Verified Greater Sacramento Index", font=f_note, fill=(251, 191, 36))
    img.save(tmp_path, "JPEG", quality=95)


def draw_city_coverage_chart(tmp_path: Path, contractors: list):
    counts = {}
    for c in contractors:
        counts[c["city"]] = counts.get(c["city"], 0) + 1
    top_cities = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:11]

    w, h = 1200, 700
    img = Image.new("RGB", (w, h), (11, 37, 69))
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, w, 10], fill=(16, 185, 129))
    d.rounded_rectangle([40, 36, w - 40, h - 36], radius=16, fill=(15, 48, 88), outline=(251, 191, 36), width=2)

    f_tag = load_font(18, bold=True)
    f_title = load_font(33, bold=True)
    f_sub = load_font(19, bold=False)
    f_lbl = load_font(18, bold=True)
    f_note = load_font(16, bold=False)

    total_c = len(contractors)
    total_rev = sum(c.get("reviews", 0) for c in contractors)
    d.text((75, 56), f"REGIONAL CONTRACTOR INDEX: {total_c} SPECIALISTS | {total_rev:,} VERIFIED REVIEWS", font=f_tag, fill=(52, 211, 153))
    d.text((75, 88), "Greater Sacramento, Placer & El Dorado City Coverage Breakdown", font=f_title, fill=(255, 255, 255))
    d.text((75, 132), "Listed foundation repair, crawlspace encapsulation, and French drain contractors by municipality", font=f_sub, fill=(203, 213, 225))

    max_cnt = max(v for _, v in top_cities) if top_cities else 1
    y = 185
    row_h = 37
    bar_x = 310
    bar_max_w = 720

    for city, cnt in top_cities:
        d.text((75, y + 6), f"{city}, CA", font=f_lbl, fill=(255, 255, 255))
        d.rounded_rectangle([bar_x, y + 4, bar_x + bar_max_w, y + 30], radius=6, fill=(8, 28, 54))
        bw = max(45, int((cnt / max_cnt) * bar_max_w))
        d.rounded_rectangle([bar_x, y + 4, bar_x + bw, y + 30], radius=6, fill=(14, 165, 233))
        d.text((bar_x + bw + 14, y + 5), f"{cnt} pros", font=f_lbl, fill=(251, 191, 36))
        y += row_h

    d.line([(75, h - 98), (w - 75, h - 98)], fill=(51, 85, 128), width=2)
    d.text((75, h - 80), "Sources: US Census Bureau QuickFacts (census.gov) | California CSLB Public Registry (cslb.ca.gov) | Google Maps Regional Index", font=f_note, fill=(203, 213, 225))
    d.text((75, h - 55), "Published at https://foundationcrawlspace.online/directory/ | Companion Data PDF Available", font=f_note, fill=(52, 211, 153))
    img.save(tmp_path, "JPEG", quality=95)


def build_companion_pdf(chart1: Path, chart2: Path, contractors: list):
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="2026 Greater Sacramento Foundation, Crawlspace & Drainage Benchmarks",
        author="Molly Perkins - Foundation & Crawlspace Directory",
        subject="California CSLB Licensing, Clay Soil Settlement Costs & Regional Contractor Index",
        keywords="Sacramento foundation repair cost, crawlspace encapsulation California, CSLB bond, French drains",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#0B2545"), spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#0E4A67"), spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14, textColor=colors.HexColor("#1F3A44"), spaceAfter=8)

    story = [
        Paragraph("<b>FOUNDATION &amp; CRAWLSPACE DIRECTORY | REGIONAL AUTHORITY REPORT</b>", ParagraphStyle("Tag", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#B45309"))),
        Paragraph("2026 Greater Sacramento Foundation Repair, Crawlspace &amp; Drainage Benchmarks", h1),
        Paragraph(
            f"Prepared by Molly Perkins for Foundation &amp; Crawlspace Directory (https://foundationcrawlspace.online). "
            f"Covers {len(contractors)} California specialists across 11 cities in Sacramento, Placer, and El Dorado counties.",
            body,
        ),
        Spacer(1, 6),
        RLImage(str(chart1), width=7.1 * inch, height=4.14 * inch),
        Spacer(1, 10),
        Paragraph("Verified Cost Ranges &amp; California Statutory Licensing Rules", h2),
    ]

    table_data = [
        ["Category / Requirement", "Observed Regional Range", "Credible Authority Source"],
        ["French Drains & Vapor Liners", "$2,500 to $6,000", "CA Dept. of Water Resources (water.ca.gov)"],
        ["20-Mil Crawlspace Encapsulation", "$4,500 to $12,500", "Homeowner regional estimate index"],
        ["Structural Underpinning Piers", "$6,000 to $25,000+", "CA Geological Survey (conservation.ca.gov/cgs)"],
        ["Mandatory CA License Bond", "$25,000 ($100k LLC extra)", "California CSLB (cslb.ca.gov, B&P 7071.6)"],
    ]
    tbl = Table(table_data, colWidths=[2.2 * inch, 2.1 * inch, 2.8 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B2545")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))
    story.append(RLImage(str(chart2), width=7.1 * inch, height=4.14 * inch))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Direct City Profiles &amp; Claim Portal: https://foundationcrawlspace.online/directory/ | "
        "Contractor Verification Desk: (916) 994-1999 | Publisher: Gold Standard Assets LLC, Folsom, CA 95630.",
        body,
    ))
    doc.build(story)


def main():
    contractors = json.loads((BASE_DIR / "contractors_data.json").read_text(encoding="utf-8"))
    tmp1 = ASSETS_DIR / "_tmp_chart1.jpg"
    tmp2 = ASSETS_DIR / "_tmp_chart2.jpg"
    out1 = ASSETS_DIR / CHART1_NAME
    out2 = ASSETS_DIR / CHART2_NAME

    draw_cost_cslb_chart(tmp1)
    draw_city_coverage_chart(tmp2, contractors)

    res1 = inject_image_metadata(
        str(tmp1),
        str(out1),
        service="Foundation Repair, Crawlspace Encapsulation & CSLB Bond Benchmarks",
        city_name="Folsom",
        heading="Greater Sacramento Foundation Repair, Crawlspace & CSLB Bond Benchmarks (2026)",
        keywords=[
            "Sacramento foundation repair cost",
            "crawlspace encapsulation California",
            "California CSLB license bond",
            "French drain waterproofing Sacramento",
            "Foundation & Crawlspace Directory",
        ],
        business=DIR_BUSINESS,
        companion_pdf_url=PDF_URL,
        preserve_dimensions=True,
    )
    res2 = inject_image_metadata(
        str(tmp2),
        str(out2),
        service="Greater Sacramento Foundation & Drainage Contractor Directory Index",
        city_name="Sacramento",
        heading="Greater Sacramento, Placer & El Dorado County Contractor Coverage (11 Cities, 91 Specialists)",
        keywords=[
            "Sacramento foundation contractors",
            "Folsom crawlspace repair",
            "Roseville French drain contractors",
            "Placer County foundation leveling",
            "Foundation & Crawlspace Directory",
        ],
        business=DIR_BUSINESS,
        companion_pdf_url=PDF_URL,
        preserve_dimensions=True,
    )
    tmp1.unlink(missing_ok=True)
    tmp2.unlink(missing_ok=True)

    print("[OK] Chart 1 injected:", out1.name, res1["dimensions"], "| GPS:", res1["coordinates"])
    print("[OK] Chart 2 injected:", out2.name, res2["dimensions"], "| GPS:", res2["coordinates"])
    print("[OK] Verify Chart 1 metadata:", verify_image_metadata(str(out1)))
    print("[OK] Verify Chart 2 metadata:", verify_image_metadata(str(out2)))

    build_companion_pdf(out1, out2, contractors)
    print(f"[OK] Companion PDF built: {PDF_PATH} ({PDF_PATH.stat().st_size:,} bytes)")

    ident = "sacramento-foundation-crawlspace-benchmarks-2026"
    uploaded = []
    for fp, title, mediatype in [
        (PDF_PATH, "2026 Greater Sacramento Foundation, Crawlspace & Drainage Benchmarks (PDF)", "texts"),
        (out1, "Sacramento Foundation Repair Cost & CSLB Bond Benchmarks Chart", "image"),
        (out2, "Greater Sacramento 11-City Foundation Contractor Coverage Chart", "image"),
    ]:
        try:
            r = upload_file_to_archive_org(
                file_path=str(fp),
                identifier=ident,
                title=title,
                description="Verified Greater Sacramento, Placer, and El Dorado foundation repair cost ranges, California CSLB licensing bonds, and regional contractor benchmarks published by foundationcrawlspace.online.",
                creator="Molly Perkins - Foundation & Crawlspace Directory",
                mediatype=mediatype,
                subject="foundation repair; crawlspace encapsulation; Sacramento; California CSLB",
                coverage="Sacramento, Placer County, El Dorado County, California",
            )
            uploaded.append(r)
            print("[OK] Archive.org uploaded:", r["file_url"])
        except Exception as e:
            print("[WARN] Archive.org upload error for", fp.name, ":", e)

    manifest = {"archive_item": f"https://archive.org/details/{ident}", "files": uploaded}
    (ASSETS_DIR / "archive_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
