"""Step 2. The physical traces: surviving milestones, mileposts and toll houses.

Sources (read in place, retrieved 28 October 2026 via QLever):
  ../../_data12/wd_osm_bundle12.json.gz
    wd_turnpike: Wikidata items in the UK of class milestone, toll house, toll bridge, toll road, toll gate,
      turnpike road or turnpike trust (CC0). One row per item x value, deduplicated by item.
    osm_tollhouses: OpenStreetMap features inside the UK tagged historic=milestone/milepost/toll_house/
      turnpike/toll_gate or barrier=toll_booth (ODbL, (c) OpenStreetMap contributors).
  ../../how-roman-is-your-road/data/counties.geojson (GB counties and unitary areas, from ONS boundaries, OGL)
  ../../how-roman-is-your-road/data/osm_aroads.json.gz (OSM ways with an A-road ref, ODbL)

An OSM feature within 40 m of a Wikidata item of the same broad kind is treated as the same object.
Wikidata inception values of exactly 1701, 1801 or 1901 are century-precision dates ("18th century" etc.) in the
listing texts; other years are taken as given.
Writes ../data/traces.csv, ../data/county_density.csv, ../data/inscriptions.csv and ../data/_traces.json.
"""
import csv, gzip, io, json, math, os, re, collections
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, Point, LineString
from shapely.strtree import STRtree
from shapely.ops import transform as stransform

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); H = os.path.join(ROOT, "..")
TO = Transformer.from_crs(4326, 27700, always_xy=True)
B = json.load(gzip.open(os.path.join(H, "_data12", "wd_osm_bundle12.json.gz")))["results"]


def tsv(k):
    return list(csv.DictReader(io.StringIO(B[k]["tsv"]), delimiter="\t"))


def strip(v):
    v = v.strip()
    m = re.match(r'^"(.*)"(@\w+)?$', v, re.S)
    return m.group(1) if m else v


def pt(w):
    m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", w or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


def centroid(w):
    nums = re.findall(r"(-?\d+\.\d+) (-?\d+\.\d+)", w or "")
    if not nums: return None
    a = np.array([[float(x), float(y)] for x, y in nums]); return float(a[:, 0].mean()), float(a[:, 1].mean())


HER = {"Q15700834": "Grade II listed", "Q15700831": "Grade II* listed", "Q15700818": "Grade I listed",
       "Q10729142": "Category B listed (Scotland)", "Q10729125": "Category C listed (Scotland)",
       "Q10729054": "Category A listed (Scotland)", "Q219538": "scheduled monument",
       "Q71056157": "Grade II listed (Northern Ireland)"}

