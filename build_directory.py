#!/usr/bin/env python3
"""
Foundation, Crawlspace & Drainage Directory Generator (foundationcrawlspace.online)
Builds static HTML pages, JSON-LD schema, client-side search index, sitemap.xml, and robots.txt.
"""

import html
import json
import re
import shutil
import urllib.parse
from datetime import date
from pathlib import Path
from guides_content import FOUNDATION_REPAIR_GUIDE, HOUSE_LEVELING_GUIDE

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "contractors_data.json"
DOMAIN = "https://foundationcrawlspace.online"
SITE_NAME = "Foundation & Crawlspace Directory"
TRACKING_PHONE = "(916) 884-9689"
TRACKING_TEL = "+19168849689"
TODAY_STR = date.today().isoformat()

CITY_LOCAL_NOTES = {
    "Sacramento": {
        "zips": "95814, 95816, 95819, 95825, 95831",
        "context": "Sacramento Valley river-basin clay soils expand during winter rain and shrink in dry heat, driving raised-floor pier settling in Land Park/East Sac and slab edge movement across Natomas and Pocket.",
    },
    "Folsom": {
        "zips": "95630",
        "context": "Sloped granite-to-clay lots around Historic Folsom, Broadstone, and Empire Ranch frequently see hydrostatic pressure pushing water under crawlspaces and behind retaining walls.",
    },
    "Roseville": {
        "zips": "95661, 95678, 95747",
        "context": "Older slab homes near Cirby and Diamond Oaks and creek-adjacent lots in Roseville regularly need perimeter French drains and slab leveling piers as dry clay shifts.",
    },
    "El Dorado Hills": {
        "zips": "95762",
        "context": "Steep foothill grades in Serrano, Ridgeview, and Bass Lake direct winter runoff straight toward lower crawlspace stem walls unless intercepted with deep French drains and vapor barriers.",
    },
    "Placerville": {
        "zips": "95667",
        "context": "Older timber-frame piers, uneven hillside bedrock, and heavy winter rainfall around Placerville trigger musty crawlspace humidity, dry rot on floor joists, and sump pump failures.",
    },
    "Auburn": {
        "zips": "95602, 95603",
        "context": "Sierra foothill slopes and shaded crawlspaces across Auburn often trap moisture against subfloors, making encapsulation, dehumidifiers, and downhill drainage swales critical.",
    },
    "Citrus Heights": {
        "zips": "95610, 95621",
        "context": "Established 1960s to 1980s subdivisions in Citrus Heights sit on flat clay soil where aging cast-iron/corrugated yard drains collapse and leave standing water near perimeter footings.",
    },
    "Lincoln": {
        "zips": "95648",
        "context": "Expansive clay basins west of Highway 65 and rural acreage lots around Lincoln put seasonal lift and settlement stress on slabs, driveways, and detached shop foundations.",
    },
    "Rocklin": {
        "zips": "95677, 95765",
        "context": "Granite outcroppings mixed with pockets of expansive soil in Stanford Ranch and Whitney Ranch create uneven settling spots and trapped yard drainage after heavy storms.",
    },
    "Granite Bay": {
        "zips": "95746",
        "context": "Larger semi-rural lots and rolling terrain near Folsom Lake often suffer subsurface spring seepage under raised crawlspaces that requires sump basins and closed vapor barriers.",
    },
    "Elk Grove": {
        "zips": "95624, 95757, 95758",
        "context": "Flat Delta clay around Laguna, Sheldon, and Old Town Elk Grove slows surface water percolation, causing backyard flooding against slab edges and exterior stucco weep screeds.",
    },
}

SERVICE_SILOS = [
    FOUNDATION_REPAIR_GUIDE,
    HOUSE_LEVELING_GUIDE,
    {
        "slug": "crawlspace-encapsulation",
        "name": "Crawlspace Encapsulation & Vapor Barriers",
        "match_token": "Crawlspace Encapsulation",
        "title": "Best Crawlspace Encapsulation & Waterproofing Sacramento",
        "h1": "Best Crawlspace Encapsulation &amp; Vapor Barrier Contractors in Greater Sacramento",
        "desc": "Find local Sacramento, Folsom, Auburn, and Placerville crawlspace waterproofing specialists for vapor barriers, sump pumps, and wood-rot prevention.",
        "intro": "Standing water and damp soil under raised floors trigger mold odors, warped hardwood floors, and pest activity before showing up in home-sale inspections. Compare local pros installing heavy-mil vapor barriers, sealed sump basins, and perimeter drainage.",
        "faq_q": "What is the difference between a basic black plastic liner and full crawlspace encapsulation?",
        "faq_a": "A loose 6-mil plastic sheet still lets humid soil air circulate around vents and overlap seams, whereas full encapsulation seals seams with 12-to-20-mil reinforced liner, closes foundation vents, and pairs with drainage or a dehumidifier.",
    },
    {
        "slug": "drainage-french-drains",
        "name": "French Drains & Yard Waterproofing",
        "match_token": "Drainage",
        "title": "Best French Drain & Yard Drainage Contractors Sacramento",
        "h1": "Best French Drain &amp; Yard Drainage Contractors in Greater Sacramento",
        "desc": "Compare Greater Sacramento, El Dorado Hills, and Roseville French drain, catch basin, grading, and sump pump drainage specialists.",
        "intro": "Water pooling against your foundation slab or running down a hillside lot causes hydrostatic cracks and flooded crawlspaces every winter storm. Compare local drainage crews building perforated French drains, surface catch basins, swales, and sump discharge lines.",
        "faq_q": "How far should a French drain discharge away from a Sacramento foundation?",
        "faq_a": "Downspouts and perimeter French drains should discharge water at least 10 feet downhill from footings or safely to a street curb/storm drain with proper slope and cleanout ports so silt cannot clog the pipe.",
    },
]

