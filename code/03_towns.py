"""Step 3. Towns and their populations, with turnpike, milestone and railway measures.

Population panels (all read in place):
  A. Census panel: every English or Welsh place in the Wikidata extract of historic populations
     (../../_data9/wd_osm_bundle.json, "wd_historic_populations_tsv", CC0; figures are the census figures that
     Wikidata editors copied, mostly from A Vision of Britain through Time) with figures for 1801, 1831 and 1851,
     plus the 20 inland towns whose census series I transcribed from A Vision of Britain through Time for the
     seaside study (../../seaside-railways/data/populations.csv, group "inland").
  B. Big towns: the largest towns of England in 1801 and 1861 from Wikipedia's "List of towns and cities in England
     by historical population", as tabulated in ../../canal-mania/data/towns_historic.csv (London left out).

Measures for each place:
  trace_km: distance to the nearest surviving milestone, milepost or toll house (../data/traces.csv).
  named: the place is named in the title of a turnpike trust (../data/towns_named.csv, same name within 3 km),
         with the year of the first such trust and the number of trusts naming it.
  rail_year: the earliest Wikidata opening date of a railway station within 3 km
         (../../_data11/wd_osm_bundle11.json.gz, wd_stations, CC0), as in the seaside study.
  gis_year: ONLY if the turnpike road GIS of Rosevear, Bogart, Shaw-Taylor and Satchell (openICPSR 195126) is
         present in ../../_data12/turnpikes/: the earliest act year of any turnpike road within 1 km. See gis_years().
Writes ../data/panel.csv, ../data/big_towns.csv and ../data/_gis_status.json.
"""
import csv, glob, gzip, io, json, math, os, re, collections
import numpy as np
from scipy.spatial import cKDTree
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); H = os.path.join(ROOT, "..")
TO = Transformer.from_crs(4326, 27700, always_xy=True)
GIS_DIR = os.path.join(H, "_data12", "turnpikes")


def norm(s):
    s = s.lower().replace("&", " and ").replace("'", "")
    s = re.sub(r"[-.,()]", " ", s); s = re.sub(r"\bupon\b", "on", s)
    s = re.sub(r"\s+", " ", s).strip()
    return {"hull": "kingston on hull"}.get(s, s)


def gis_years(xy):
    """If the Rosevear et al. turnpike GIS is on disk, return for each (x, y) in British National Grid the earliest
    turnpike act year of any road line within 1 km, else None. Reads shapefiles with pyshp (or GeoJSON). The year
    field is the first attribute whose name contains 'year', 'date' or 'act' and holds four-digit years; the field
    used is reported in ../data/_gis_status.json so it can be checked against the dataset's codebook."""
    status = dict(present=os.path.isdir(GIS_DIR), used=False)
    if not status["present"]:
        return None, status
    from shapely.geometry import shape, LineString
    from shapely.strtree import STRtree
    geoms, years = [], []
    files = glob.glob(os.path.join(GIS_DIR, "**", "*.shp"), recursive=True) + glob.glob(os.path.join(GIS_DIR, "**", "*.geojson"), recursive=True)
    status["files"] = [os.path.relpath(f, GIS_DIR) for f in files]
    for fn in files:
        if fn.endswith(".shp"):
            import shapefile
            sf = shapefile.Reader(fn)
            fields = [f[0] for f in sf.fields[1:]]
            recs = [(dict(zip(fields, sr.record)), sr.shape.__geo_interface__) for sr in sf.iterShapeRecords()]
            prj = open(fn[:-4] + ".prj").read() if os.path.exists(fn[:-4] + ".prj") else ""
        else:
            g = json.load(open(fn)); recs = [(f["properties"], f["geometry"]) for f in g["features"]]
            fields = list(recs[0][0].keys()) if recs else []; prj = "EPSG:4326"
        yf = None
        for f in fields:
            if re.search(r"(?i)year|date|act", f):
                vals = [str(r[0].get(f, "")) for r in recs[:200]]
                if sum(bool(re.search(r"1[678]\d\d", v)) for v in vals) > 20:
                    yf = f; break
        status.setdefault("year_field", {})[os.path.basename(fn)] = yf
        if not yf:
            continue
        bng = "British_National_Grid" in prj or "27700" in prj or "OSGB" in prj
        for props, gi in recs:
            m = re.search(r"(1[678]\d\d)", str(props.get(yf, "")))
            if not m or not gi: continue
            geom = shape(gi)
            if not bng:
                from shapely.ops import transform
                geom = transform(lambda x, y, z=None: TO.transform(x, y), geom)
            geoms.append(geom); years.append(int(m.group(1)))
    if not geoms:
        return None, status
    tree = STRtree(geoms); out = []
    from shapely.geometry import Point
    for x, y in xy:
        p = Point(x, y); c = tree.query(p.buffer(1000))
        ys = [years[i] for i in c if geoms[i].distance(p) <= 1000]
        out.append(min(ys) if ys else None)
    status.update(used=True, n_lines=len(geoms))
    return out, status


