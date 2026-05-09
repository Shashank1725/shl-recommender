import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.shl.com"
CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def get_all_catalog_pages():
    pages = []
    page = 0
    while True:
        url = f"{CATALOG_URL}?start={page}&type=1"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")

        rows = soup.select("tr.js-target-company-row, div[data-type]")
        if not rows:
            rows = soup.select("table tbody tr")

        if not rows:
            break

        pages.append((url, soup))
        next_btn = soup.select_one("a[rel='next'], .pagination__next:not(.disabled)")
        if not next_btn:
            break
        page += 12
        time.sleep(0.5)

    return pages


def parse_assessments_from_soup(soup):
    assessments = []

    rows = soup.select("table tbody tr")
    for row in rows:
        try:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            link = cols[0].find("a")
            if not link:
                continue
            name = link.get_text(strip=True)
            href = link.get("href", "")
            url = BASE_URL + href if href.startswith("/") else href

            test_types = []
            for col in cols[1:]:
                if col.find("span", class_=lambda c: c and "yes" in c.lower()):
                    test_types.append(col.get("data-type", "").strip())
                img = col.find("img")
                if img and img.get("alt"):
                    test_types.append(img["alt"].strip())

            remote = bool(row.select_one("[class*='remote'], [data-remote='true']"))
            adaptive = bool(row.select_one("[class*='adaptive'], [data-adaptive='true']"))

            assessments.append({
                "name": name,
                "url": url,
                "test_types": [t for t in test_types if t],
                "remote_testing": remote,
                "adaptive": adaptive,
                "description": ""
            })
        except Exception as e:
            print(f"Row parse error: {e}")
            continue

    return assessments


def fetch_detail(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        desc_el = soup.select_one(
            ".product-catalogue-training-calendar__description, "
            ".product-detail__description, "
            "article p, "
            ".c-product-hero__description"
        )
        if desc_el:
            return desc_el.get_text(separator=" ", strip=True)[:500]
    except Exception:
        pass
    return ""


def scrape_catalog():
    print("SHL catalog scraping start...")
    
    all_assessments = []
    page = 0
    while True:
        url = f"{CATALOG_URL}?start={page}&type=1"
        print(f"Page {page} fetch kar raha hoon: {url}")
        
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"Fetch error: {e}")
            break

        rows = soup.select("table tbody tr")
        if not rows:
            print("Koi rows nahi mile, stop.")
            break

        batch = parse_assessments_from_soup(soup)
        if not batch:
            break

        all_assessments.extend(batch)
        print(f"  {len(batch)} assessments found on this page")

        next_link = soup.select_one("li.pagination__item--next a, a.pagination-next")
        if not next_link:
            break

        page += 12
        time.sleep(0.8)

    print(f"\nTotal {len(all_assessments)} assessments found. Descriptions fetching...")
    for i, a in enumerate(all_assessments[:50]):
        if a["url"].startswith("http"):
            a["description"] = fetch_detail(a["url"])
            print(f"  [{i+1}] {a['name']}: description fetched")
            time.sleep(0.3)

    with open("catalog.json", "w", encoding="utf-8") as f:
        json.dump(all_assessments, f, indent=2, ensure_ascii=False)

    print(f"\ncatalog.json saved with {len(all_assessments)} assessments!")
    return all_assessments


if __name__ == "__main__":
    data = scrape_catalog()
    print(f"\nDone! {len(data)} assessments scraped.")