COMMON_CSS = """
:root {
  --bg: #ffffff;
  --surface: #f5f7f9;
  --text: #27444f;
  --muted: #526973;
  --accent: #0b2545;
  --accent-mid: #0e4a67;
  --heading: #0b2545;
  --link: #0d5c63;
  --action: #f59e0b;
  --action-hover: #d97706;
  --action-text: #0b2545;
  --gold-soft: #fffbeb;
  --gold-border: #d97706;
  --radius: 10px;
  --btn-radius: 8px;
  --shadow: 0 2px 6px rgba(11,37,69,0.06), 0 1px 2px rgba(11,37,69,0.08);
  --font-head: Georgia, "Times New Roman", serif;
  --font-body: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
  font-size: 16px;
  line-height: 1.55;
}
h1, h2, h3, h4 {
  font-family: var(--font-head);
  color: var(--heading);
  margin: 0 0 0.5em;
  line-height: 1.22;
}
h1 { font-size: clamp(1.9rem, 3.6vw, 2.65rem); }
h2 { font-size: clamp(1.35rem, 2.4vw, 1.9rem); margin-top: 2rem; }
h3 { font-size: 1.15rem; }
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
.wrap { max-width: 1140px; margin: 0 auto; padding: 0 1.25rem; }

.site-header {
  background: var(--accent);
  color: #ffffff;
  border-bottom: 3px solid var(--action);
}
.site-header .wrap {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem 1.25rem;
  min-height: 70px;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
}
.logo {
  font-family: var(--font-head);
  font-size: 1.2rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.01em;
}
.logo em { font-style: normal; color: #fbbf24; }
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem 1.25rem;
  align-items: center;
}
.nav a { color: #e2e8f0; font-weight: 600; font-size: 0.94rem; }
.nav a:hover { color: #ffffff; text-decoration: none; }
.nav a.nav-cta {
  background: var(--action);
  color: var(--action-text);
  padding: 0.48rem 1rem;
  border-radius: var(--btn-radius);
  font-weight: 800;
}
.nav a.nav-cta:hover { background: var(--action-hover); }

.hero-band {
  background: linear-gradient(135deg, #0b2545 0%, #0e4a67 100%);
  color: #ffffff;
  padding: 3.1rem 0 4.2rem;
  text-align: center;
}
.hero-band h1 { color: #ffffff; margin-bottom: 0.45em; }
.hero-band h1 .hl { color: #fbbf24; }
.hero-band .lede {
  color: #dbeafe;
  font-size: 1.12rem;
  max-width: 64ch;
  margin: 0 auto 1.6rem;
}

.dir-search {
  display: flex;
  gap: 0.45rem;
  max-width: 700px;
  margin: 1.35rem auto 0;
  background: #ffffff;
  padding: 0.4rem;
  border-radius: 999px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.22);
}
.dir-search input {
  flex: 1;
  min-width: 0;
  border: 0;
  padding: 0.72rem 1.15rem;
  font: inherit;
  font-size: 0.98rem;
  border-radius: 999px;
  outline: none;
  color: var(--heading);
}
.dir-search button {
  background: var(--action);
  color: var(--action-text);
  border: 0;
  padding: 0.72rem 1.5rem;
  border-radius: 999px;
  font-weight: 800;
  cursor: pointer;
  font-size: 0.96rem;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
  gap: 1rem;
  background: #081c36;
  color: #ffffff;
  padding: 1.75rem 1.5rem;
  border-radius: var(--radius);
  margin: -2.4rem auto 2.25rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.16);
  max-width: 1020px;
  text-align: center;
}
.stat-cards dd {
  font-family: var(--font-head);
  font-size: 1.85rem;
  font-weight: 800;
  color: #fbbf24;
  margin: 0;
}
.stat-cards dt {
  font-size: 0.8rem;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.25rem;
}

.city-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
  list-style: none;
  padding: 0;
  margin: 1.25rem 0 2.5rem;
}
.city-cards a {
  display: block;
  background: var(--surface);
  border: 1px solid #d9e2ec;
  border-radius: var(--radius);
  padding: 1.1rem 1.2rem;
  box-shadow: var(--shadow);
}
.city-cards a:hover {
  text-decoration: none;
  border-color: var(--accent-mid);
  transform: translateY(-1px);
}
.city-cards strong { display: block; font-size: 1.08rem; color: var(--heading); }
.city-cards .count { display: block; margin-top: 0.25rem; font-size: 0.88rem; color: var(--muted); }

.biz-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 1.25rem;
  margin: 1.25rem 0 2.5rem;
}
.biz-card {
  background: #ffffff;
  border: 1px solid #d9e2ec;
  border-radius: var(--radius);
  padding: 1.25rem;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.biz-card.open-slot {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border: 2px dashed var(--gold-border);
}
.biz-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.83rem;
  color: var(--muted);
}
.badge {
  display: inline-block;
  padding: 0.16rem 0.55rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 800;
  text-transform: uppercase;
  background: #e2e8f0;
  color: #1e293b;
}
.badge.gold { background: #f59e0b; color: #0b2545; }
.biz-name { font-family: var(--font-head); font-size: 1.15rem; font-weight: 800; color: var(--heading); }
.biz-name a { color: var(--heading); }
.stars { font-size: 0.9rem; font-weight: 700; color: #b45309; }
.chips { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.25rem 0; }
.chip {
  font-size: 0.76rem;
  background: #edf2f7;
  color: #334e68;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-weight: 600;
}
.biz-foot {
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.phone-link { font-weight: 700; color: var(--heading); font-size: 0.95rem; }
.btn {
  display: inline-block;
  padding: 0.45rem 0.85rem;
  border-radius: var(--btn-radius);
  font-weight: 700;
  font-size: 0.84rem;
  text-align: center;
  cursor: pointer;
  border: 0;
}
.btn.primary { background: var(--accent); color: #ffffff; }
.btn.primary:hover { background: var(--accent-mid); text-decoration: none; }
.btn.action { background: var(--action); color: var(--action-text); }
.btn.action:hover { background: var(--action-hover); text-decoration: none; }
.btn.subtle { background: #e2e8f0; color: var(--heading); }
.btn.subtle:hover { background: #cbd5e1; text-decoration: none; }

.two-col {
  display: grid;
  grid-template-columns: 1.45fr 1fr;
  gap: 2rem;
  align-items: start;
  margin: 2rem 0 3.5rem;
}
.panel {
  background: var(--surface);
  border: 1px solid #d9e2ec;
  border-radius: var(--radius);
  padding: 1.4rem;
  box-shadow: var(--shadow);
}
.panel.quote-box {
  background: #f0f9ff;
  border: 2px solid #0284c7;
}
.panel.claim-box {
  background: var(--gold-soft);
  border: 2px solid var(--gold-border);
}
.lead-form { display: grid; gap: 0.85rem; }
.lead-form label { display: block; font-size: 0.85rem; font-weight: 700; margin-bottom: 0.25rem; color: var(--heading); }
.lead-form input, .lead-form select, .lead-form textarea {
  width: 100%;
  padding: 0.65rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: var(--btn-radius);
  font: inherit;
  font-size: 0.95rem;
  background: #ffffff;
  color: var(--heading);
}
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0.85rem; }
.form-status {
  display: none;
  padding: 0.9rem 1rem;
  border-radius: var(--btn-radius);
  background: #ecfdf5;
  border: 1px solid #10b981;
  color: #065f46;
  font-weight: 600;
}
.hp-trap { position: absolute; left: -9999px; opacity: 0; height: 0; width: 0; overflow: hidden; }

.breadcrumbs { font-size: 0.88rem; color: var(--muted); margin: 1.25rem 0 0.75rem; }
.breadcrumbs a { color: var(--muted); }
.info-table { width: 100%; border-collapse: collapse; margin: 1rem 0 1.5rem; }
.info-table th, .info-table td {
  padding: 0.7rem 0.5rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  vertical-align: top;
}
.info-table th { width: 32%; color: var(--muted); font-weight: 700; font-size: 0.92rem; }

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  background: var(--surface);
  padding: 1rem;
  border-radius: var(--radius);
  border: 1px solid #d9e2ec;
  margin: 1.5rem 0;
}
.filter-bar input, .filter-bar select {
  padding: 0.6rem 0.8rem;
  border: 1px solid #cbd5e1;
  border-radius: var(--btn-radius);
  font: inherit;
  font-size: 0.94rem;
  background: #ffffff;
}
.filter-bar input { flex: 1 1 240px; }

.site-footer {
  background: var(--accent);
  color: #cbd5e1;
  padding: 2.75rem 0 1.75rem;
  margin-top: 3.5rem;
}
.footer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 1.75rem;
}
.site-footer h4 { color: #fbbf24; font-size: 0.98rem; margin-bottom: 0.75rem; }
.site-footer ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.4rem; font-size: 0.9rem; }
.site-footer a { color: #e2e8f0; }
.footer-bottom {
  border-top: 1px solid rgba(255,255,255,0.14);
  margin-top: 2rem;
  padding-top: 1.25rem;
  font-size: 0.85rem;
  color: #94a3b8;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem;
}

.guide-article {
  background: #ffffff;
  border: 1px solid #d9e2ec;
  border-radius: var(--radius);
  padding: 1.65rem;
  box-shadow: var(--shadow);
  margin-bottom: 2rem;
}
.guide-article h2 { margin-top: 2rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.35rem; }
.guide-article h3 { margin-top: 1.35rem; color: #0e4a67; }
.guide-article p { margin: 0 0 1rem; color: #1f3a44; }
.guide-article a { font-weight: 600; text-decoration: underline; }

@media (max-width: 780px) {
  .two-col, .form-row-2 { grid-template-columns: 1fr; }
  .dir-search { flex-direction: column; border-radius: 14px; padding: 0.6rem; }
  .dir-search button { border-radius: 10px; }
}
"""

FORM_JS = """
<script>
(function() {
  var loadedAt = Date.now();
  document.querySelectorAll('form[data-lead-form]').forEach(function(form) {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      var btn = form.querySelector('button[type="submit"]');
      var statusEl = form.parentElement.querySelector('.form-status');
      var origText = btn ? btn.textContent : 'Submit';
      if (btn) { btn.disabled = true; btn.textContent = 'Sending...'; }

      var fd = new FormData(form);
      var payload = {
        leadType: form.getAttribute('data-lead-type') || 'quote',
        name: (fd.get('name') || '').toString().trim(),
        company: (fd.get('company') || '').toString().trim(),
        phone: (fd.get('phone') || '').toString().trim(),
        email: (fd.get('email') || '').toString().trim(),
        city: (fd.get('city') || '').toString().trim(),
        service: (fd.get('service') || '').toString().trim(),
        license: (fd.get('license') || '').toString().trim(),
        notes: (fd.get('notes') || '').toString().trim(),
        targetCompany: form.getAttribute('data-target-company') || '',
        website_url: (fd.get('website_url') || '').toString().trim(),
        pageUrl: window.location.pathname,
        loadedAt: loadedAt
      };

      try {
        var res = await fetch('/api/lead-capture', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          form.style.display = 'none';
          if (statusEl) statusEl.style.display = 'block';
          return;
        }
      } catch (err) {
        console.warn('Submit error:', err);
      }
      if (btn) { btn.disabled = false; btn.textContent = origText; }
      alert('Please call ' + '""" + TRACKING_PHONE + """' + ' directly or check your phone/email and try again.');
    });
  });
})();
</script>
"""


def esc(val: str) -> str:
    return html.escape(str(val or ""), quote=True)


def clean_tel(phone: str) -> str:
    return re.sub(r"[^0-9+]", "", phone or "")