if __name__ == "__main__":
    # traces
    T = list(csv.DictReader(open(os.path.join(ROOT, "data", "traces.csv"), encoding="utf-8")))
    T = [t for t in T if t["nation"] != "Northern Ireland"]
    txy = np.array([TO.transform(float(t["lon"]), float(t["lat"])) for t in T]); tk = cKDTree(txy)
    # named towns
    N = list(csv.DictReader(open(os.path.join(ROOT, "data", "towns_named.csv"), encoding="utf-8")))
    nxy = np.array([TO.transform(float(n["lon"]), float(n["lat"])) for n in N]); nk = cKDTree(nxy)
    # stations
    B = json.load(gzip.open(os.path.join(H, "_data11", "wd_osm_bundle11.json.gz")))["results"]
    st = []
    for r in csv.DictReader(io.StringIO(B["wd_stations"]["tsv"]), delimiter="\t"):
        m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", r["?coord"]); y = re.search(r"(1[89]\d\d|20\d\d)", r["?open"])
        if m and y: st.append((float(m.group(1)), float(m.group(2)), int(y.group(1))))
    sxy = np.array([TO.transform(a, b) for a, b, _ in st]); sk = cKDTree(sxy); syear = np.array([s[2] for s in st])

    def measures(name, lat, lon):
        x, y = TO.transform(lon, lat)
        d, _ = tk.query([x, y]); r = dict(trace_km=round(d / 1000, 3), traces_2km=len(tk.query_ball_point([x, y], 2000)))
        best = None
        for i in nk.query_ball_point([x, y], 3000):
            if norm(N[i]["name"]) == norm(name) or norm(name).startswith(norm(N[i]["name"]) + " ") or norm(N[i]["name"]).startswith(norm(name) + " "):
                best = N[i]; break
        r.update(named=int(best is not None), first_trust_year=int(best["first_trust_year"]) if best and best["first_trust_year"] else None,
                 n_trusts=int(best["n_trusts"]) if best else 0)
        ii = sk.query_ball_point([x, y], 3000)
        r["rail_year"] = int(syear[ii].min()) if ii else None
        r["x"], r["y"] = x, y
        return r

    # ---- panel A: Wikidata
    d9 = json.load(open(os.path.join(H, "_data9", "wd_osm_bundle.json")))
    by = collections.defaultdict(dict); lab = {}; co = {}
    for r in csv.DictReader(io.StringIO(d9["wd_historic_populations_tsv"]), delimiter="\t"):
        y = r["?date"][:4]
        if y in ("1801", "1811", "1821", "1831", "1841", "1851", "1861", "1871", "1881", "1891", "1901"):
            by[r["?item"]][int(y)] = float(r["?pop"])
        lab[r["?item"]] = r["?label"].replace("@en", ""); co[r["?item"]] = r["?coord"]
    rows = []
    for k, v in by.items():
        if not all(y in v for y in (1801, 1831, 1851)) or not co[k]: continue
        if lab[k] in ("England", "Wales", "London") or v[1801] > 100000: continue
        m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", co[k]); lon, lat = float(m.group(1)), float(m.group(2))
        rows.append(dict(place=lab[k], source="Wikidata " + k.strip("<>").rsplit("/", 1)[-1], lat=lat, lon=lon,
                         **{f"pop{y}": v.get(y) for y in (1801, 1811, 1821, 1831, 1841, 1851, 1881, 1901)}))
    # ---- panel A: VoB inland towns from the seaside study
    pp = list(csv.DictReader(open(os.path.join(H, "seaside-railways", "data", "populations.csv"), encoding="utf-8")))
    pl = {r["place"]: r for r in csv.DictReader(open(os.path.join(H, "seaside-railways", "data", "places.csv"), encoding="utf-8"))}
    vob = collections.defaultdict(dict)
    for r in pp:
        if r["group"] == "inland" and r["population"]:
            vob[r["place"]][int(r["year"])] = float(r["population"])
    for p, v in vob.items():
        if not all(y in v for y in (1801, 1831, 1851)): continue
        if any(abs(float(pl[p]["lat"]) - q["lat"]) < .02 and abs(float(pl[p]["lon"]) - q["lon"]) < .03 for q in rows): continue
        rows.append(dict(place=p, source="A Vision of Britain through Time (" + pl[p]["vob_unit"] + ")", lat=float(pl[p]["lat"]), lon=float(pl[p]["lon"]),
                         **{f"pop{y}": v.get(y) for y in (1801, 1811, 1821, 1831, 1841, 1851, 1881, 1901)}))
    n0 = len(rows)
    rows = [r for r in rows if r["pop1801"] >= 50]  # tiny extra-parochial places and fen hamlets give meaningless rates
    print("dropped (fewer than 50 people in 1801):", n0 - len(rows))
    for r in rows:
        r.update(measures(r["place"], r["lat"], r["lon"]))
    gy, gst = gis_years([(r["x"], r["y"]) for r in rows])
    for i, r in enumerate(rows):
        r["gis_year"] = gy[i] if gy else None
    cols = ["place", "source", "lat", "lon"] + [f"pop{y}" for y in (1801, 1811, 1821, 1831, 1841, 1851, 1881, 1901)] + \
           ["trace_km", "traces_2km", "named", "first_trust_year", "n_trusts", "rail_year", "gis_year"]
    with open(os.path.join(ROOT, "data", "panel.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({k: r.get(k) for k in cols})
    print("panel", len(rows), "named", sum(r["named"] for r in rows), "trace<1km", sum(r["trace_km"] < 1 for r in rows))
    # ---- panel B: big towns
    big = []
    for r in csv.DictReader(open(os.path.join(H, "canal-mania", "data", "towns_historic.csv"), encoding="utf-8")):
        if r["town"] == "London" or not r["pop1801"]: continue
        z = dict(town=r["town"], lat=float(r["lat"]), lon=float(r["lon"]), region=r["region"],
                 pop1801=float(r["pop1801"]), pop1861=float(r["pop1861"]) if r["pop1861"] else None,
                 pop1881=float(r["pop1881"]) if r["pop1881"] else None, pop1900=float(r["pop1900"]) if r["pop1900"] else None)
        z.update(measures(r["town"], z["lat"], z["lon"])); big.append(z)
    gy, _ = gis_years([(b["x"], b["y"]) for b in big])
    cols = ["town", "region", "lat", "lon", "pop1801", "pop1861", "pop1881", "pop1900", "trace_km", "traces_2km", "named", "first_trust_year", "n_trusts", "rail_year", "gis_year"]
    with open(os.path.join(ROOT, "data", "big_towns.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for i, b in enumerate(big): b["gis_year"] = gy[i] if gy else None; w.writerow({k: b.get(k) for k in cols})
    print("big towns", len(big), "with 1801", sum(1 for b in big), "named", sum(b["named"] for b in big))
    json.dump(gst, open(os.path.join(ROOT, "data", "_gis_status.json"), "w"), indent=1)
    print("GIS:", gst)
