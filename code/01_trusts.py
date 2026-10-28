"""Step 1. Build a gazetteer of English turnpike trusts and place the towns their names mention.

Sources
  Wikipedia's eight regional lists of turnpike trusts (CC BY-SA 4.0):
  - "Turnpike trusts in South East England": wikitext read from ../../_data12/wikipedia_batch12b.json.gz
    (English Wikipedia API, retrieved 28 October 2026).
  - The seven other regional lists (East Midlands, East of England, West Midlands, North East, North West,
    Yorkshire, South West): rows transcribed with an automated web reader on 28 October 2026, kept verbatim in
    ../data/raw/trusts_*.txt as "County | Trust | Founded | Initial act short title".
  - ../data/raw/check_se_webfetch.txt: Berkshire and Kent rows read the same way from the South East list, used
    only to measure how faithful the web reader is against the wikitext held on disk.
  OS Open Names (OGL v3) for placing the towns named in each trust.

Each trust row keeps the region, county, trust name(s), founding year (the year of its first act as given in the
list) and the short title of that act. Rows without a trust name (later acts of the trust above) are dropped.
The same trust listed under two counties is kept once (same name and year).

Placing: each trust name is split into place words ("Ashbourne and Yoxall Bridge" -> Ashbourne, Yoxall Bridge).
Each word is matched exactly (case, hyphens and punctuation ignored; "upon" read as "on") to an OS Open Names
populated place. Among several places of the same name, prefer one in the trust's region, then a city or town,
then the one nearest the trust's other placed words. A short list of old spellings is translated (ALIASES).

Writes ../data/trusts.csv, ../data/trust_places.csv (one row per trust x placed name),
../data/towns_named.csv (one row per OS place named in at least one trust) and ../data/_trusts_check.json.
"""
import csv, gzip, json, math, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); H = os.path.join(ROOT, "..")
RAW = os.path.join(ROOT, "data", "raw")

REGION_FILES = {"East Midlands": "trusts_east_midlands.txt", "East of England": "trusts_east_of_england.txt",
                "West Midlands": "trusts_west_midlands.txt", "North East": "trusts_north_east.txt",
                "Yorkshire": "trusts_yorkshire.txt", "North West": "trusts_north_west.txt",
                "South West": "trusts_south_west.txt"}
# OS Open Names regions (modern) in which a trust's places are expected to lie, by list region
OSREG = {"South East": {"South East", "London"}, "East of England": {"Eastern", "London"},
         "East Midlands": {"East Midlands"}, "West Midlands": {"West Midlands"}, "North East": {"North East"},
         "North West": {"North West"}, "Yorkshire": {"Yorkshire and the Humber"}, "South West": {"South West"}}
NEIGH = {"South East": {"Eastern", "South West", "West Midlands"}, "East of England": {"South East", "East Midlands"},
         "East Midlands": {"Eastern", "West Midlands", "Yorkshire and the Humber"},
         "West Midlands": {"East Midlands", "North West", "South West", "Wales"},
         "North East": {"Yorkshire and the Humber", "North West", "Scotland"},
         "North West": {"Yorkshire and the Humber", "North East", "West Midlands", "Wales", "East Midlands"},
         "Yorkshire": {"North East", "North West", "East Midlands"}, "South West": {"South East", "West Midlands", "Wales"}}
ALIASES = {"brighthelmston": "brighton", "sarum": "salisbury", "new sarum": "salisbury", "lynn": "kings lynn",
           "kirby kendall": "kendal", "kirkby kendal": "kendal", "ealand": "elland", "altringham": "altrincham",
           "severnoaks": "sevenoaks", "tunbridge wells": "royal tunbridge wells", "hull": "kingston upon hull",
           "aldburgh": "aldeburgh", "sailsbury": "salisbury", "heckmondwyke": "heckmondwike", "collumpton": "cullompton",
           "abberford": "aberford", "langset": "langsett", "newton bushell": "newton abbot", "ministerley": "minsterley",
           "whistable": "whitstable", "halsted": "halstead", "cranbrooke": "cranbrook", "tenderton": "tenterden",
           "prestwick": "prestwich", "eddlingham": "edlingham", "wanspeck": "", "great grimsby": "grimsby"}
DROP_WORDS = r"\b(turnpike trust|turnpike roads?|turnpike|trust|district|division|branch(es)?|roads?|lower|upper|first|second|north west|south|north|east|west|new road|old road|etc\.?|&c\.?|and branches|thru|military road)\b"