def city_slug(city: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")


def canonical_tag(path: str) -> str:
    path = "/" + path.lstrip("/")
    if not path.endswith("/"):
        path += "/"
    if path == "//":
        path = "/"
    return f'<link rel="canonical" href="{DOMAIN}{path}" />'


def render_header() -> str:
    return f"""
<header class="site-header">
  <div class="wrap">
    <a class="logo" href="/">Foundation &amp; <em>Crawlspace</em> Directory</a>
    <nav class="nav" aria-label="Main Navigation">
      <a href="/directory/">Browse Contractors</a>
      <a href="/quote/">Request Quotes</a>
      <a href="/featured/">Get Featured</a>
      <a href="tel:{TRACKING_TEL}">{TRACKING_PHONE}</a>
      <a class="nav-cta" href="/claim/">Claim Listing</a>
    </nav>
  </div>
</header>
"""


def render_footer(cities: list) -> str:
    city_links = "".join(
        f'<li><a href="/directory/california/{city_slug(c)}/">{esc(c)} Contractors</a></li>'
        for c in cities[:8]
    )
    return f"""
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <h4>{SITE_NAME}</h4>
        <p style="font-size: 0.9rem; margin: 0 0 0.75rem;">
          Independent California contractor index covering foundation leveling, crawlspace encapsulation, vapor barriers, and yard drainage across Greater Sacramento, Placer, and El Dorado counties.
        </p>
        <p style="font-size: 0.9rem; margin: 0;">
          Dispatch &amp; Verification Line: <a href="tel:{TRACKING_TEL}"><strong>{TRACKING_PHONE}</strong></a>
        </p>
      </div>
      <div>
        <h4>Top Service Cities</h4>
        <ul>{city_links}</ul>
      </div>
      <div>
        <h4>Homeowners</h4>
        <ul>
          <li><a href="/directory/">Search All Contractors</a></li>
          <li><a href="/quote/">Request Local Quotes</a></li>
          <li><a href="/about/">About This Directory</a></li>
          <li><a href="/privacy-policy/">Privacy Policy</a></li>
        </ul>
      </div>
      <div>
        <h4>For Contractors</h4>
        <ul>
          <li><a href="/claim/">Claim Your Free Profile</a></li>
          <li><a href="/featured/">Featured City Slots ($49/mo)</a></li>
          <li><a href="/featured/#leads">Exclusive City Leads ($149/mo)</a></li>
          <li><a href="/services/foundation-repair/">Foundation Repair Guide</a></li>
          <li><a href="/services/house-leveling/">House Leveling Guide</a></li>
          <li><a href="/services/crawlspace-encapsulation/">Crawlspace Encapsulation</a></li>
          <li><a href="/services/drainage-french-drains/">French Drains &amp; Waterproofing</a></li>
          <li><a href="/contact/">Contact Directory Desk</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>Copyright &copy; {date.today().year} {SITE_NAME} (foundationcrawlspace.online). Public contractor data compiled from verified Google Business &amp; public filings.</span>
      <span><a href="/sitemap.xml">Sitemap</a> &middot; <a href="/llms.txt">llms.txt (AI 3/3)</a></span>
    </div>
  </div>
</footer>
{FORM_JS}
"""


def render_quote_form(default_city: str = "", default_service: str = "Foundation Repair", target_company: str = "", heading: str = "Request Local Estimates", lead_type: str = "quote") -> str:
    safe_city = esc(default_city)
    safe_target = esc(target_company)
    services = [
        "Foundation Repair & Leveling",
        "Crawlspace Encapsulation & Vapor Barrier",
        "French Drain & Yard Waterproofing",
        "Sump Pump & Standing Water Drainage",
        "Home Inspection / Escrow Repair Quote",
    ]
    options = "".join(
        f'<option value="{esc(s)}"{" selected" if default_service.lower() in s.lower() else ""}>{esc(s)}</option>'
        for s in services
    )
    return f"""
<div class="panel quote-box">
  <h3 style="margin-top:0;">{esc(heading)}</h3>
  <p style="font-size: 0.9rem; color: var(--muted); margin: 0 0 1rem;">
    Describe what is happening under your home or yard. We alert our dispatch desk right away or call <a href="tel:{TRACKING_TEL}"><strong>{TRACKING_PHONE}</strong></a>.
  </p>
  <form class="lead-form" data-lead-form="1" data-lead-type="{esc(lead_type)}" data-target-company="{safe_target}">
    <div class="hp-trap" aria-hidden="true">
      <label>Website</label>
      <input type="text" name="website_url" tabindex="-1" autocomplete="off" />
    </div>
    <div class="form-row-2">
      <div>
        <label>Your Name *</label>
        <input type="text" name="name" required placeholder="First &amp; Last Name" />
      </div>
      <div>
        <label>Phone Number *</label>
        <input type="tel" name="phone" required placeholder="(916) 555-0192" />
      </div>
    </div>
    <div class="form-row-2">
      <div>
        <label>City or ZIP *</label>
        <input type="text" name="city" required value="{safe_city}" placeholder="e.g. Folsom or 95630" />
      </div>
      <div>
        <label>Email (Optional)</label>
        <input type="email" name="email" placeholder="you@email.com" />
      </div>
    </div>
    <div>
      <label>Project / Problem *</label>
      <select name="service">{options}</select>
    </div>
    <div>
      <label>Brief Notes (Optional)</label>
      <textarea name="notes" rows="2" placeholder="Sticking doors, slab cracks, wet crawlspace, or drainage runoff..."></textarea>
    </div>
    <button type="submit" class="btn action" style="padding: 0.78rem 1rem; font-size: 0.98rem;">Request Estimate</button>
    <p style="font-size: 0.78rem; color: var(--muted); margin: 0;">Using this directory is free. Ask each contractor upfront whether your visit qualifies for a no-charge repair estimate or carries a diagnostic or escrow inspection fee.</p>
  </form>
  <div class="form-status">
    <strong>Request Received.</strong> Our Greater Sacramento dispatch desk just received your details and will text or call you from {TRACKING_PHONE} shortly.
  </div>
</div>
"""


def render_rating_line(c: dict) -> str:
    if c.get("rating") is not None:
        return f'<div class="stars">{c["rating"]:.1f}&#9733; ({c["reviews"]} Google reviews)</div>'
    return '<div style="font-size:0.86rem; color: var(--muted);">Public contractor record</div>'


def render_card(c: dict) -> str:
    cslug = city_slug(c["city"])
    prof_url = f'/company/california/{cslug}/{c["slug"]}/'
    chips = "".join(f'<span class="chip">{esc(s)}</span>' for s in c.get("services", [])[:4])
    tel = clean_tel(c.get("phone", ""))
    phone_html = f'<a class="phone-link" href="tel:{tel}">{esc(c["phone"])}</a>' if c.get("phone") else f'<a class="phone-link" href="tel:{TRACKING_TEL}">{TRACKING_PHONE}</a>'
    status_badge = '<span class="badge gold">Verified</span>' if c.get("claimed") else '<span class="badge">Unclaimed</span>'
    claim_btn = "" if c.get("claimed") else f'<a class="btn subtle" href="/claim/?company={urllib.parse.quote(c["name"])}&city={urllib.parse.quote(c["city"])}">Claim</a>'
    return f"""
<article class="biz-card">
  <div class="biz-top">
    <span>{esc(c["city"])}, CA</span>
    {status_badge}
  </div>
  <div class="biz-name"><a href="{prof_url}">{esc(c["name"])}</a></div>
  {render_rating_line(c)}
  <div style="font-size:0.86rem; color: var(--muted);">{esc(c.get("address", ""))}</div>
  <div class="chips">{chips}</div>
  <div class="biz-foot">
    {phone_html}
    <div style="display:flex; gap:0.4rem;">
      {claim_btn}
      <a class="btn primary" href="{prof_url}">View Profile</a>
    </div>
  </div>
</article>
"""


def page_shell(title: str, desc: str, canon_path: str, body_html: str, cities: list, schema_obj: dict = None) -> str:
    if schema_obj is None and canon_path != "/":
        label = canon_path.strip("/").replace("-", " ").title()
        schema_obj = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                {"@type": "ListItem", "position": 2, "name": label, "item": f"{DOMAIN}{canon_path}"},
            ],
        }
    schema_tag = ""
    if schema_obj:
        schema_tag = f'<script type="application/ld+json">{json.dumps(schema_obj, ensure_ascii=False)}</script>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}" />
  {canonical_tag(canon_path)}
  <link rel="alternate" type="text/plain" title="LLMs.txt" href="{DOMAIN}/llms.txt" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:url" content="{DOMAIN}{canon_path}" />
  <style>{COMMON_CSS}</style>
  {schema_tag}
</head>
<body>
{render_header()}
<main id="main-content">
{body_html}
</main>
{render_footer(cities)}
</body>
</html>
"""


def build_homepage(contractors: list, cities_dict: dict, all_cities: list) -> str:
    total = len(contractors)
    total_revs = sum(c.get("reviews", 0) for c in contractors)
    top_rated = sorted(
        contractors,
        key=lambda x: ((x.get("reviews") or 0), (x.get("rating") or 0.0)),
        reverse=True,
    )[:6]
    cards_html = "".join(render_card(c) for c in top_rated)
    city_items = "".join(
        f'<li><a href="/directory/california/{city_slug(c)}/"><strong>{esc(c)}, CA</strong><span class="count">{len(cities_dict[c])} listed contractors</span></a></li>'
        for c in all_cities
    )

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{DOMAIN}/#website",
                "url": f"{DOMAIN}/",
                "name": SITE_NAME,
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": f"{DOMAIN}/directory/?q={{search_term_string}}",
                    "query-input": "required name=search_term_string",
                },
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "How much does foundation repair or crawlspace encapsulation cost around Sacramento?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Minor drainage or vapor barrier fixes often start between $2,500 and $6,000, while structural underpinning piers and full crawlspace encapsulation commonly range from $6,000 to $25,000 depending on soil movement and square footage.",
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "Why do homes in Folsom, Roseville, and Sacramento develop foundation cracks?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Expansive local clay soils swell during winter rain and shrink during dry summer months, lifting and dropping concrete slabs, stem walls, and crawlspace piers.",
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "How do contractors claim a listing or get featured leads?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Any foundation, crawlspace, or drainage company can submit the Claim Listing form to update phone numbers and license info for free, or reserve an exclusive Featured city spotlight starting at $49/month.",
                        },
                    },
                ],
            },
        ],
    }

    body = f"""
