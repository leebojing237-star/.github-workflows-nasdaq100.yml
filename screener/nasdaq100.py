import sys
from datetime import datetime, timezone

from fmp import fmp_get, fmp_get_try, first, pick, as_num
from sheets import get_sheet, write_rows

# TODO: replace with your actual Nasdaq-100 list, or scrape it fresh each run
TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA"]

HEADERS = [
    "asof", "ticker", "companyName",
    "price", "marketCap", "beta", "avgVolume",
    "sector", "industry",
    "pe", "priceToSalesRatio", "pbRatio", "priceToFreeCashFlowRatio",
    "roic", "roe", "roa",
    "grossProfitMargin", "operatingProfitMargin", "netProfitMargin",
    "revenueGrowth", "epsgrowth",
    "debtToEquity", "currentRatio",
    "dividendYield", "payoutRatio",
    "change3mPct", "change6mPct", "change12mPct",
    "epsTTM", "evEbitda", "peg",
    "altmanZ", "piotroski",
    "fetch_status",
]


def fetch_one(sym, asof):
    status = "OK"
    profile = first(fmp_get("profile", symbol=sym))
    quote = first(fmp_get("quote", symbol=sym))
    ratios = first(fmp_get("ratios-ttm", symbol=sym))
    km = first(fmp_get("key-metrics-ttm", symbol=sym))
    growth = first(fmp_get("financial-growth", symbol=sym, limit=1))
    scores = first(fmp_get("financial-scores", symbol=sym))
    change = first(fmp_get_try(["stock-price-change", "quote-change"], symbol=sym))

    for o in (profile, quote, ratios, km, growth, scores, change):
        if isinstance(o, dict) and o.get("__error"):
            status = "PARTIAL"

    price = as_num(pick(quote, ["price"])) or as_num(pick(profile, ["price"]))
    pe = as_num(pick(quote, ["pe"])) or as_num(pick(ratios, ["priceToEarningsRatioTTM"]))

    return [
        asof, sym, pick(profile, ["companyName"]),
        price,
        as_num(pick(quote, ["marketCap"])) or as_num(pick(profile, ["marketCap", "mktCap"])),
        as_num(pick(profile, ["beta"])),
        as_num(pick(quote, ["avgVolume", "averageVolume"])),
        pick(profile, ["sector"]),
        pick(profile, ["industry"]),
        pe,
        as_num(pick(ratios, ["priceToSalesRatioTTM"])),
        as_num(pick(ratios, ["priceToBookRatioTTM"])),
        as_num(pick(ratios, ["priceToFreeCashFlowRatioTTM", "priceToFreeCashFlowsRatioTTM"])),
        as_num(pick(km, ["returnOnInvestedCapitalTTM", "roicTTM"])),
        as_num(pick(ratios, ["returnOnEquityTTM"])),
        as_num(pick(ratios, ["returnOnAssetsTTM"])),
        as_num(pick(ratios, ["grossProfitMarginTTM"])),
        as_num(pick(ratios, ["operatingProfitMarginTTM"])),
        as_num(pick(ratios, ["netProfitMarginTTM"])),
        as_num(pick(growth, ["revenueGrowth"])),
        as_num(pick(growth, ["epsgrowth", "epsGrowth"])),
        as_num(pick(ratios, ["debtToEquityRatioTTM", "debtEquityRatioTTM"])),
        as_num(pick(ratios, ["currentRatioTTM"])),
        as_num(pick(ratios, ["dividendYieldTTM"])),
        as_num(pick(ratios, ["payoutRatioTTM", "dividendPayoutRatioTTM"])),
        as_num(pick(change, ["3M"])),
        as_num(pick(change, ["6M"])),
        as_num(pick(change, ["1Y"])),
        as_num(pick(quote, ["eps"])),
        as_num(pick(km, ["evToEBITDATTM", "enterpriseValueOverEBITDATTM"])) or as_num(pick(ratios, ["enterpriseValueMultipleTTM"])),
        as_num(pick(ratios, ["priceToEarningsGrowthRatioTTM", "pegRatioTTM", "priceEarningsToGrowthRatioTTM"])),
        as_num(pick(scores, ["altmanZScore"])),
        as_num(pick(scores, ["piotroskiScore"])),
        status,
    ]


def main():
    asof = datetime.now(timezone.utc).isoformat()
    rows = []
    errors = 0

    for sym in TICKERS:
        try:
            rows.append(fetch_one(sym, asof))
        except Exception as e:
            errors += 1
            print(f"ERROR on {sym}: {e}", file=sys.stderr)
            row = [""] * len(HEADERS)
            row[0], row[1], row[-1] = asof, sym, f"ERR: {e}"
            rows.append(row)

    ws = get_sheet("FMP")
    write_rows(ws, HEADERS, rows)
    print(f"Done. {len(rows)} rows written, {errors} errors.")


if __name__ == "__main__":
    main()
