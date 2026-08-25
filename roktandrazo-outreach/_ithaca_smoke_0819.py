"""Ithaca NY browser_maps smoke test — DIRECT mode via existing provider."""
import os, sys, json
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
from discovery.providers.browser_maps import BrowserMapsProvider

prov = BrowserMapsProvider(mode="direct", headless=True)
print("configured:", prov.configured)

# smoke: 1 query family, Ithaca NY
page = prov.search_places("toy store", "Ithaca", "NY", page_size=10)
print(f"status={page.status} results={len(page.results)} error={page.error}")
for r in page.results[:8]:
    print(f"  - {r.business_name[:40]:<40} | {str(r.city or '')[:14]:<14} | {str(r.website or '')[:44]}")