def norm(s):
    s = s.lower().replace("&", " and ").replace("'", "").replace("’", "")
    s = re.sub(r"[-.,()]", " ", s)
    s = re.sub(r"\bupon\b", "on", s)
    s = re.sub(r"\bsaint\b", "st", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_se_wikitext():
    d = json.load(gzip.open(os.path.join(H, "_data12", "wikipedia_batch12b.json.gz")))["articles"]
    t = d["Turnpike trusts in South East England"]["text"]
    rows, county = [], None
    lines = t.split("\n")
    for i, ln in enumerate(lines):
        m = re.match(r"^==\s*([^=]+?)\s*==\s*$", ln)
        if m:
            county = m.group(1)
            continue
        if "{{ubli" not in ln or not ln.startswith("|"):
            continue
        body = ln.split("{{ubli|", 1)[1]
        cut = min([i for i in (body.find("}}"), body.find("||")) if i >= 0] or [len(body)])
        names = "; ".join(x.strip() for x in body[:cut].split("|") if x.strip())
        rest = body[cut + 2:] if body[cut:cut + 2] == "}}" else body[cut:]  # some rows lack the closing braces
        if "||" not in rest:  # rowspan: year on next line
            rest = lines[i + 1]
        cells = [c.strip() for c in rest.split("||")]
        cells = [c for c in cells if c not in ("", "|")]
        year = ""
        for c in cells:
            mm = re.fullmatch(r"\|?\s*(1[6-8]\d\d)", c)
            if mm:
                year = mm.group(1); break
        act = re.search(r"\[\[([^\]|]*Act[^\]|]*)\]\]", rest)
        rows.append(dict(region="South East", county=county, trust=names, year=year,
                         act=act.group(1) if act else "", source="wikitext"))
    return rows


def parse_txt(region, fn):
    out = []
    for ln in open(os.path.join(RAW, fn), encoding="utf-8"):
        if ln.startswith("#") or "|" not in ln:
            continue
        c = [x.strip() for x in ln.rstrip("\n").split("|")]
        while len(c) < 4: c.append("")
        out.append(dict(region=region, county=c[0], trust=c[1], year=c[2] if re.fullmatch(r"1[6-8]\d\d", c[2]) else "",
                        act=c[3], source="web reader"))
    return out


def fidelity(se):
    chk = parse_txt("South East", "check_se_webfetch.txt")
    disk = {(r["county"], norm(r["trust"].split(";")[0])): r for r in se if r["county"] in ("Berkshire", "Kent")}
    n = len(chk); name_ok = year_ok = act_ok = 0; mism = []
    for r in chk:
        k = (r["county"], norm(r["trust"]))
        if k in disk:
            name_ok += 1; d = disk[k]
            if d["year"] == r["year"]: year_ok += 1
            else: mism.append([r["trust"], d["year"], r["year"]])
            if norm(d["act"]) == norm(r["act"]) or (not d["act"] and not r["act"]): act_ok += 1
    return dict(n_checked=n, n_disk_rows=len(disk), name_matched=name_ok, year_same=year_ok, act_same=act_ok,
                year_mismatches=mism)


def load_os():
    places = collections.defaultdict(list)
    with open(os.path.join(H, "osnames_gb.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["type"] != "populatedPlace":
                continue
            for nm in (r["name1"], r["name2"]):
                if nm:
                    places[norm(nm)].append(dict(name=r["name1"], lt=r["local_type"], lat=float(r["lat"]), lon=float(r["lon"]),
                                                 region=r["region"], county=r["county"] or r["district"], x=float(r["x"]), y=float(r["y"])))
    return places


def words(trust):
    out = []
    for alt in trust.split(";"):
        s = re.sub(r"\(.*?\)", " ", alt)
        s = re.sub(r"(?i)" + DROP_WORDS, " ", s)
        for p in re.split(r"(?i)\s+(?:and|to|or|through|thru|by)\s+|,|;|\s&\s|\s+-\s+", s):
            p = re.sub(r"\s+", " ", p).strip(" .")
            if len(p) >= 3 and not re.fullmatch(r"(?i)(of|the|in|on|at|etc)", p):
                out.append(p)
    seen, res = set(), []
    for p in out:
        if norm(p) not in seen:
            seen.add(norm(p)); res.append(p)
    return res


RANK = {"City": 0, "Town": 0, "Village": 1, "Suburban Area": 2, "Hamlet": 3, "Other Settlement": 3}


def place_trust(t, OS):
    cands = []
    for w in words(t["trust"]):
        k = norm(w); k = norm(ALIASES[k]) if ALIASES.get(k) else ("" if k in ALIASES else k)
        if not k: continue
        c = OS.get(k, [])
        if not c:
            continue
        reg = [p for p in c if p["region"] in OSREG[t["region"]]]
        nei = [p for p in c if p["region"] in NEIGH[t["region"]]]
        pool = reg or nei
        if not pool:
            continue
        cands.append((w, pool))
    placed = {}
    for w, pool in cands:  # unambiguous first
        best = sorted(pool, key=lambda p: RANK.get(p["lt"], 4))
        if len(pool) == 1 or (RANK.get(best[0]["lt"], 4) == 0 and sum(RANK.get(p["lt"], 4) == 0 for p in pool) == 1):
            placed[w] = (best[0], "unique" if len(pool) == 1 else "town")
    for _ in range(2):
        if not placed: break
        cx = sum(p["x"] for p, _ in placed.values()) / len(placed); cy = sum(p["y"] for p, _ in placed.values()) / len(placed)
        for w, pool in cands:
            if w in placed: continue
            best = min(pool, key=lambda p: (math.hypot(p["x"] - cx, p["y"] - cy) / 1000 + 15 * RANK.get(p["lt"], 4)))
            if math.hypot(best["x"] - cx, best["y"] - cy) < 60000:
                placed[w] = (best, "nearest to trust's other places")
    return placed


if __name__ == "__main__":
    se = parse_se_wikitext()
    chk = fidelity(se)
    print("fidelity check:", {k: v for k, v in chk.items() if k != "year_mismatches"}, chk["year_mismatches"][:5])
    rows = se[:]
    for reg, fn in REGION_FILES.items():
        rows += parse_txt(reg, fn)
    raw_n = len(rows)
    rows = [r for r in rows if r["trust"]]
    seen, trusts = set(), []
    for r in rows:
        k = (norm(r["trust"].split(";")[0]), r["year"])
        if k in seen: continue
        seen.add(k); trusts.append(r)
    print("rows", raw_n, "named", len(rows), "unique trusts", len(trusts))
    OS = load_os()
    tp = []
    for i, t in enumerate(trusts):
        t["id"] = i + 1
        pl = place_trust(t, OS)
        t["n_words"] = len(words(t["trust"])); t["n_placed"] = len(pl)
        t["placed"] = "; ".join(f'{w}={p["name"]}' for w, (p, _) in pl.items())
        for w, (p, how) in pl.items():
            tp.append(dict(trust_id=t["id"], trust=t["trust"], year=t["year"], region=t["region"], word=w, os_name=p["name"],
                           os_type=p["lt"], os_county=p["county"], lat=p["lat"], lon=p["lon"], how=how))
    with open(os.path.join(ROOT, "data", "trusts.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "region", "county", "trust", "year", "act", "source", "n_words", "n_placed", "placed"])
        w.writeheader(); [w.writerow({k: t[k] for k in w.fieldnames}) for t in trusts]
    with open(os.path.join(ROOT, "data", "trust_places.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(tp[0].keys())); w.writeheader(); w.writerows(tp)
    towns = {}
    for r in tp:
        k = (r["os_name"], r["lat"], r["lon"])
        z = towns.setdefault(k, dict(name=r["os_name"], os_type=r["os_type"], county=r["os_county"], lat=r["lat"], lon=r["lon"],
                                     region=r["region"], trusts=set(), years=[]))
        z["trusts"].add(r["trust_id"])
        if r["year"]: z["years"].append(int(r["year"]))
    with open(os.path.join(ROOT, "data", "towns_named.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["name", "os_type", "os_county", "list_region", "lat", "lon", "n_trusts", "first_trust_year", "trust_ids"])
        for z in sorted(towns.values(), key=lambda z: (min(z["years"]) if z["years"] else 9999, z["name"])):
            w.writerow([z["name"], z["os_type"], z["county"], z["region"], z["lat"], z["lon"], len(z["trusts"]),
                        min(z["years"]) if z["years"] else "", " ".join(map(str, sorted(z["trusts"])))])
    json.dump(dict(fidelity=chk, rows_read=raw_n, rows_named=len(rows), trusts=len(trusts)),
              open(os.path.join(ROOT, "data", "_trusts_check.json"), "w"), indent=1)
    print("trusts placed (>=1 name):", sum(t["n_placed"] > 0 for t in trusts), "places named:", len(towns))
