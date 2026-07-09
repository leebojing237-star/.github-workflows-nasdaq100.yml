import os
import time
import requests

FMP_BASE = "https://financialmodelingprep.com/stable"
API_KEY = os.environ["FMP_API_KEY"]
THROTTLE_SEC = 0.12  # Premium = 750/min; matches your Apps Script throttle


def fmp_get(slug, **params):
    params["apikey"] = API_KEY
    resp = requests.get(f"{FMP_BASE}/{slug}", params=params, timeout=30)
    time.sleep(THROTTLE_SEC)
    if resp.status_code == 429:
        raise RuntimeError("FMP rate limited")
    if resp.status_code != 200:
        return {"__error": f"HTTP {resp.status_code}"}
    try:
        return resp.json()
    except ValueError:
        return {"__error": "parse"}


def fmp_get_try(slugs, **params):
    for slug in slugs:
        j = fmp_get(slug, **params)
        if not (isinstance(j, dict) and j.get("__error")):
            return j
    return {"__error": "all-slugs-failed"}


def first(j):
    """FMP endpoints return either a list or a dict — normalize to a dict."""
    if isinstance(j, list):
        return j[0] if j else {}
    return j or {}


def pick(d, keys, default=""):
    """Try several possible field names (FMP renames fields between versions)."""
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return default


def as_num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return ""