<section class="hero-band">
  <div class="wrap">
    <h1>Greater Sacramento <span class="hl">Foundation, Crawlspace &amp; Drainage</span> Contractors</h1>
    <p class="lede">
      Compare {total} local structural repair, vapor barrier, French drain, and waterproofing specialists across {len(all_cities)} Sacramento, Placer, and El Dorado cities.
    </p>
    <form class="dir-search" action="/directory/" method="get">
      <input type="text" name="q" placeholder="Search city (Folsom, Roseville, Elk Grove) or service (French drain, crawlspace)..." />
      <button type="submit">Search Directory</button>
    </form>
  </div>
</section>

<div class="wrap">
  <dl class="stat-cards">
    <div><dd>{total}</dd><dt>Local Specialists</dt></div>
    <div><dd>{len(all_cities)}</dd><dt>Cities Covered</dt></div>
    <div><dd>{total_revs:,}</dd><dt>Public Reviews Indexed</dt></div>
    <div><dd>$0</dd><dt>Directory Access Fee</dt></div>
  </dl>

  <section class="two-col" style="margin-top: 1.5rem;">
    <div>
      <h2 style="margin-top:0;">Need Help With Settling Floors, Wet Crawlspaces, or Yard Drainage?</h2>
      <p>
        Expansive clay soil across Sacramento, Folsom, Roseville, and Elk Grove puts heavy pressure on foundations, crawlspace joists, and perimeter drains. Waiting until floors slope or mold spreads turns a $3,500 moisture fix into a $20,000+ structural repair.
      </p>
      <p>
        Use this directory to compare established local specialists by city, or send one quick inspection request using the form here to get connected directly.
      </p>
      <div class="biz-card open-slot" style="margin-top: 1.25rem;">
        <div class="biz-top"><span class="badge gold">Featured Sponsor Slot Open</span><span>All {len(all_cities)} Cities</span></div>
        <div class="biz-name">Put Your Company at the Top of Your City Page</div>
        <p style="margin:0; font-size:0.93rem;">
          Lock in the #1 spotlight in Folsom, Roseville, Sacramento, Rocklin, El Dorado Hills, or Elk Grove starting at $49/month, or claim exclusive homeowner quote routing.
        </p>
        <div class="biz-foot">
          <a class="phone-link" href="tel:{TRACKING_TEL}">Call {TRACKING_PHONE}</a>
          <a class="btn action" href="/featured/">Lock Your City Slot</a>
        </div>
      </div>
    </div>
    {render_quote_form(heading="Request Local Estimates &amp; Quotes")}
  </section>

  <section>
    <h2>Browse by Specialty</h2>
    <div class="biz-grid">
      <div class="biz-card">
        <div class="biz-top"><span class="badge gold">Specialty Guide</span><span>Slabs &amp; Piers</span></div>
        <div class="biz-name"><a href="/services/foundation-repair/">Foundation Repair &amp; Stabilization</a></div>
        <p style="margin:0; font-size:0.9rem;">Push piers, helical piers, stem wall crack repair, costs, and engineer vetting.</p>
        <div class="biz-foot"><a class="btn primary" href="/services/foundation-repair/">Read Guide &amp; Pros</a></div>
      </div>
      <div class="biz-card">
        <div class="biz-top"><span class="badge gold">Specialty Guide</span><span>Floor Lifting</span></div>
        <div class="biz-name"><a href="/services/house-leveling/">House Leveling Services</a></div>
        <p style="margin:0; font-size:0.9rem;">Slab foam jacking, pier-and-beam shimming, plumbing pipe protection, and leveling costs.</p>
        <div class="biz-foot"><a class="btn primary" href="/services/house-leveling/">Read Guide &amp; Pros</a></div>
      </div>
      <div class="biz-card">
        <div class="biz-top"><span class="badge gold">Specialty Guide</span><span>Under-Floor Moisture</span></div>
        <div class="biz-name"><a href="/services/crawlspace-encapsulation/">Crawlspace Encapsulation &amp; Vapor Barriers</a></div>
        <p style="margin:0; font-size:0.9rem;">Stop musty indoor air, damp floor joists, and standing water beneath raised foundations.</p>
        <div class="biz-foot"><a class="btn primary" href="/services/crawlspace-encapsulation/">View Specialists</a></div>
      </div>
      <div class="biz-card">
        <div class="biz-top"><span class="badge gold">Specialty Guide</span><span>Runoff Control</span></div>
        <div class="biz-name"><a href="/services/drainage-french-drains/">French Drains &amp; Yard Waterproofing</a></div>
        <p style="margin:0; font-size:0.9rem;">Perimeter drains, sump basins, catch basins, and grading to keep winter storms away from footings.</p>
        <div class="biz-foot"><a class="btn primary" href="/services/drainage-french-drains/">View Specialists</a></div>
      </div>
    </div>
  </section>

  <section>
    <h2>Browse Contractors by City</h2>
    <p style="color: var(--muted); margin-top: 0;">Select your city to view local foundation leveling, crawlspace encapsulation, and French drain specialists.</p>
    <ul class="city-cards">{city_items}</ul>
  </section>

  <section>
    <h2>Top Reviewed Regional Specialists</h2>
    <div class="biz-grid">{cards_html}</div>
    <p><a class="btn primary" href="/directory/">Browse All {total} Contractors</a></p>
  </section>

  <section style="margin-top: 2.5rem;">
    <h2>Common Homeowner Questions</h2>
    <h3>How much does foundation repair or crawlspace encapsulation cost around Sacramento?</h3>
    <p>
      Targeted French drains, sump pumps, and crawlspace vapor barriers often range from $2,500 to $6,500, while structural underpinning piers and full crawlspace encapsulation commonly cost between $6,000 and $25,000 depending on home size and soil movement.
    </p>
    <h3>Why do homes in Folsom, Roseville, and Sacramento develop foundation cracks?</h3>
    <p>
      Expansive local clay soil swells when soaked by winter storms and shrinks sharply in dry summer heat, causing slab edges and pier-and-beam footings to heave or settle unevenly.
    </p>
    <h3>How do contractors claim a listing or receive featured leads?</h3>
    <p>
      Submit the <a href="/claim/">Claim Listing</a> page to update your phone number and license details free, or see <a href="/featured/">Featured Placements</a> to reserve top placement in your service area.
    </p>
  </section>
</div>
"""
    return page_shell(
        "Sacramento & Placer Foundation, Crawlspace & Drainage Directory",
        f"Compare {total} foundation repair, crawlspace encapsulation, and French drain contractors across Folsom, Roseville, Sacramento, Rocklin, and El Dorado Hills.",
        "/",
        body,
        all_cities,
        schema,
    )


def build_directory_index(contractors: list, all_cities: list) -> str:
    city_opts = "".join(f'<option value="{esc(c)}">{esc(c)}, CA</option>' for c in all_cities)
    cards_html = "".join(render_card(c) for c in contractors)

    body = f"""
<div class="wrap">
  <div class="breadcrumbs"><a href="/">Home</a> &rsaquo; Directory</div>
  <h1>All Foundation, Crawlspace &amp; Drainage Contractors</h1>
  <p style="color: var(--muted);">Filter all {len(contractors)} regional listings by city, specialty, or company name.</p>

  <div class="filter-bar">
    <input type="text" id="filterQuery" placeholder="Filter by company name, city, or street..." />
    <select id="filterCity">
      <option value="">All Cities ({len(all_cities)})</option>
      {city_opts}
    </select>
    <select id="filterService">
      <option value="">All Specialties</option>
      <option value="Foundation Repair">Foundation Repair</option>
      <option value="Crawlspace Encapsulation">Crawlspace Encapsulation</option>
      <option value="Drainage">Drainage &amp; French Drains</option>
    </select>
  </div>

  <p id="resultCount" style="font-weight:700; color:var(--heading);">Showing {len(contractors)} contractors</p>
  <div id="resultsGrid" class="biz-grid">{cards_html}</div>
</div>

