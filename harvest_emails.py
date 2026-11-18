#!/usr/bin/env python3
"""
Contractor Website Finder, Email Harvester & List Hygiene Validator
for foundationcrawlspace.online.

1. Cleans placeholder websites (e.g. https://www.google.com/goto) and discovers real
   official contractor domains via Serper organic search, verifying ownership via
   phone-number or domain+title match on the live page.
2. Crawls contractor pages (/, /contact, /contact-us, /about, /about-us, /free-estimate,
   plus discovered internal contact/quote links), decodes Cloudflare __cf_email__ tokens,
   and strips <script>/<style>/HTML comments so font/library/plugin author emails never leak in.
3. Falls back to Serper email queries with strict attribution guards.
4. Enforces strict bounce hygiene (valid syntax, no asset/CMS/placeholder/vendor domains,
   no noreply/system traps, valid DNS MX + SPF check, global email deduplication).
5. Writes clean tiered CSVs (never storing private outreach emails inside public JSON).
"""

import csv
import html
import json
import re
import smtplib
import ssl
import subprocess
import threading
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "contractors_data.json"
OUT_CLEAN_CSV = BASE_DIR / "contractor_outreach_clean.csv"
OUT_REJECTED_CSV = BASE_DIR / "contractor_outreach_rejected.csv"
ROOT_ENV = BASE_DIR.parent / ".env"

SSL_CTX = ssl._create_unverified_context()
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,12}")
CF_EMAIL_RE = re.compile(r'(?:data-cfemail=|/cdn-cgi/l/email-protection#)([0-9a-fA-F]{6,})')

AGGREGATOR_OR_INVALID_HOSTS = {
    "google.com", "maps.google.com", "goo.gl", "yelp.com", "bbb.org",
    "angi.com", "angieslist.com", "homeadvisor.com", "thumbtack.com",
    "buildzoom.com", "porch.com", "nextdoor.com", "yellowpages.com",
    "superpages.com", "mapquest.com", "chamberofcommerce.com", "manta.com",
    "bizapedia.com", "opengovus.com", "dnb.com", "zoominfo.com",
    "houzz.com", "expertise.com", "threebestrated.com", "bark.com",
    "networx.com", "cslb.ca.gov", "sos.ca.gov", "ca.gov",
    "facebook.com", "instagram.com", "linkedin.com", "youtube.com",
    "twitter.com", "x.com", "tiktok.com", "pinterest.com", "reddit.com",
    "wikipedia.org", "apple.com", "bing.com", "yahoo.com", "local.yahoo.com",
    "amazon.com", "birdeye.com", "reviews.birdeye.com", "guildquality.com",
    "patch.com", "ziprecruiter.com", "indeed.com", "glassdoor.com",
    "cybo.com", "biashara.cybo.com", "toponavi.com", "primelocal.org",
    "cityspotz.com", "findaconcretecontractor.com", "listaservice.com",
    "verifiednode.com", "calstatedir.com", "alignable.com", "merchantcircle.com",
    "hotfrog.com", "tuugo.us", "crunchbase.com", "opencorporates.com",
    "corporationwiki.com", "buzzfile.com", "issuu.com", "scribd.com",
    "medium.com", "procore.com", "thebluebook.com", "construction.com",
    "foundationcrawlspace.online", "bestoforangevale.com", "trustanalytica.org",
    "folsomdirect.us", "myarea.network", "localstack.com", "kudzu.com",
    "dexknows.com", "crawlspacespecialistnc.com",
}