if __name__ == "__main__":
    # ---- Wikidata
    items = {}
    for r in tsv("wd_turnpike"):
        q = strip(r["?s"]).rsplit("/", 1)[-1].rstrip(">")
        z = items.setdefault(q, dict(src="wikidata", id=q, label=strip(r["?label"]).replace("@en", ""), coord=pt(r["?coord"]),
                                     cls=set(), inc=set(), her=set()))
        if r["?clsl"]: z["cls"].add(strip(r["?clsl"]).replace("@en", ""))
        if r["?inc"]: z["inc"].add(strip(r["?inc"])[:4])
        if r["?herit"]: z["her"].add(strip(r["?herit"]).rsplit("/", 1)[-1].rstrip(">"))
    T = []
    for z in items.values():
        if not z["coord"]: continue
        cls = z["cls"]
        kind = "toll house" if "tollhouse" in cls or "toll house" in cls else ("milestone" if "milestone" in cls else
               "toll bridge" if "toll bridge" in cls else "toll road" if "toll road" in cls else "other")
        if kind in ("toll bridge", "toll road", "other"):
            continue
        lab = z["label"]
        if kind == "milestone" and re.match(r"(?i)\s*mile\s*post", lab): kind = "milepost"
        if kind == "milestone" and re.match(r"(?i)\s*guide\s*(stone|post)", lab): kind = "guide stone"
        yrs = sorted(int(y) for y in z["inc"] if y.isdigit())
        y = yrs[0] if yrs else None
        cent = None
        if y in (1601, 1701, 1801, 1901, 2001): cent, y = (y - 1) // 100 + 1, None
        her = sorted(HER.get(h, "other designation") for h in z["her"])
        T.append(dict(src="wikidata", id=z["id"], kind=kind, name=lab, lon=z["coord"][0], lat=z["coord"][1], year=y, century=cent,
                      listed=her[0] if her else "", inscription="", turnpike_in_name=int("urnpike" in lab)))
    nwd = len(T)
    # ---- OSM
    osm = []
    for r in tsv("osm_tollhouses"):
        h = strip(r["?historic"]); w = strip(r["?wkt"])
        c = pt(w) if w.startswith("POINT") else centroid(w)
        if not c: continue
        kind = {"milestone": "milestone", "milepost": "milepost", "toll_house": "toll house", "turnpike": "toll house",
                "toll_gate": "toll house"}.get(h, "toll house")
        st = strip(r["?start"]); m = re.search(r"(1[5-9]\d\d)", st)
        osm.append(dict(src="osm", id=strip(r["?osm"]).replace("https://www.openstreetmap.org/", "").strip("<>"), kind=kind,
                        name=strip(r["?name"]), lon=c[0], lat=c[1], year=int(m.group(1)) if m else None, century=None,
                        listed=strip(r["?heritage"]) and "heritage tag" or "", inscription=strip(r["?inscription"]).replace("\\n", " / "),
                        turnpike_in_name=0))
    # dedupe OSM against Wikidata
    for t in T + osm:
        t["x"], t["y"] = TO.transform(t["lon"], t["lat"])
    wdxy = np.array([[t["x"], t["y"]] for t in T])
    from scipy.spatial import cKDTree
    kd = cKDTree(wdxy)
    dup = 0
    for o in osm:
        d, i = kd.query([o["x"], o["y"]])
        same = (o["kind"] in ("milestone", "milepost", "guide stone")) == (T[i]["kind"] in ("milestone", "milepost", "guide stone"))
        if d < 40 and same:
            dup += 1
            if o["inscription"] and not T[i]["inscription"]: T[i]["inscription"] = o["inscription"]
            continue
        T.append(o)
    print("wikidata", nwd, "osm", len(osm), "osm duplicates", dup, "total", len(T))
    # ---- counties and nations
    G = json.load(open(os.path.join(H, "how-roman-is-your-road", "data", "counties.geojson")))
    proj = lambda x, y, z=None: TO.transform(x, y)
    polys = [stransform(proj, shape(f["geometry"])) for f in G["features"]]
    meta = [f["properties"] for f in G["features"]]
    tree = STRtree(polys)
    for t in T:
        p = Point(t["x"], t["y"]); hit = None
        for i in tree.query(p):
            if polys[i].contains(p): hit = i; break
        if hit is None:
            d = [polys[i].distance(p) for i in tree.query(p.buffer(3000))]
            cand = list(tree.query(p.buffer(3000)))
            if cand: hit = cand[int(np.argmin(d))]
        t["county"] = meta[hit]["county"] if hit is not None else ""
        t["nation"] = meta[hit]["nation"] if hit is not None else "Northern Ireland"
    # ---- distance to A-roads
    A = json.load(gzip.open(os.path.join(H, "how-roman-is-your-road", "data", "osm_aroads.json.gz")))
    lines = []
    for w in A:
        c = w[5]; pts = [TO.transform(c[i] / 1e5, c[i + 1] / 1e5) for i in range(0, len(c), 2)]
        if len(pts) >= 2: lines.append(LineString(pts))
    at = STRtree(lines)
    for t in T:
        if t["nation"] == "Northern Ireland": t["aroad_m"] = None; continue
        p = Point(t["x"], t["y"]); c = at.query(p.buffer(2000))
        t["aroad_m"] = round(min(lines[i].distance(p) for i in c)) if len(c) else None
    # ---- write traces
    cols = ["src", "id", "kind", "name", "lat", "lon", "nation", "county", "year", "century", "listed", "turnpike_in_name", "aroad_m", "inscription"]
    with open(os.path.join(ROOT, "data", "traces.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for t in sorted(T, key=lambda t: (t["nation"], t["county"], t["lat"])):
            r = {k: t.get(k, "") for k in cols}; r["lat"] = round(t["lat"], 5); r["lon"] = round(t["lon"], 5)
            w.writerow(r)
    # ---- county density
    area = {m["county"]: polys[i].area / 1e6 for i, m in enumerate(meta)}
    nat = {m["county"]: m["nation"] for m in meta}
    cnt = collections.Counter(t["county"] for t in T if t["kind"] in ("milestone", "milepost"))
    th = collections.Counter(t["county"] for t in T if t["kind"] == "toll house")
    with open(os.path.join(ROOT, "data", "county_density.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["county", "nation", "area_km2", "milestones_and_mileposts", "toll_houses", "per_100km2"])
        for c in sorted(area, key=lambda c: -cnt[c] / area[c]):
            w.writerow([c, nat[c], round(area[c]), cnt[c], th[c], round(cnt[c] / area[c] * 100, 2)])
    # ---- inscriptions: destinations named with a distance
    ins = []
    for t in T:
        s = t["inscription"]
        if not s: continue
        for m in re.finditer(r"([A-Z][A-Za-z'\.&\- ]{2,30}?)[\s,:/]+(\d{1,3})\s*([¼½¾]|1/4|1/2|3/4)?\s*(?:MILES?|Miles?|miles?|M\b)", s):
            nm = re.sub(r"(?i)^(to|from)\s+", "", m.group(1)).strip(" .,/").upper()
            if len(nm) < 3 or nm in ("MILES", "MILE"): continue
            ins.append(dict(trace_id=t["id"], place=nm, miles=int(m.group(2)), lat=round(t["lat"], 5), lon=round(t["lon"], 5)))
    with open(os.path.join(ROOT, "data", "inscriptions.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["trace_id", "place", "miles", "lat", "lon"]); w.writeheader(); w.writerows(ins)
    json.dump(dict(n_wikidata=nwd, n_osm=len(osm), osm_dups=dup, n_total=len(T)), open(os.path.join(ROOT, "data", "_traces.json"), "w"))
    print(collections.Counter(t["kind"] for t in T)); print(collections.Counter(t["nation"] for t in T))
    print("inscription destinations", len(ins), collections.Counter(i["place"] for i in ins).most_common(15))