<script>
(function() {{
  var allData = [];
  var qEl = document.getElementById('filterQuery');
  var cEl = document.getElementById('filterCity');
  var sEl = document.getElementById('filterService');
  var gridEl = document.getElementById('resultsGrid');
  var countEl = document.getElementById('resultCount');

  var params = new URLSearchParams(window.location.search);
  if (params.get('q')) qEl.value = params.get('q');
  if (params.get('city')) cEl.value = params.get('city');
  if (params.get('service')) sEl.value = params.get('service');

  function escHtml(s) {{
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }}

  function render() {{
    if (!allData.length) return;
    var q = qEl.value.trim().toLowerCase();
    var city = cEl.value.trim().toLowerCase();
    var svc = sEl.value.trim().toLowerCase();

    var filtered = allData.filter(function(item) {{
      if (city && item.city.toLowerCase() !== city) return false;
      if (svc && !item.services.join(' ').toLowerCase().includes(svc)) return false;
      if (q) {{
        var hay = (item.name + ' ' + item.city + ' ' + item.address + ' ' + item.services.join(' ')).toLowerCase();
        if (!hay.includes(q)) return false;
      }}
      return true;
    }});

    countEl.textContent = 'Showing ' + filtered.length + ' contractor' + (filtered.length === 1 ? '' : 's');
    if (!filtered.length) {{
      gridEl.innerHTML = '<div class="panel"><p>No listings matched that filter. Call <a href="tel:{TRACKING_TEL}">{TRACKING_PHONE}</a> or <a href="/quote/">request local estimates</a> for direct contractor matching.</p></div>';
      return;
    }}

    gridEl.innerHTML = filtered.map(function(c) {{
      var chips = (c.services || []).slice(0, 4).map(function(s) {{
        return '<span class="chip">' + escHtml(s) + '</span>';
      }}).join('');
      var rev = c.rating !== null && c.rating !== undefined
        ? '<div class="stars">' + Number(c.rating).toFixed(1) + '&#9733; (' + c.reviews + ' Google reviews)</div>'
        : '<div style="font-size:0.86rem;color:var(--muted);">Public contractor record</div>';
      var tel = (c.phone || '').replace(/[^0-9+]/g, '');
      var phoneHtml = c.phone
        ? '<a class="phone-link" href="tel:' + tel + '">' + escHtml(c.phone) + '</a>'
        : '<a class="phone-link" href="tel:{TRACKING_TEL}">{TRACKING_PHONE}</a>';
      return '<article class="biz-card">' +
        '<div class="biz-top"><span>' + escHtml(c.city) + ', CA</span><span class="badge">Unclaimed</span></div>' +
        '<div class="biz-name"><a href="' + c.url + '">' + escHtml(c.name) + '</a></div>' +
        rev +
        '<div style="font-size:0.86rem;color:var(--muted);">' + escHtml(c.address) + '</div>' +
        '<div class="chips">' + chips + '</div>' +
        '<div class="biz-foot">' + phoneHtml +
        '<div style="display:flex;gap:0.4rem;">' +
        '<a class="btn subtle" href="/claim/?company=' + encodeURIComponent(c.name) + '&city=' + encodeURIComponent(c.city) + '">Claim</a>' +
        '<a class="btn primary" href="' + c.url + '">View Profile</a></div></div></article>';
    }}).join('');
  }}

  fetch('/search-index.json')
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{ allData = data; render(); }})
    .catch(function() {{}});

  qEl.addEventListener('input', render);
  cEl.addEventListener('change', render);
  sEl.addEventListener('change', render);
}})();
</script>
"""
    return page_shell(
        f"Browse All {len(contractors)} Foundation & Crawlspace Contractors",
        "Search and filter foundation repair, crawlspace encapsulation, vapor barrier, and drainage contractors across Greater Sacramento and Placer County.",
        "/directory/",
        body,
        all_cities,
    )


def build_city_page(city: str, county: str, list_co: list, all_cities: list) -> str:
    cslug = city_slug(city)
    canon = f"/directory/california/{cslug}/"
    cards_html = "".join(render_card(c) for c in list_co)
    nearby = "".join(
        f'<a class="btn subtle" href="/directory/california/{city_slug(other)}/">{esc(other)}</a>'
        for other in all_cities if other != city
    )
    local_note = CITY_LOCAL_NOTES.get(city, {})
    local_zips = local_note.get("zips", "")
    local_context = local_note.get("context", f"Soil movement and winter storm runoff around {city} require proper grading, perimeter drainage, and stable footings.")
    silo_links = "".join(
        f'<a class="btn subtle" href="/services/{s["slug"]}/">{esc(s["name"])}</a>'
        for s in SERVICE_SILOS
    )

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                    {"@type": "ListItem", "position": 2, "name": "Directory", "item": f"{DOMAIN}/directory/"},
                    {"@type": "ListItem", "position": 3, "name": f"{city}, CA", "item": f"{DOMAIN}{canon}"},
                ],
            },
            {
                "@type": "ItemList",
                "name": f"Best Foundation, Crawlspace & Drainage Contractors in {city}, CA",
                "numberOfItems": len(list_co),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": idx,
                        "name": c["name"],
                        "url": f"{DOMAIN}/company/california/{cslug}/{c['slug']}/",
                    }
                    for idx, c in enumerate(list_co, start=1)
                ],
            },
        ],
    }

    body = f"""
<div class="wrap">
  <div class="breadcrumbs"><a href="/">Home</a> &rsaquo; <a href="/directory/">Directory</a> &rsaquo; {esc(city)}, CA</div>
  <h1>Best Foundation, Crawlspace &amp; Drainage Contractors in {esc(city)}, CA</h1>
  <p style="font-size:1.05rem; color: var(--muted);">
    Comparing {len(list_co)} local specialists serving {esc(city)} ({esc(county)}{f", ZIP codes {esc(local_zips)}" if local_zips else ""}).
  </p>
  <p style="margin-top:0.25rem;">
    {esc(local_context)}
  </p>

  <div class="two-col">
    <div>
      <div class="biz-card open-slot" style="margin-bottom: 1.5rem;">
        <div class="biz-top"><span class="badge gold">#1 {esc(city)} Spotlight Open</span><span>Exclusive City Placement</span></div>
        <div class="biz-name">Own the Top Contractor Position in {esc(city)}, CA</div>
        <p style="margin:0; font-size:0.93rem;">
          Put your company above every {esc(city)} listing with priority phone dispatch and direct homeowner inspection leads.
        </p>
        <div class="biz-foot">
          <a class="phone-link" href="tel:{TRACKING_TEL}">Call {TRACKING_PHONE}</a>
          <a class="btn action" href="/featured/?city={urllib.parse.quote(city)}">Reserve {esc(city)} Slot ($49/mo)</a>
        </div>
      </div>

      <h2 style="margin-top:0;">Listed Contractors in {esc(city)} ({len(list_co)})</h2>
      <div class="biz-grid">{cards_html}</div>
    </div>

    <div>
      {render_quote_form(default_city=city, heading=f"Request {city} Quotes")}
      <div class="panel" style="margin-top: 1.25rem;">
        <h3 style="margin-top:0;">Explore By Specialty</h3>
        <div style="display:flex; flex-wrap:wrap; gap:0.45rem; margin-bottom:1.1rem;">{silo_links}</div>
        <h3 style="margin-top:0;">Nearby Service Cities</h3>
        <div style="display:flex; flex-wrap:wrap; gap:0.45rem;">{nearby}</div>
      </div>
    </div>
  </div>
</div>
"""
    return page_shell(
        f"Best Foundation, Crawlspace & Drainage in {city}, CA",
        f"Compare {len(list_co)} foundation repair, crawlspace waterproofing, and French drain contractors serving {city}, {county}, CA.",
        canon,
        body,
        all_cities,
        schema,
    )


def build_company_page(c: dict, cities_dict: dict, all_cities: list) -> str:
    cslug = city_slug(c["city"])
    canon = f"/company/california/{cslug}/{c['slug']}/"
    tel = clean_tel(c.get("phone", ""))
    chips = "".join(f'<span class="chip">{esc(s)}</span>' for s in c.get("services", []))
    website_cell = f'<a href="{esc(c["website"])}" target="_blank" rel="noopener nofollow">{esc(c["website"])}</a>' if c.get("website") else "Not listed"
    maps_cell = f'<a href="https://www.google.com/maps?cid={esc(c["cid"])}" target="_blank" rel="noopener nofollow">View on Google Maps</a>' if c.get("cid") else "Not linked"
    rating_row = f'{c["rating"]:.1f} stars ({c["reviews"]} Google reviews)' if c.get("rating") is not None else "Pending public rating sync"
    peers = [p for p in cities_dict.get(c["city"], []) if p["slug"] != c["slug"]][:4]
    peer_links = "".join(
        f'<li><a href="/company/california/{cslug}/{p["slug"]}/">{esc(p["name"])}</a></li>'
        for p in peers
    )
    silo_links = "".join(
        f'<a class="btn subtle" href="/services/{s["slug"]}/">{esc(s["name"])}</a>'
        for s in SERVICE_SILOS
    )

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                    {"@type": "ListItem", "position": 2, "name": "Directory", "item": f"{DOMAIN}/directory/"},
                    {"@type": "ListItem", "position": 3, "name": f"{c['city']}, CA", "item": f"{DOMAIN}/directory/california/{cslug}/"},
                    {"@type": "ListItem", "position": 4, "name": c["name"], "item": f"{DOMAIN}{canon}"},
                ],
            },
            {
                "@type": "HomeAndConstructionBusiness",
                "name": c["name"],
                "url": f"{DOMAIN}{canon}",
                "telephone": c.get("phone") or TRACKING_PHONE,
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": c.get("address", ""),
                    "addressLocality": c["city"],
                    "addressRegion": "CA",
                    "addressCountry": "US",
                },
            },
        ],
    }

    claim_card = f"""