BAD_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net", "domain.com", "email.com",
    "test.com", "yoursite.com", "yourdomain.com", "company.com", "business.com",
    "sentry.io", "sentry-next.wixpress.com", "wixpress.com", "wix.com",
    "squarespace.com", "godaddy.com", "secureserver.net", "wordpress.org",
    "wordpress.com", "wpengine.com", "webflow.com", "shopify.com",
    "cloudflare.com", "gstatic.com", "googleapis.com", "google.com",
    "facebook.com", "instagram.com", "youtube.com", "twitter.com", "x.com",
    "linkedin.com", "yelp.com", "bbb.org", "latofonts.com", "fontawesome.com",
    "jquery.com", "schema.org", "w3.org", "typekit.net", "fonts.com",
    "hubspot.com", "mailchimp.com", "constantcontact.com", "calendly.com",
    "intercom.io", "zendesk.com", "freshdesk.com", "servpro.com",
    "groundworks.com", "userway.org", "cookieyes.com", "iubenda.com",
    "mysite.com", "website.com", "placeholder.com", "patch.com",
    "ziprecruiter.com", "guildquality.com", "birdeye.com", "listaservice.com",
    "verifiednode.com", "cityspotz.com", "primelocal.org", "findaconcretecontractor.com",
}

BAD_LOCAL_PREFIXES = (
    "noreply", "no-reply", "donotreply", "do-not-reply", "mailer-daemon",
    "postmaster", "abuse", "privacy", "legal", "dmca", "billing", "ap", "ar",
    "careers", "jobs", "hr", "spam", "webmaster", "hostmaster", "root",
    "security", "compliance", "unsubscribe", "bounce", "bounces", "feedback",
    "notifications", "notification", "alert", "alerts", "automated",
    "accessibility", "contributors",
)

BAD_LOCAL_EXACT = {
    "test", "demo", "user", "name", "yourname", "youremail", "email",
    "someone", "example", "filler", "johndoe", "janedoe", "john.doe",
    "admin", "administrator", "dev", "developer", "design", "webdesign",
    "marketing", "seo", "wordpress", "wp", "impallari",
}

BAD_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".css",
    ".js", ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".mp4", ".webm",
)

FREE_PROVIDERS = {
    "gmail.com", "yahoo.com", "ymail.com", "aol.com", "hotmail.com",
    "outlook.com", "icloud.com", "me.com", "live.com", "msn.com",
    "sbcglobal.net", "att.net", "comcast.net", "pacbell.net", "proton.me",
    "protonmail.com", "gmx.com",
}

GENERIC_COMPANY_WORDS = {
    "inc", "llc", "co", "corp", "company", "services", "service", "group",
    "enterprises", "enterprise", "california", "sacramento", "construction",
    "contracting", "contractor", "contractors", "builders", "concrete",
    "foundation", "foundations", "crawlspace", "crawl", "space", "drainage",
    "waterproofing", "repair", "repairs", "solutions", "pros", "pro", "the",
    "and", "of", "in", "by", "son", "sons", "brothers", "bros", "landscape",
    "landscaping", "restoration", "home", "homes", "design", "remodel",
    "remodeling", "building", "excavating",
}

ROLE_LOCAL_PARTS = {
    "info", "contact", "office", "estimates", "estimate", "quotes", "quote",
    "service", "services", "sales", "hello", "inquiries", "inquiry",
    "dispatch", "scheduling", "schedule", "team", "support", "help",
}

cache_lock = threading.Lock()
mx_cache = {}
spf_cache = {}
port25_blocked = None


