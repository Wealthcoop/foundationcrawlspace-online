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


def _fit_font(d: ImageDraw.ImageDraw, text: str, start_size: int, max_width: int, bold: bool = True):
    size = start_size
    while size >= 13:
        font = load_font(size, bold=bold)
        bbox = d.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font
        size -= 1
    return load_font(13, bold=bold)


def _assert_fits(d: ImageDraw.ImageDraw, x: int, text: str, font, max_right: int, label: str):
    bbox = d.textbbox((x, 0), text, font=font)
    if bbox[2] > max_right:
        raise ValueError(f"Chart text overflow [{label}]: '{text}' reaches {bbox[2]} > {max_right}")


def draw_cost_cslb_chart(tmp_path: Path):
    w, h = 1200, 700
    img = Image.new("RGB", (w, h), (11, 37, 69))
    d = ImageDraw.Draw(img)

    # Top accent band & inner panel
    d.rectangle([0, 0, w, 10], fill=(217, 119, 6))
    panel_l, panel_t, panel_r, panel_b = 36, 32, w - 36, h - 32
    pad_l = 68
    pad_r = panel_r - 32
    max_full_w = pad_r - pad_l
    d.rounded_rectangle([panel_l, panel_t, panel_r, panel_b], radius=16, fill=(15, 48, 88), outline=(56, 189, 248), width=2)

    tag_txt = "GREATER SACRAMENTO HOMEOWNER & LICENSING BENCHMARKS (2026)"
    title_txt = "2026 Foundation, Crawlspace & French Drain Cost vs. CSLB Bonds"
    sub_txt = "Regional residential cost baselines compared against mandatory California CSLB contractor bonds"

    f_tag = _fit_font(d, tag_txt, 17, max_full_w, bold=True)
    f_title = _fit_font(d, title_txt, 31, max_full_w, bold=True)
    f_sub = _fit_font(d, sub_txt, 19, max_full_w, bold=False)
    f_lbl = load_font(20, bold=True)
    f_val = load_font(19, bold=True)
    f_note = load_font(15, bold=False)

    d.text((pad_l, 56), tag_txt, font=f_tag, fill=(251, 191, 36))
    d.text((pad_l, 88), title_txt, font=f_title, fill=(255, 255, 255))
    d.text((pad_l, 132), sub_txt, font=f_sub, fill=(203, 213, 225))
    _assert_fits(d, pad_l, title_txt, f_title, pad_r, "Chart1 Title")

    # Left column: x=68..520 (452px safe width); Right bar track: x=540..1128 (588px)
    bar_x = 540
    bar_max_w = pad_r - bar_x
    lbl_max_w = bar_x - pad_l - 22

    bars = [
        ("French Drains & Vapor Liners", "$2,500 - $6,000", 0.28, (56, 189, 248), (11, 37, 69), "CA Dept. of Water Resources runoff guidelines"),
        ("20-Mil Crawlspace Encapsulation", "$4,500 - $12,500", 0.50, (34, 197, 94), (11, 37, 69), "Moisture barrier + rim joist seal + dehumidifier"),
        ("Structural Push Piers / Underpinning", "$6,000 - $25,000+", 0.90, (245, 158, 11), (11, 37, 69), "CA Geological Survey expansive clay stabilization"),
        ("Mandatory CA Contractor Bond", "$25,000 Bond Required", 0.90, (168, 85, 247), (255, 255, 255), "CSLB B&P Code 7071.6 ($100k LLC extra bond)"),
    ]

    y = 198
    for label, val_txt, pct, col, val_col, sub in bars:
        lbl_font = _fit_font(d, label, 20, lbl_max_w, bold=True)
        sub_font = _fit_font(d, sub, 15, lbl_max_w, bold=False)
        _assert_fits(d, pad_l, label, lbl_font, bar_x - 16, f"Bar Label {label}")
        _assert_fits(d, pad_l, sub, sub_font, bar_x - 16, f"Bar Sub {label}")

        d.text((pad_l, y), label, font=lbl_font, fill=(255, 255, 255))
        d.text((pad_l, y + 29), sub, font=sub_font, fill=(148, 163, 184))
        d.rounded_rectangle([bar_x, y + 4, bar_x + bar_max_w, y + 48], radius=8, fill=(8, 28, 54))
        bw = max(180, int(bar_max_w * pct))
        d.rounded_rectangle([bar_x, y + 4, bar_x + bw, y + 48], radius=8, fill=col)
        v_font = _fit_font(d, val_txt, 19, bw - 24, bold=True)
        d.text((bar_x + 14, y + 14), val_txt, font=v_font, fill=val_col)
        y += 98

    d.line([(pad_l, h - 98), (pad_r, h - 98)], fill=(51, 85, 128), width=2)
    src1 = "Sources: California CSLB (cslb.ca.gov, B&P Code 7071.6) | CA Geological Survey (conservation.ca.gov/cgs) | CA Water Resources (water.ca.gov)"
    src2 = "Compiled by Foundation & Crawlspace Directory (foundationcrawlspace.online) | Verified Greater Sacramento Index"
    f_src1 = _fit_font(d, src1, 15, max_full_w, bold=False)
    f_src2 = _fit_font(d, src2, 15, max_full_w, bold=False)
    d.text((pad_l, h - 80), src1, font=f_src1, fill=(203, 213, 225))
    d.text((pad_l, h - 55), src2, font=f_src2, fill=(251, 191, 36))
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
    panel_l, panel_t, panel_r, panel_b = 36, 32, w - 36, h - 32
    pad_l = 68
    pad_r = panel_r - 32
    max_full_w = pad_r - pad_l
    d.rounded_rectangle([panel_l, panel_t, panel_r, panel_b], radius=16, fill=(15, 48, 88), outline=(251, 191, 36), width=2)

    total_c = len(contractors)
    total_rev = sum(c.get("reviews", 0) for c in contractors)
    tag_txt = f"REGIONAL CONTRACTOR INDEX: {total_c} SPECIALISTS | {total_rev:,} VERIFIED REVIEWS"
    title_txt = "Greater Sacramento, Placer & El Dorado City Coverage Breakdown"
    sub_txt = "Listed foundation repair, house leveling, crawlspace encapsulation & French drain pros by city"

    f_tag = _fit_font(d, tag_txt, 17, max_full_w, bold=True)
    f_title = _fit_font(d, title_txt, 31, max_full_w, bold=True)
    f_sub = _fit_font(d, sub_txt, 18, max_full_w, bold=False)
    f_lbl = load_font(18, bold=True)

    d.text((pad_l, 56), tag_txt, font=f_tag, fill=(52, 211, 153))
    d.text((pad_l, 88), title_txt, font=f_title, fill=(255, 255, 255))
    d.text((pad_l, 132), sub_txt, font=f_sub, fill=(203, 213, 225))

    max_cnt = max(v for _, v in top_cities) if top_cities else 1
    y = 182
    row_h = 37
    bar_x = 300
    bar_max_w = pad_r - bar_x - 90

    for city, cnt in top_cities:
        city_lbl = f"{city}, CA"
        c_font = _fit_font(d, city_lbl, 18, bar_x - pad_l - 16, bold=True)
        d.text((pad_l, y + 6), city_lbl, font=c_font, fill=(255, 255, 255))
        d.rounded_rectangle([bar_x, y + 4, bar_x + bar_max_w, y + 30], radius=6, fill=(8, 28, 54))
        bw = max(45, int((cnt / max_cnt) * bar_max_w))
        d.rounded_rectangle([bar_x, y + 4, bar_x + bw, y + 30], radius=6, fill=(14, 165, 233))
        d.text((bar_x + bw + 14, y + 5), f"{cnt} pros", font=f_lbl, fill=(251, 191, 36))
        y += row_h

    d.line([(pad_l, h - 98), (pad_r, h - 98)], fill=(51, 85, 128), width=2)
    src1 = "Sources: US Census Bureau QuickFacts (census.gov) | California CSLB Public Registry (cslb.ca.gov) | Google Maps Regional Index"
    src2 = "Published at https://foundationcrawlspace.online/directory/ | Companion Data PDF Available"
    f_src1 = _fit_font(d, src1, 15, max_full_w, bold=False)
    f_src2 = _fit_font(d, src2, 15, max_full_w, bold=False)
    d.text((pad_l, h - 80), src1, font=f_src1, fill=(203, 213, 225))
    d.text((pad_l, h - 55), src2, font=f_src2, fill=(52, 211, 153))
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