<div class="panel claim-box" style="margin-top: 1.25rem;">
  <h3 style="margin-top:0;">Do You Own {esc(c["name"])}?</h3>
  <p style="font-size: 0.9rem; margin: 0 0 0.9rem;">
    Claim this free listing to verify your California CSLB license number, update your direct phone, and receive priority homeowner quote alerts in {esc(c["city"])}.
  </p>
  <a class="btn action" style="display:block;" href="/claim/?company={urllib.parse.quote(c['name'])}&city={urllib.parse.quote(c['city'])}">Claim This Profile Free</a>
</div>
"""

    peers_block = f"""
      <div class="panel" style="margin-top: 1.25rem;">
        <h3 style="margin-top:0;">More {esc(c["city"])} Specialists &amp; Guides</h3>
        {"<ul style='padding-left:1.15rem; margin:0 0 1rem;'>" + peer_links + "</ul>" if peer_links else ""}
        <div style="display:flex; flex-wrap:wrap; gap:0.45rem;">
          <a class="btn subtle" href="/directory/california/{cslug}/">All {esc(c["city"])} Contractors</a>
          {silo_links}
        </div>
      </div>"""

    body = f"""
<div class="wrap">
  <div class="breadcrumbs">
    <a href="/">Home</a> &rsaquo; <a href="/directory/">Directory</a> &rsaquo; <a href="/directory/california/{cslug}/">{esc(c["city"])}, CA</a> &rsaquo; {esc(c["name"])}
  </div>
  <h1>{esc(c["name"])}</h1>
  <p style="color:var(--muted); margin-top:0;">{esc(c.get("category", "Contractor"))} serving {esc(c["city"])} &amp; {esc(c["county"])}</p>

  <div class="two-col">
    <div>
      <div class="panel">
        <h2 style="margin-top:0;">Business Profile Details</h2>
        <table class="info-table">
          <tr><th>Company Name</th><td>{esc(c["name"])}</td></tr>
          <tr><th>City / County</th><td>{esc(c["city"])}, CA ({esc(c["county"])})</td></tr>
          <tr><th>Listed Address</th><td>{esc(c.get("address", ""))}</td></tr>
          <tr><th>Phone</th><td>{f'<a href="tel:{tel}">{esc(c["phone"])}</a>' if c.get("phone") else "Not listed"}</td></tr>
          <tr><th>Website</th><td>{website_cell}</td></tr>
          <tr><th>Google Maps</th><td>{maps_cell}</td></tr>
          <tr><th>Google Rating</th><td>{esc(rating_row)}</td></tr>
          <tr><th>Profile Status</th><td>{"Verified Owner" if c.get("claimed") else "Unclaimed Public Record"}</td></tr>
        </table>
        <h3>Listed Capabilities</h3>
        <div class="chips" style="margin-bottom:1rem;">{chips}</div>
        <p style="font-size: 0.85rem; color: var(--muted); margin-bottom:0;">
          Listing note: Public business facts compiled from Google Maps and public California contractor listings. Business owners can update or verify details anytime via <a href="/claim/">Claim Listing</a>.
        </p>
      </div>
      {peers_block}
    </div>

    <div>
      {render_quote_form(default_city=c["city"], target_company=c["name"], heading=f"Request a {c['city']} Estimate")}
      {claim_card}
    </div>
  </div>
</div>
"""
    return page_shell(
        f"{c['name']} | {c['city']}, CA Foundation & Crawlspace",
        f"{c['name']} in {c['city']}, CA. View listed services, address, phone, and request a local foundation, crawlspace, or drainage estimate.",
        canon,
        body,
        all_cities,
        schema,
    )


def build_service_page(silo: dict, contractors: list, all_cities: list) -> str:
    canon = f"/services/{silo['slug']}/"
    matching = [
        c for c in contractors
        if silo["match_token"].lower() in " ".join(c.get("services", [])).lower()
    ]
    if not matching:
        matching = contractors[:12]
    cards_html = "".join(render_card(c) for c in matching[:24])
    city_btns = "".join(
        f'<a class="btn subtle" href="/directory/california/{city_slug(c)}/">{esc(c)}</a>'
        for c in all_cities
    )

    faq_pairs = silo.get("faqs") or [(silo["faq_q"], silo["faq_a"])]
    faq_entities = [
        {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        }
        for q, a in faq_pairs
    ]

    graph = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                {"@type": "ListItem", "position": 2, "name": "Directory", "item": f"{DOMAIN}/directory/"},
                {"@type": "ListItem", "position": 3, "name": silo["name"], "item": f"{DOMAIN}{canon}"},
            ],
        },
        {
            "@type": "ItemList",
            "name": silo["title"],
            "numberOfItems": len(matching),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": idx,
                    "name": c["name"],
                    "url": f"{DOMAIN}/company/california/{city_slug(c['city'])}/{c['slug']}/",
                }
                for idx, c in enumerate(matching[:24], start=1)
            ],
        },
        {
            "@type": "FAQPage",
            "mainEntity": faq_entities,
        },
    ]

    if silo.get("html"):
        graph.append(
            {
                "@type": "Article",
                "headline": silo["title"],
                "description": silo["desc"],
                "mainEntityOfPage": f"{DOMAIN}{canon}",
                "datePublished": TODAY_STR,
                "dateModified": TODAY_STR,
                "author": {
                    "@type": "Person",
                    "name": "Molly Perkins",
                    "url": "https://www.facebook.com/mollyperkins354",
                    "sameAs": [
                        "https://www.facebook.com/mollyperkins354",
                        "https://aine.ws/authors/molly-perkins",
                    ],
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "Gold Standard Assets LLC",
                    "url": "https://www.gslocalseo.com/",
                },
            }
        )

    schema = {"@context": "https://schema.org", "@graph": graph}

    if silo.get("html"):
        author_box = f"""
      <div class="panel" style="margin-bottom:2rem; display:flex; flex-direction:column; gap:0.4rem;">
        <div style="font-size:0.82rem; font-weight:800; text-transform:uppercase; color:var(--accent-mid);">About the Author</div>
        <div style="font-weight:800; font-size:1.08rem; color:var(--heading);">
          <a href="https://www.facebook.com/mollyperkins354" target="_blank" rel="noopener author">Molly Perkins</a>
        </div>
        <p style="margin:0; font-size:0.93rem;">
          Molly Perkins writes practical California homeowner guides covering contractor vetting, call response systems, and residential foundation and drainage repair across Greater Sacramento. Connect via <a href="https://www.facebook.com/mollyperkins354" target="_blank" rel="noopener">Facebook</a> or view her editorial profile on <a href="https://aine.ws/authors/molly-perkins" target="_blank" rel="noopener">Aine</a>.
        </p>
      </div>"""
        main_col = f"""
      {silo["html"]}
      {author_box}
      <h2>Compare Local {esc(silo["name"])} Specialists ({len(matching)})</h2>
      <p style="color:var(--muted); margin-top:0;">Review area contractors serving Greater Sacramento, Placer, and El Dorado counties, or claim your company profile to update details.</p>
      <div class="biz-grid">{cards_html}</div>"""
        subhead = f'<p style="font-size:0.92rem; color:var(--muted); margin-top:0;">By <a href="https://www.facebook.com/mollyperkins354" target="_blank" rel="noopener author"><strong>Molly Perkins</strong></a> &middot; Updated {TODAY_STR}</p>'
    else:
        main_col = f"""
      <h2 style="margin-top:0;">Matching Local Specialists ({len(matching)})</h2>
      <div class="biz-grid">{cards_html}</div>
      <div class="panel" style="margin-top:1.5rem;">
        <h2 style="margin-top:0;">{esc(silo["faq_q"])}</h2>
        <p style="margin-bottom:0;">{esc(silo["faq_a"])}</p>
      </div>"""
        subhead = f'<p style="font-size:1.05rem; color:var(--muted); max-width:74ch;">{esc(silo["intro"])}</p>'

    silo_nav = "".join(
        f'<a class="btn subtle" href="/services/{s["slug"]}/">{esc(s["name"])}</a>'
        for s in SERVICE_SILOS if s["slug"] != silo["slug"]
    )

    body = f"""
<div class="wrap">
  <div class="breadcrumbs"><a href="/">Home</a> &rsaquo; <a href="/directory/">Directory</a> &rsaquo; {esc(silo["name"])}</div>
  <h1>{silo["h1"]}</h1>
  {subhead}

  <div class="two-col">
    <div>
      {main_col}
    </div>
    <div>
      {render_quote_form(default_service=silo["name"], heading=f"Request {silo['name']} Quotes")}
      <div class="panel" style="margin-top:1.25rem;">
        <h3 style="margin-top:0;">Related Buying Guides</h3>
        <div style="display:flex; flex-wrap:wrap; gap:0.45rem; margin-bottom:1.1rem;">{silo_nav}</div>
        <h3 style="margin-top:0;">Browse By City</h3>
        <div style="display:flex; flex-wrap:wrap; gap:0.45rem;">{city_btns}</div>
      </div>
    </div>
  </div>