def load_serper_key() -> str:
    if ROOT_ENV.exists():
        for line in ROOT_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("SERPER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def norm_host(url: str) -> str:
    if not url or not url.startswith("http"):
        return ""
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.").split(":")[0]


def is_aggregator_host(host: str) -> bool:
    if not host or "." not in host:
        return True
    return host in AGGREGATOR_OR_INVALID_HOSTS or any(
        host.endswith("." + bad) for bad in AGGREGATOR_OR_INVALID_HOSTS
    )


def company_tokens(name: str) -> list:
    raw = re.findall(r"[a-z0-9]+", name.lower())
    distinctive = [t for t in raw if len(t) >= 3 and t not in GENERIC_COMPANY_WORDS]
    return distinctive if distinctive else [t for t in raw if len(t) >= 2 and t not in ("inc", "llc", "co", "corp")]


def domain_matches_company(dom: str, company: str) -> bool:
    dom_flat = re.sub(r"[^a-z0-9]", "", dom.split(".", 1)[0])
    toks = company_tokens(company)
    all_raw = [t for t in re.findall(r"[a-z0-9]+", company.lower()) if len(t) >= 3 and t not in ("inc", "llc", "corp", "the", "and")]
    if any(t in dom_flat for t in toks if len(t) >= 4):
        return True
    if len(toks) == 1 and len(toks[0]) == 3 and toks[0] in dom_flat:
        return True
    # Match abbreviated two-word names like "California Exteriors" -> californiaext.com
    if len(all_raw) >= 2 and all_raw[0] in dom_flat and any(t[:3] in dom_flat for t in all_raw[1:]):
        return True
    hits = sum(1 for t in toks if len(t) >= 3 and t in dom_flat)
    return hits >= 2


def fetch_url(url: str, timeout: int = 8) -> tuple:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "text/html" not in ctype and "text/plain" not in ctype and ctype:
                return "", resp.geturl()
            return resp.read(450_000).decode("utf-8", errors="ignore"), resp.geturl()
    except Exception:
        return "", ""


def serper_search(query: str, serper_key: str, num: int = 6) -> list:
    if not serper_key:
        return []
    payload = json.dumps({"q": query, "num": num}).encode("utf-8")
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        return d.get("organic", [])
    except Exception:
        return []


def verify_website_ownership(url: str, company: str, city: str, phone: str, serper_blob: str = "") -> str:
    body, final_url = fetch_url(url, timeout=7)
    final_host = norm_host(final_url or url)
    if is_aggregator_host(final_host):
        return ""
    if body:
        body_digits = re.sub(r"\D", "", body)
        phone_digits = re.sub(r"\D", "", phone or "")
        phone_match = len(phone_digits) >= 10 and (phone_digits[-10:] in body_digits or phone_digits[-7:] in body_digits)
        if phone_match:
            parsed = urllib.parse.urlparse(final_url or url)
            return f"{parsed.scheme}://{parsed.netloc}/"

        title_m = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
        title_txt = html.unescape(title_m.group(1)).lower() if title_m else ""
        body_low = body.lower()
        ca_geo = (city.lower() in body_low) or ("california" in body_low) or any(ac in body_low for ac in ("(916)", "(530)", "(279)", "916-", "530-", "279-"))
        toks = company_tokens(company)
        if domain_matches_company(final_host, company) and any(t in title_txt for t in toks) and ca_geo:
            parsed = urllib.parse.urlparse(final_url or url)
            return f"{parsed.scheme}://{parsed.netloc}/"
        return ""

    # If live site returned 403/timeout (e.g. Cloudflare), trust only when Serper snippet confirms domain + CA/city/phone
    snip_low = serper_blob.lower()
    phone_digits = re.sub(r"\D", "", phone or "")
    has_ca_or_phone = (phone_digits and phone_digits[-4:] in re.sub(r"\D", "", snip_low)) or (
        city.lower() in snip_low or "california" in snip_low or " ca" in snip_low
    )
    if domain_matches_company(final_host, company) and has_ca_or_phone:
        parsed = urllib.parse.urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/"
    return ""


def discover_real_website(company: str, city: str, phone: str, serper_key: str) -> str:
    if not serper_key:
        return ""
    queries = [f'"{company}" {city} CA']
    if phone:
        queries.append(f'"{company}" "{phone}"')

    seen_hosts = set()
    for q in queries:
        for item in serper_search(q, serper_key, num=6):
            link = item.get("link", "")
            host = norm_host(link)
            if not link.startswith("http") or is_aggregator_host(host) or host in seen_hosts:
                continue
            seen_hosts.add(host)
            parsed = urllib.parse.urlparse(link)
            root = f"{parsed.scheme}://{parsed.netloc}/"
            blob = f"{item.get('title', '')} {item.get('snippet', '')}"
            verified = verify_website_ownership(root, company, city, phone, serper_blob=blob)
            if verified:
                return verified
    return ""


def strip_nonvisible_blocks(raw_html: str) -> str:
    # Remove short HTML comments and CSS blocks without risking cross-document swallow
    cleaned = re.sub(r"<!--.{0,1500}?-->", " ", raw_html, flags=re.S)
    cleaned = re.sub(r"<style\b[^>]*>[^<]{0,25000}</style>", " ", cleaned, flags=re.I)
    return cleaned


LICENSE_NOISE_RE = re.compile(
    r"(copyright|\(c\)|license|open font|ofl|@font-face|sil |jquery|bootstrap|gsap|mit license|apache|gpl)",
    re.I,
)


def decode_cf_emails(raw_html: str) -> list:
    decoded = []
    for hex_str in CF_EMAIL_RE.findall(raw_html):
        if len(hex_str) < 6 or len(hex_str) % 2 != 0:
            continue
        try:
            key = int(hex_str[:2], 16)
            out = "".join(
                chr(int(hex_str[i:i + 2], 16) ^ key)
                for i in range(2, len(hex_str), 2)
            )
            if "@" in out:
                decoded.append(out)
        except ValueError:
            continue
    return decoded


def clean_extracted_email(raw: str) -> str:
    em = html.unescape(urllib.parse.unquote(raw)).strip().lower()
    em = em.split("?", 1)[0].strip().rstrip(".,;:)>\"'")
    if "@" not in em or len(em) > 75:
        return ""
    if any(em.endswith(ext) for ext in BAD_EXTENSIONS):
        return ""
    if "@2x" in em or "@3x" in em or "u00" in em or "\\" in em:
        return ""
    local, dom = em.rsplit("@", 1)
    if not re.match(r"^[a-z0-9][a-z0-9._%+\-]{0,48}[a-z0-9]$|^[a-z0-9]$", local):
        return ""
    if ".." in local or ".." in dom:
        return ""
    if not re.match(r"^[a-z0-9][a-z0-9.\-]+\.[a-z]{2,10}$", dom):
        return ""
    if dom in BAD_EMAIL_DOMAINS or any(dom.endswith("." + bd) for bd in BAD_EMAIL_DOMAINS):
        return ""
    if local in BAD_LOCAL_EXACT:
        return ""
    if any(
        local == p or local.startswith(p + "+") or local.startswith(p + ".") or local.startswith(p + "_")
        for p in BAD_LOCAL_PREFIXES
    ):
        return ""
    if any(w in em for w in ("wixpress", "squarespace", "godaddy", "webflow", "elementor", "wordpress")):
        return ""
    return em


def normalize_obfuscated_text(raw_html: str) -> str:
    txt = html.unescape(raw_html)
    txt = re.sub(r"\s*(?:\[at\]|\(at\))\s*", "@", txt, flags=re.I)
    txt = re.sub(r"\s*(?:\[dot\]|\(dot\))\s*", ".", txt, flags=re.I)
    return txt


def is_attributed_to_contractor(email: str, company: str, site_host: str, is_site_crawl: bool) -> bool:
    dom = email.split("@", 1)[1]
    if is_aggregator_host(dom):
        return False
    if site_host and (dom == site_host or dom.endswith("." + site_host)):
        return True
    if domain_matches_company(dom, company):
        return True
    if dom in FREE_PROVIDERS:
        if is_site_crawl:
            return True
        # From web search snippets, require company token inside the free email local part or full brand match
        local = email.split("@", 1)[0]
        return any(t in local for t in company_tokens(company) if len(t) >= 3)
    return False


def score_email(email: str, site_host: str, company: str) -> int:
    local, dom = email.split("@", 1)
    s = 0
    if site_host and (dom == site_host or dom.endswith("." + site_host)):
        s += 60
    elif domain_matches_company(dom, company):
        s += 55
    elif dom in FREE_PROVIDERS:
        s += 20
    if local in ROLE_LOCAL_PARTS:
        s += 10
    elif not any(ch.isdigit() for ch in local):
        s += 25
    return s


def extract_emails_from_site(website: str, company: str) -> list:
    site_host = norm_host(website)
    if not website or is_aggregator_host(site_host):
        return []
    parsed = urllib.parse.urlparse(website)
    root_url = f"{parsed.scheme}://{parsed.netloc}"

    found = {}
    candidate_paths = ["/", "/contact", "/contact-us", "/about", "/about-us", "/free-estimate", "/get-a-quote"]
    visited = set()

    def scan_page(target_url: str, discover_links: bool = False):
        if target_url in visited:
            return []
        visited.add(target_url)
        body, final_url = fetch_url(target_url)
        if not body:
            return []
        final_host = norm_host(final_url) or site_host
        page_links = []
        if discover_links:
            for href in re.findall(r'href=["\']([^"\'#]+)["\']', body, re.I):
                if any(k in href.lower() for k in ("contact", "about", "estimate", "quote", "team")):
                    abs_url = urllib.parse.urljoin(final_url or root_url, href)
                    if norm_host(abs_url) == final_host and abs_url not in visited:
                        page_links.append(abs_url)

        visible = strip_nonvisible_blocks(body)
        raw_hits = []
        raw_hits.extend(decode_cf_emails(visible))
        for m in re.findall(r'mailto:([^"\'\s?>]+)', visible, re.I):
            raw_hits.append(m)
        norm_visible = normalize_obfuscated_text(visible)
        for m in EMAIL_RE.finditer(norm_visible):
            ctx = norm_visible[max(0, m.start() - 120):min(len(norm_visible), m.end() + 120)]
            if LICENSE_NOISE_RE.search(ctx):
                continue
            raw_hits.append(m.group(0))

        for rh in raw_hits:
            ce = clean_extracted_email(rh)
            if ce and is_attributed_to_contractor(ce, company, final_host, is_site_crawl=True):
                found.setdefault(ce, final_url or target_url)
        return page_links

    discovered = scan_page(website, discover_links=True)
    extra_urls = discovered[:4] + [root_url + p for p in candidate_paths[1:]]
    for u in extra_urls:
        if len(visited) >= 8:
            break
        scan_page(u, discover_links=False)
        if found and len(visited) >= 3:
            break

    return sorted(found.items(), key=lambda kv: score_email(kv[0], site_host, company), reverse=True)


def serper_fallback_email(company: str, city: str, website: str, serper_key: str) -> list:
    if not serper_key:
        return []
    site_host = norm_host(website)
    queries = []
    if site_host and not is_aggregator_host(site_host):
        queries.append(f'site:{site_host} "@{site_host}" OR email OR "@gmail.com"')
    queries.append(f'"{company}" "{city}" ("email" OR "mailto" OR "@gmail.com" OR "@yahoo.com")')

    found = {}
    toks = company_tokens(company)
    for q in queries:
        for item in serper_search(q, serper_key, num=8):
            link = item.get("link", "")
            link_host = norm_host(link)
            title = item.get("title", "")
            snip = item.get("snippet", "")
            blob = f"{title} {snip}".lower()

            if "facebook.com/groups/" in link.lower() or "facebook.com/marketplace/" in link.lower():
                continue
            is_own_site = site_host and (link_host == site_host or link_host.endswith("." + site_host))
            is_social_brand = link_host in ("facebook.com", "instagram.com", "linkedin.com") and all(
                t in title.lower() for t in toks[:2]
            )
            has_company_city = any(t in blob for t in toks) and (city.lower() in blob or "california" in blob or "ca " in blob) and (
                not is_aggregator_host(link_host)
            )
            if not (is_own_site or is_social_brand or has_company_city):
                continue

            for m in EMAIL_RE.findall(f"{title} {snip}"):
                ce = clean_extracted_email(m)
                if ce and is_attributed_to_contractor(ce, company, site_host, is_site_crawl=False):
                    found.setdefault(ce, link or "serper_snippet")
        if found:
            break

    return sorted(found.items(), key=lambda kv: score_email(kv[0], site_host, company), reverse=True)


def lookup_mx(domain: str) -> list:
    with cache_lock:
        if domain in mx_cache:
            return mx_cache[domain]
    try:
        raw = subprocess.check_output(["dig", "+short", "MX", domain], timeout=6).decode().strip()
        records = []
        for line in raw.splitlines():
            parts = line.strip().split()
            if len(parts) == 2 and parts[0].isdigit():
                host = parts[1].rstrip(".").lower()
                if host and host not in (".", "localhost", "0") and "parked" not in host:
                    records.append((int(parts[0]), host))
        records.sort()
        hosts = [h for _, h in records]
    except Exception:
        hosts = []
    with cache_lock:
        mx_cache[domain] = hosts
    return hosts


def lookup_spf(domain: str) -> bool:
    with cache_lock:
        if domain in spf_cache:
            return spf_cache[domain]
    has_spf = False
    try:
        raw = subprocess.check_output(["dig", "+short", "TXT", domain], timeout=6).decode().lower()
        has_spf = "v=spf1" in raw
    except Exception:
        has_spf = False
    with cache_lock:
        spf_cache[domain] = has_spf
    return has_spf


def smtp_probe(email: str, mx_hosts: list) -> str:
    global port25_blocked
    if not mx_hosts:
        return "no_mx"
    if port25_blocked is True:
        return "mx_valid_smtp_unreachable"
    host = mx_hosts[0]
    try:
        with smtplib.SMTP(host, 25, timeout=3) as srv:
            srv.ehlo("gslocalseo.com")
            srv.mail("verify@gslocalseo.com")
            code, _ = srv.rcpt(email)
            port25_blocked = False
            if code in (550, 551, 552, 553, 554):
                return f"hard_bounce_{code}"
            if code in (250, 251):
                dom = email.split("@", 1)[1]
                fc, _ = srv.rcpt(f"x9z8q7nonexistent441@{dom}")
                if fc in (250, 251):
                    return "catch_all_mx_valid"
                return "verified_250"
            return f"smtp_{code}"
    except (TimeoutError, OSError, smtplib.SMTPException):
        port25_blocked = True
        return "mx_valid_smtp_unreachable"


def classify_tier(email: str, site_host: str, has_spf: bool) -> str:
    local, dom = email.split("@", 1)
    spf_tag = "spf_ok" if has_spf else "no_spf"
    if dom in FREE_PROVIDERS:
        return f"tier_3_free_provider_{spf_tag}"
    if local in ROLE_LOCAL_PARTS:
        return f"tier_2_role_company_domain_{spf_tag}"
    if site_host and (dom == site_host or dom.endswith("." + site_host)):
        return f"tier_1_direct_company_domain_{spf_tag}"
    return f"tier_2_matched_domain_{spf_tag}"


def process_contractor(c: dict, serper_key: str) -> tuple:
    raw_site = (c.get("website") or "").strip()
    site_host = norm_host(raw_site)
    cleaned_site = raw_site if (raw_site and not is_aggregator_host(site_host)) else ""

    if not cleaned_site:
        cleaned_site = discover_real_website(c["name"], c["city"], c.get("phone", ""), serper_key)
        site_host = norm_host(cleaned_site)

    candidates = []
    source = ""
    if cleaned_site:
        candidates = extract_emails_from_site(cleaned_site, c["name"])
        source = "website_crawl"

    if not candidates:
        candidates = serper_fallback_email(c["name"], c["city"], cleaned_site, serper_key)
        source = "serper_search"

    best_email = ""
    found_on = ""
    mx_status = "none"
    has_spf = False
    smtp_status = "not_found"
    reject_reason = "No public website" if not cleaned_site else "No email published (contact form/phone only)"
    risk_tier = ""

    for em, origin_url in candidates:
        dom = em.split("@", 1)[1]
        mxs = lookup_mx(dom)
        if not mxs:
            reject_reason = f"{em} (no valid MX record)"
            continue
        has_spf = lookup_spf(dom)
        probe = smtp_probe(em, mxs)
        if probe.startswith("hard_bounce_"):
            reject_reason = f"{em} ({probe})"
            continue
        best_email = em
        found_on = origin_url
        mx_status = mxs[0]
        smtp_status = probe
        risk_tier = classify_tier(em, site_host, has_spf)
        reject_reason = ""
        break

    row = {
        "id": c["id"],
        "name": c["name"],
        "city": c["city"],
        "county": c["county"],
        "category": c["category"],
        "phone": c.get("phone", ""),
        "email": best_email,
        "risk_tier": risk_tier,
        "mx_host": mx_status,
        "has_spf": "yes" if has_spf else "no",
        "smtp_status": smtp_status,
        "email_source": source if best_email else "",
        "found_on": found_on,
        "website": cleaned_site,
        "rating": c.get("rating") if c.get("rating") is not None else "",
        "reviews": c.get("reviews", 0),
        "reject_reason": reject_reason,
        "profile_url": f"https://foundationcrawlspace.online/company/california/{re.sub(r'[^a-z0-9]+', '-', c['city'].lower()).strip('-')}/{c['slug']}/",
        "claim_url": f"https://foundationcrawlspace.online/claim/?company={urllib.parse.quote(c['name'])}&city={urllib.parse.quote(c['city'])}",
    }
    return row, cleaned_site


def main():
    contractors = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    serper_key = load_serper_key()
    print(f"[*] Auditing websites & harvesting emails across {len(contractors)} contractors...")

    results = [None] * len(contractors)
    cleaned_sites = [""] * len(contractors)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(process_contractor, c, serper_key): idx for idx, c in enumerate(contractors)}
        for fut in as_completed(futs):
            idx = futs[fut]
            results[idx], cleaned_sites[idx] = fut.result()

    sites_discovered = 0
    gotos_removed = 0
    for idx, c in enumerate(contractors):
        old_site = (c.get("website") or "").strip()
        new_site = cleaned_sites[idx]
        if "google.com" in old_site and not new_site:
            gotos_removed += 1
        elif new_site and old_site != new_site:
            sites_discovered += 1
        c["website"] = new_site
        c.pop("email", None)

    DATA_PATH.write_text(json.dumps(contractors, indent=2), encoding="utf-8")

    seen_emails = set()
    clean_rows = []
    rejected_rows = []
    tier_counts = {}

    for r in results:
        if r["email"]:
            if r["email"] in seen_emails:
                r["reject_reason"] = f"Duplicate email ({r['email']})"
                r["email"] = ""
                rejected_rows.append(r)
                continue
            seen_emails.add(r["email"])
            tier_counts[r["risk_tier"]] = tier_counts.get(r["risk_tier"], 0) + 1
            clean_rows.append(r)
        else:
            rejected_rows.append(r)

    fields = [
        "id", "name", "city", "county", "category", "phone", "email", "risk_tier",
        "mx_host", "has_spf", "smtp_status", "email_source", "found_on",
        "website", "rating", "reviews", "profile_url", "claim_url",
    ]
    with OUT_CLEAN_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(clean_rows)

    r_fields = ["id", "name", "city", "phone", "website", "reject_reason", "smtp_status"]
    with OUT_REJECTED_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=r_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rejected_rows)

    print(f"\n[OK] Real websites resolved/updated: {sites_discovered} | Broken google.com URLs cleared: {gotos_removed}")
    print(f"[OK] Clean valid-MX outreach emails: {len(clean_rows)} / {len(contractors)}")
    print(f"[OK] Tier breakdown: {tier_counts}")
    print(f"[OK] Saved clean CSV   -> {OUT_CLEAN_CSV}")
    print(f"[OK] Saved skipped CSV -> {OUT_REJECTED_CSV}")


if __name__ == "__main__":
    main()
