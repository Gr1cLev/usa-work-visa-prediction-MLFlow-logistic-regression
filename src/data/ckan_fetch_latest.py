import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=False)

DATA_GOV_API = os.getenv(
    "DATA_GOV_API_URL", "https://api.gsa.gov/technology/datagov/v3/action/package_search"
)


def search_oflc_lca_resources(year: str | None = None):
    q = "oflc performance data lca"
    api_key = os.getenv("DATAGOV_API_KEY")
    if not api_key:
        print(
            "[CKAN] DATAGOV_API_KEY missing. Skipping remote lookup and "
            "letting ingest() fallback to synthetic sample."
        )
        return []
    params = {"api_key": api_key, "q": q, "rows": 100}
    r = requests.get(DATA_GOV_API, params=params, timeout=60)
    r.raise_for_status()
    results = r.json().get("result", {}).get("results", [])
    resources = []
    for pkg in results:
        for rsc in pkg.get("resources", []):
            name = (rsc.get("name") or rsc.get("title") or "").lower()
            url = rsc.get("url") or ""
            if "lca" in name and ("disclosure" in name or "fy" in name):
                if (year is None) or (str(year) in name):
                    resources.append({"name": rsc.get("name"), "url": url})
    if year and not resources:
        return search_oflc_lca_resources(year=None)
    return resources

def pick_latest_url(resources):
    best, best_year = None, -1
    for r in resources:
        name = r.get("name") or ""
        m = re.search(r"FY(\d{4})", name, re.IGNORECASE)
        y = int(m.group(1)) if m else -1
        if y >= best_year:
            best_year = y
            best = r
    return best

if __name__ == "__main__":
    year = os.getenv("LCA_YEAR")
    res = search_oflc_lca_resources(year)
    latest = pick_latest_url(res) if res else None
    print(json.dumps({"picked": latest, "candidates": res[:5] if res else []}, indent=2))