</div>
"""
    return page_shell(silo["title"], silo["desc"], canon, body, all_cities, schema)


def build_static_pages(all_cities: list) -> dict:
    pages = {}

    # /quote/
    pages["/quote/"] = page_shell(
        "Request Foundation, Crawlspace or Drainage Quotes",
        "Get connected with Greater Sacramento, Folsom, Roseville, and Elk Grove foundation leveling, crawlspace encapsulation, and French drain contractors.",
        "/quote/",
        f"""
<div class="wrap" style="max-width: 780px; margin: 2.25rem auto 4rem;">
  <div class="breadcrumbs"><a href="/">Home</a> &rsaquo; Request Quotes</div>
  <h1>Request Foundation, Crawlspace or Drainage Quotes</h1>
  <p style="color: var(--muted);">
    Tell us what your home or crawlspace needs below, or call our dispatch desk at <a href="tel:{TRACKING_TEL}"><strong>{TRACKING_PHONE}</strong></a>. Submitting a request here is free; individual contractors confirm upfront if a diagnostic or real-estate escrow inspection fee applies.
  </p>
  {render_quote_form(heading="Homeowner Project Details")}
</div>
""",
        all_cities,
    )

    # /claim/
    claim_body = f"""
<div class="wrap" style="max-width: 740px; margin: 2.25rem auto 4rem;">
  <div class="breadcrumbs"><a href="/">Home</a> &rsaquo; Claim Profile</div>
  <h1>Claim Your Free Contractor Profile</h1>
  <p style="color: var(--muted);">
    Own or manage a foundation repair, crawlspace waterproofing, or drainage company in Greater Sacramento? Verify your profile below to update your phone number, add your CSLB license, and opt into direct homeowner quote alerts.
  </p>
  <div class="panel claim-box">
    <h2 style="margin-top:0;">Contractor Verification Form</h2>
    <form class="lead-form" data-lead-form="1" data-lead-type="claim">
      <div class="hp-trap" aria-hidden="true">
        <label>Website</label>
        <input type="text" name="website_url" tabindex="-1" autocomplete="off" />
      </div>
      <div class="form-row-2">
        <div>
          <label>Company Name *</label>
          <input type="text" id="claimCompany" name="company" required placeholder="Exact Business Name" />
        </div>
        <div>
          <label>Owner / Manager Name *</label>
          <input type="text" name="name" required placeholder="First &amp; Last Name" />
        </div>
      </div>
      <div class="form-row-2">
        <div>
          <label>Direct Mobile / Dispatch Phone *</label>
          <input type="tel" name="phone" required placeholder="(916) 555-0192" />
        </div>
        <div>
          <label>Work Email *</label>
          <input type="email" name="email" required placeholder="owner@company.com" />
        </div>
      </div>
      <div class="form-row-2">
        <div>
          <label>Primary City *</label>
          <input type="text" id="claimCity" name="city" required placeholder="e.g. Folsom, Roseville, Sacramento" />
        </div>
        <div>
          <label>California CSLB License # (Optional)</label>
          <input type="text" name="license" placeholder="e.g. 1045231" />
        </div>
      </div>
      <div>
        <label>Notes / Services to Highlight</label>
        <textarea name="notes" rows="2" placeholder="Foundation piers, crawlspace vapor barrier, French drains, sump pumps..."></textarea>
      </div>
      <button type="submit" class="btn action" style="padding: 0.85rem; font-size: 1rem;">Submit Verification Request</button>
    </form>
    <div class="form-status">
      <strong>Verification Submitted.</strong> We received your profile claim and will confirm your listing updates shortly. Need priority placement? Call <a href="tel:{TRACKING_TEL}">{TRACKING_PHONE}</a>.
    </div>
  </div>
</div>
<script>
(function() {{
  var p = new URLSearchParams(window.location.search);
  if (p.get('company')) document.getElementById('claimCompany').value = p.get('company');
  if (p.get('city')) document.getElementById('claimCity').value = p.get('city');
}})();
</script>
"""
    pages["/claim/"] = page_shell(
        "Claim Your Contractor Listing | Foundation & Crawlspace Directory",
        "Claim and update your foundation repair, crawlspace waterproofing, or drainage listing on foundationcrawlspace.online.",
        "/claim/",
        claim_body,
        all_cities,
    )

    # /featured/
    featured_body = f"""
<div class="wrap" style="margin: 2rem auto 4rem;">
  <div class="breadcrumbs"><a href="/">Home</a> &rsaquo; Featured &amp; Lead Routing</div>
  <h1>Get Featured &amp; Capture Exclusive Local Inspection Leads</h1>
  <p style="color: var(--muted); max-width: 72ch;">
    Put your company at the very top of your city pages on foundationcrawlspace.online, or lock exclusive homeowner inspection leads in your service radius.
  </p>

  <div class="biz-grid" style="margin-top:1.75rem;">
    <div class="biz-card">
      <div class="biz-top"><span class="badge">Free</span><span>Standard</span></div>
      <div class="biz-name">Verified Public Profile</div>
      <p style="font-size:1.4rem; font-weight:800; color:var(--heading); margin:0.25rem 0;">$0 / mo</p>
      <p style="font-size:0.92rem;">Verify your phone number, website link, city list, and CSLB license number.</p>
      <div class="biz-foot"><a class="btn primary" style="width:100%;" href="/claim/">Claim Free Listing</a></div>
    </div>

    <div class="biz-card open-slot">
      <div class="biz-top"><span class="badge gold">Best Value</span><span>1 Spot Per City</span></div>
      <div class="biz-name">City Spotlight Listing</div>
      <p style="font-size:1.4rem; font-weight:800; color:var(--heading); margin:0.25rem 0;">$49 / mo</p>
      <p style="font-size:0.92rem;">Pinned #1 card above regular listings in your target city, Verified Sponsor badge, and direct call/quote button.</p>
      <div class="biz-foot"><a class="btn action" style="width:100%;" href="tel:{TRACKING_TEL}">Call {TRACKING_PHONE} to Lock</a></div>
    </div>

    <div class="biz-card" id="leads">
      <div class="biz-top"><span class="badge">Exclusive</span><span>Lead Routing</span></div>
      <div class="biz-name">Exclusive City Lead Partner</div>
      <p style="font-size:1.4rem; font-weight:800; color:var(--heading); margin:0.25rem 0;">$149 / mo</p>
      <p style="font-size:0.92rem;">Top placement across 3 cities plus exclusive homeowner inspection requests and inbound calls forwarded live to your dispatch line.</p>
      <div class="biz-foot"><a class="btn primary" style="width:100%;" href="tel:{TRACKING_TEL}">Reserve City Territory</a></div>
    </div>
  </div>

  <div style="max-width: 700px; margin-top: 2rem;">
    <div class="panel">
      <h2 style="margin-top:0;">Want Your Google Business Profile Ranking #1 Too?</h2>
      <p style="font-size:0.95rem;">
        Published by <a href="https://www.gslocalseo.com" target="_blank" rel="noopener">Gold Standard Local SEO</a> in Folsom, CA. Along with featured directory placement, we help contractors win the Google Maps 3-Pack and run automated 5-star review campaigns on flat month-to-month terms.
      </p>
    </div>
  </div>

  <div style="max-width: 700px; margin-top: 1.5rem;">
    {render_quote_form(heading="Inquire About a Featured City Slot or Exclusive Leads", lead_type="featured")}
  </div>
</div>
"""
    pages["/featured/"] = page_shell(
        "Featured Contractor Listings & Lead Routing | Foundation & Crawlspace Directory",
        "Reserve a #1 City Spotlight ($49/mo) or Exclusive City Lead Partner territory ($149/mo) for Greater Sacramento foundation and crawlspace contractors.",
        "/featured/",
        featured_body,
        all_cities,
    )

    # /about/
    pages["/about/"] = page_shell(
        "About Foundation & Crawlspace Directory",
        "About foundationcrawlspace.online, our verification process, and publisher information in Folsom, CA.",
        "/about/",
        f"""
<div class="wrap" style="max-width: 800px; margin: 2.25rem auto 4rem;">
  <div class="breadcrumbs"><a href="/">Home</a> &rsaquo; About</div>
  <h1>About {SITE_NAME}</h1>
  <p>
    <strong>foundationcrawlspace.online</strong> is an independent regional directory covering residential and light commercial foundation repair, house leveling, crawlspace encapsulation, vapor barriers, French drains, and sump pump drainage across Greater Sacramento, Placer County, and El Dorado County.
  </p>
  <p>
    Our goal is simple: help local homeowners compare legitimate area specialists by city without fighting noisy national lead-broker spam, and give local contractors a clean verified profile they control.
  </p>
  <h2>Publisher &amp; Verification Desk</h2>
  <p>
    Maintained by <strong>Gold Standard Assets LLC</strong> (Gold Standard Local SEO), 705 Gold Lake Dr Ste 250, Folsom, CA 95630.<br />
    Verification Desk: <a href="tel:{TRACKING_TEL}">{TRACKING_PHONE}</a> | Email: <a href="mailto:goldstandardaiagency@gmail.com">goldstandardaiagency@gmail.com</a>
  </p>
</div>
""",
        all_cities,
    )

    # /contact/
    pages["/contact/"] = page_shell(
        "Contact Us | Foundation & Crawlspace Directory",
        "Contact the foundationcrawlspace.online team in Folsom, CA to request a listing update, removal, or featured partnership.",
        "/contact/",
        f"""
<div class="wrap" style="max-width: 760px; margin: 2.25rem auto 4rem;">
  <div class="breadcrumbs"><a href="/">Home</a> &rsaquo; Contact</div>
  <h1>Contact Directory Desk</h1>
  <p>Call or text <a href="tel:{TRACKING_TEL}"><strong>{TRACKING_PHONE}</strong></a>, email <a href="mailto:goldstandardaiagency@gmail.com">goldstandardaiagency@gmail.com</a>, or send a note below.</p>
  {render_quote_form(heading="Send a Message or Listing Update")}
</div>
""",
        all_cities,
    )

    # /privacy-policy/
    pages["/privacy-policy/"] = page_shell(
        "Privacy Policy | Foundation & Crawlspace Directory",
        "Privacy policy and lead-handling disclosure for foundationcrawlspace.online.",
        "/privacy-policy/",
        f"""
<div class="wrap" style="max-width: 800px; margin: 2.25rem auto 4rem;">
  <div class="breadcrumbs"><a href="/">Home</a> &rsaquo; Privacy Policy</div>
  <h1>Privacy Policy</h1>
  <p>
    When you submit an estimate request, inspection inquiry, or contractor profile claim on <strong>foundationcrawlspace.online</strong>, we use your contact information strictly to follow up on your request or connect you with participating foundation, crawlspace, or drainage contractors in your service area.
  </p>
  <p>
    We do not sell visitor data to unrelated third-party ad networks. To update or delete an inquiry or business listing, call <a href="tel:{TRACKING_TEL}">{TRACKING_PHONE}</a> or email <a href="mailto:goldstandardaiagency@gmail.com">goldstandardaiagency@gmail.com</a>.
  </p>
</div>
""",
        all_cities,
    )

    return pages


def write_page(rel_path: str, content: str):
    clean = rel_path.strip("/")
    out_dir = BASE_DIR / clean if clean else BASE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(content, encoding="utf-8")


def main():
    for stale_dir in ["directory", "company", "services", "quote", "claim", "featured", "about", "contact", "privacy-policy"]:
        target = BASE_DIR / stale_dir
        if target.exists():
            shutil.rmtree(target)

    contractors = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    cities_dict = {}
    for c in contractors:
        cities_dict.setdefault(c["city"], []).append(c)
    all_cities = sorted(cities_dict.keys(), key=lambda x: (-len(cities_dict[x]), x))

    urls = ["/"]
    write_page("/", build_homepage(contractors, cities_dict, all_cities))

    urls.append("/directory/")
    write_page("/directory/", build_directory_index(contractors, all_cities))

    for silo in SERVICE_SILOS:
        path = f"/services/{silo['slug']}/"
        urls.append(path)
        write_page(path, build_service_page(silo, contractors, all_cities))

    for city in all_cities:
        list_co = cities_dict[city]
        county = list_co[0]["county"]
        path = f"/directory/california/{city_slug(city)}/"
        urls.append(path)
        write_page(path, build_city_page(city, county, list_co, all_cities))

    for c in contractors:
        path = f"/company/california/{city_slug(c['city'])}/{c['slug']}/"
        urls.append(path)
        write_page(path, build_company_page(c, cities_dict, all_cities))

    static_pages = build_static_pages(all_cities)
    for path, content in static_pages.items():
        urls.append(path)
        write_page(path, content)

    search_index = [
        {
            "name": c["name"],
            "city": c["city"],
            "county": c["county"],
            "address": c["address"],
            "phone": c["phone"],
            "rating": c["rating"],
            "reviews": c["reviews"],
            "services": c["services"],
            "url": f"/company/california/{city_slug(c['city'])}/{c['slug']}/",
        }
        for c in contractors
    ]
    (BASE_DIR / "search-index.json").write_text(json.dumps(search_index, indent=2), encoding="utf-8")

    sitemap_entries = "".join(
        f"  <url><loc>{DOMAIN}{u}</loc><lastmod>{TODAY_STR}</lastmod></url>\n"
        for u in urls
    )
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_entries}</urlset>
"""
    (BASE_DIR / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")

    robots_txt = f"""# {SITE_NAME} ({DOMAIN})
# 3/3 AI Crawlability & Multi-Engine Indexing Policy

User-agent: *
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: GoogleOther
Allow: /

User-agent: Bingbot
Allow: /

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: Applebot
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: Meta-ExternalAgent
Allow: /

User-agent: DuckDuckBot
Allow: /

User-agent: CCBot
Allow: /

User-agent: YouBot
Allow: /

User-agent: cohere-ai
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
# LLMs.txt: {DOMAIN}/llms.txt
# LLMs-Full.txt: {DOMAIN}/llms-full.txt
"""
    (BASE_DIR / "robots.txt").write_text(robots_txt, encoding="utf-8")

    city_summary_lines = "\n".join(
        f"- [{c}, CA Foundation & Drainage Contractors ({len(cities_dict[c])} listed)]({DOMAIN}/directory/california/{city_slug(c)}/): {CITY_LOCAL_NOTES.get(c, {}).get('zips', 'California')}"
        for c in all_cities
    )
    guide_summary_lines = "\n".join(
        f"- [{s['title']}]({DOMAIN}/services/{s['slug']}/): {s['desc']}"
        for s in SERVICE_SILOS
    )
    llms_txt = f"""# {SITE_NAME} (foundationcrawlspace.online)

> Independent California contractor directory and homeowner cost guide for foundation repair, house leveling, crawlspace encapsulation, vapor barriers, and French drain waterproofing across {len(all_cities)} Greater Sacramento, Placer County, and El Dorado County cities ({len(contractors)} public contractor profiles).

## Canonical Verification Facts
- **Site URL**: {DOMAIN}/
- **Direct Dispatch & Verification Line**: {TRACKING_PHONE} ({TRACKING_TEL})
- **Contact Email**: goldstandardaiagency@gmail.com
- **Guide Author**: Molly Perkins (https://www.facebook.com/mollyperkins354 | https://aine.ws/authors/molly-perkins)
- **Publisher**: Gold Standard Assets LLC (Gold Standard Local SEO, 705 Gold Lake Dr Ste 250, Folsom, CA 95630)
- **Total Indexed Contractors**: {len(contractors)}

## Buying & Cost Guides (PAA + PASF Answers)
{guide_summary_lines}

## Key Local Cost & Repair Facts
- **Foundation Pier Underpinning Cost (Sacramento)**: $1,600 to $3,000 per push pier or helical pier; most residential structural projects run $6,500 to $22,000.
- **Pier-and-Beam House Leveling Cost**: $2,500 to $6,500 for accessible crawlspace re-shimming and adjustable steel posts; full deep-pier slab lifting runs $8,000 to $25,000+.
- **Polyurethane Foam Slab Lifting**: $1,500 to $4,500 for settled interior slab pockets, driveways, or garages.
- **Homeowners Insurance Rule**: Standard California policies exclude clay-soil movement; coverage applies only when a sudden plumbing break under the slab washes out support soil.

## City Contractor Directories
{city_summary_lines}

## Directory Funnels & Policy
- [Browse All Contractors ({len(contractors)})]({DOMAIN}/directory/)
- [Request Foundation or Crawlspace Quotes]({DOMAIN}/quote/)
- [Claim Free Contractor Profile]({DOMAIN}/claim/)
- [Featured City Spotlight & Exclusive Lead Routing ($49 to $149/mo)]({DOMAIN}/featured/)
- [Full Directory Context (llms-full.txt)]({DOMAIN}/llms-full.txt)
"""
    (BASE_DIR / "llms.txt").write_text(llms_txt, encoding="utf-8")

    company_lines = "\n".join(
        f"- [{c['name']} ({c['city']}, CA)]({DOMAIN}/company/california/{city_slug(c['city'])}/{c['slug']}/) | {c.get('phone') or TRACKING_PHONE} | {', '.join(c.get('services', [])[:3])}"
        for c in contractors
    )
    llms_full = llms_txt + "\n## Listed Greater Sacramento, Placer & El Dorado Contractors\n" + company_lines + "\n"
    (BASE_DIR / "llms-full.txt").write_text(llms_full, encoding="utf-8")

    print(f"[OK] Built {len(urls)} pages across {len(all_cities)} cities + search-index.json + sitemap.xml + robots.txt + llms.txt")


if __name__ == "__main__":
    main()
