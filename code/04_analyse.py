"""Step 4. All statistics. Writes ../data/results.json (every number used on the page, in the paper, the blog post
and the collage), ../data/page_data.json (compact data for the page), ../data/decades.csv, ../data/towns_today.csv.
Run after 01_trusts.py, 02_traces.py and 03_towns.py.
"""
import csv, json, math, os, re, collections
import numpy as np, pandas as pd
from scipy import stats
from scipy.spatial import cKDTree
import statsmodels.formula.api as smf
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); H = os.path.join(ROOT, "..")
DATA = os.path.join(ROOT, "data")
TO = Transformer.from_crs(4326, 27700, always_xy=True)
R = {}


def r3(x, d=3):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), d)


def norm(s):
    s = s.lower().replace("&", " and ").replace("'", "")
    s = re.sub(r"[-.,()]", " ", s); s = re.sub(r"\bupon\b", "on", s)
    return re.sub(r"\s+", " ", s).strip()


# ======================================================== trusts
tr = pd.read_csv(os.path.join(DATA, "trusts.csv"))
chk = json.load(open(os.path.join(DATA, "_trusts_check.json")))
tp = pd.read_csv(os.path.join(DATA, "trust_places.csv"))
tn = pd.read_csv(os.path.join(DATA, "towns_named.csv"))
ty = tr.dropna(subset=["year"]).copy(); ty["year"] = ty.year.astype(int)
R["trusts"] = dict(rows_read=chk["rows_read"], unique=len(tr), with_year=len(ty), regions=int(tr.region.nunique()),
                   placed=int((tr.n_placed > 0).sum()), placed_share=r3((tr.n_placed > 0).mean()),
                   first_year=int(ty.year.min()), first_name=ty.loc[ty.year.idxmin(), "trust"],
                   last_year=int(ty.year.max()), last_name=ty.loc[ty.year.idxmax(), "trust"],
                   median_year=int(ty.year.median()), q1=int(ty.year.quantile(.25)), q3=int(ty.year.quantile(.75)),
                   by1750=r3((ty.year < 1750).mean()), by1772=r3((ty.year <= 1772).mean()), by1800=r3((ty.year <= 1800).mean()),
                   n_1750_1772=int(((ty.year >= 1750) & (ty.year <= 1772)).sum()), share_1750_1772=r3(((ty.year >= 1750) & (ty.year <= 1772)).mean()),
                   after1830=int((ty.year > 1830).sum()), sussex_no_year=int(((tr.county == "Sussex") & tr.year.isna()).sum()),
                   fidelity=dict(n=chk["fidelity"]["n_disk_rows"], names=chk["fidelity"]["name_matched"], years=chk["fidelity"]["year_same"],
                                 acts=chk["fidelity"]["act_same"]))
dec = ty.assign(decade=(ty.year // 10) * 10).groupby("decade").size().reindex(range(1660, 1870, 10), fill_value=0)
R["decades"] = [dict(decade=int(d), n=int(n)) for d, n in dec.items()]
pk = dec.idxmax(); R["trusts"]["peak_decade"] = int(pk); R["trusts"]["peak_n"] = int(dec.max())
R["trusts"]["n_1750s"] = int(dec[1750]); R["trusts"]["n_1760s"] = int(dec[1760]); R["trusts"]["n_1820s"] = int(dec[1820])
R["trusts"]["n_1700s"] = int(dec[1700]); R["trusts"]["n_1840s_on"] = int(dec[dec.index >= 1840].sum())
dec.rename("trusts_founded").to_csv(os.path.join(DATA, "decades.csv"))
R["regions"] = []
for reg, g in ty.groupby("region"):
    ga = tr[tr.region == reg]
    R["regions"].append(dict(region=reg, n=int(len(g)), n_all=int(len(ga)), placed=r3((ga.n_placed > 0).mean()), median=int(g.year.median()), first=int(g.year.min()),
                             first_name=g.loc[g.year.idxmin(), "trust"], by1772=r3((g.year <= 1772).mean())))
R["regions"].sort(key=lambda d: d["median"])
nw = ty[ty.region == "North West"]; R["nw_1790_1829"] = r3(((nw.year >= 1790) & (nw.year <= 1829)).mean())
# wave from London: OS city/town named in a trust
LON = TO.transform(-0.1276, 51.5074)
tn["x"], tn["y"] = zip(*[TO.transform(lo, la) for lo, la in zip(tn.lon, tn.lat)])
tn["km_london"] = np.hypot(tn.x - LON[0], tn.y - LON[1]) / 1000
tt = tn[tn.os_type.isin(["City", "Town"]) & tn.first_trust_year.notna()].copy()
rho, p = stats.spearmanr(tt.km_london, tt.first_trust_year)
bands = [(0, 50), (50, 100), (100, 200), (200, 600)]
R["wave"] = dict(n_towns=len(tt), rho=r3(rho), p=float(p), bands=[dict(lo=a, hi=b, n=int(((tt.km_london >= a) & (tt.km_london < b)).sum()),
                 median=int(round(tt[(tt.km_london >= a) & (tt.km_london < b)].first_trust_year.median()))) for a, b in bands])
R["named"] = dict(places=len(tn), towns=int(tn.os_type.isin(["City", "Town"]).sum()),
                  hub_top=[dict(name=r.name, n=int(r.n_trusts), first=int(r.first_trust_year) if not math.isnan(r.first_trust_year) else None)
                           for r in tn.sort_values("n_trusts", ascending=False).head(12).itertuples()])
# example early places
ex = {}
for nm in ["Wadesmill", "Stilton", "Bath", "Bristol", "Liverpool", "Manchester", "Leeds", "Norwich", "Exeter", "Truro", "Kendal", "Carlisle", "Newcastle upon Tyne", "Penzance", "Ilfracombe"]:
    z = tn[tn.name == nm]
    if len(z): ex[nm] = dict(first=int(z.first_trust_year.min()) if z.first_trust_year.notna().any() else None, n=int(z.n_trusts.max()))
R["named"]["examples"] = ex

# ======================================================== traces
T = pd.read_csv(os.path.join(DATA, "traces.csv"), low_memory=False)
tj = json.load(open(os.path.join(DATA, "_traces.json")))
gb = T[T.nation != "Northern Ireland"]
R["traces"] = dict(total=len(T), wikidata=int((T.src == "wikidata").sum()), osm_only=int((T.src == "osm").sum()), osm_all=tj["n_osm"], osm_dups=tj["osm_dups"],
                   milestones=int((T.kind == "milestone").sum()), mileposts=int((T.kind == "milepost").sum()), guide=int((T.kind == "guide stone").sum()),
                   tollhouses=int((T.kind == "toll house").sum()), england=int((T.nation == "England").sum()), wales=int((T.nation == "Wales").sum()),
                   scotland=int((T.nation == "Scotland").sum()), ni=int((T.nation == "Northern Ireland").sum()),
                   listed=int((T.listed.fillna("").str.contains("listed|scheduled")).sum()),
                   grade2=int((T.listed == "Grade II listed").sum()),
                   c18=int((T.century == 18).sum()), c19=int((T.century == 19).sum()), c20=int((T.century == 20).sum()),
                   exact_year=int(T.year.notna().sum()),
                   exact_median=int(T.year.median()), exact_1750_1840=r3(((T.year >= 1750) & (T.year <= 1840)).sum() / T.year.notna().sum()),
                   turnpike_in_name=int(T.turnpike_in_name.sum()),
                   inscribed=int(T.inscription.notna().sum()))
a = gb.aroad_m.fillna(99999)
R["traces"].update(aroad_50=r3((a <= 50).mean()), aroad_200=r3((a <= 200).mean()), aroad_far=r3((a > 2000).mean()), aroad_median=int(a.median()))
dated = T.dropna(subset=["year"]); dated = dated[(dated.year >= 1700) & (dated.year < 1900)]
R["trace_decades"] = [dict(decade=int(d), n=int(n)) for d, n in dated.assign(d=(dated.year // 10) * 10).groupby("d").size().items()]
cd = pd.read_csv(os.path.join(DATA, "county_density.csv"))
eng = cd[cd.nation == "England"]
R["counties"] = dict(top=[dict(county=r.county, n=int(r.milestones_and_mileposts), d=r3(r.per_100km2, 1)) for r in eng[eng.area_km2 > 500].head(8).itertuples()],
                     bottom=[dict(county=r.county, n=int(r.milestones_and_mileposts), d=r3(r.per_100km2, 1)) for r in eng[eng.area_km2 > 500].tail(6).itertuples()],
                     england_density=r3(eng.milestones_and_mileposts.sum() / eng.area_km2.sum() * 100, 1),
                     wales_density=r3(cd[cd.nation == "Wales"].milestones_and_mileposts.sum() / cd[cd.nation == "Wales"].area_km2.sum() * 100, 1),
                     scotland_density=r3(cd[cd.nation == "Scotland"].milestones_and_mileposts.sum() / cd[cd.nation == "Scotland"].area_km2.sum() * 100, 1))
ins = pd.read_csv(os.path.join(DATA, "inscriptions.csv"))
R["inscriptions"] = dict(n=len(ins), stones=int(ins.trace_id.nunique()), top=[dict(place=k, n=int(v)) for k, v in ins.place.value_counts().head(6).items()])

# OS towns today: validation and "find your town"
os_t = pd.read_csv(os.path.join(H, "osnames_gb.tsv"), sep="\t", quoting=3, dtype=str, keep_default_na=False,
                   usecols=["name1", "type", "local_type", "lat", "lon", "x", "y", "county", "district", "region", "country"])
for c_ in ["lat", "lon", "x", "y"]: os_t[c_] = pd.to_numeric(os_t[c_], errors="coerce")
os_t = os_t[(os_t.type == "populatedPlace") & os_t.local_type.isin(["City", "Town"]) & os_t.country.isin(["England", "Wales"])].copy()
gxy = np.c_[TO.transform(gb.lon.values, gb.lat.values)]; gk = cKDTree(gxy)
d, _ = gk.query(np.c_[os_t.x, os_t.y]); os_t["trace_km"] = d / 1000
os_t["traces_5km"] = [len(v) for v in gk.query_ball_point(np.c_[os_t.x, os_t.y], 5000)]
nk = cKDTree(np.c_[tn.x, tn.y])
fy, nt = [], []
for nm, x, y in zip(os_t.name1, os_t.x, os_t.y):
    best = None
    for i in nk.query_ball_point([x, y], 1500):
        if norm(tn.name.iloc[i]) == norm(nm): best = i; break
    fy.append(tn.first_trust_year.iloc[best] if best is not None else np.nan); nt.append(int(tn.n_trusts.iloc[best]) if best is not None else 0)
os_t["first_trust_year"] = fy; os_t["n_trusts"] = nt; os_t["named"] = os_t.n_trusts > 0
os_t.drop_duplicates(subset=["name1", "x", "y"], inplace=True)
osE = os_t[os_t.country == "England"]
R["validate"] = dict(towns=len(osE), named=int(osE.named.sum()), named_share=r3(osE.named.mean()),
                     named_trace2=r3((osE[osE.named].trace_km <= 2).mean()), other_trace2=r3((osE[~osE.named].trace_km <= 2).mean()),
                     named_median_km=r3(osE[osE.named].trace_km.median(), 2), other_median_km=r3(osE[~osE.named].trace_km.median(), 2))
# 20 km grid: named places vs surviving traces (England, cells with at least one OS city, town or village)
osv = pd.read_csv(os.path.join(H, "osnames_gb.tsv"), sep="\t", quoting=3, dtype=str, keep_default_na=False, usecols=["type", "local_type", "x", "y", "country"])
osv["x"] = pd.to_numeric(osv.x, errors="coerce"); osv["y"] = pd.to_numeric(osv.y, errors="coerce")
osv = osv[(osv.type == "populatedPlace") & (osv.country == "England")]
cell = lambda x, y: (int(x // 20000), int(y // 20000))
cells = {cell(x, y) for x, y in zip(osv.x, osv.y)}
cn = collections.Counter(cell(x, y) for x, y in zip(tn.x, tn.y))
ge = gb[gb.nation == "England"]; gex = np.c_[TO.transform(ge.lon.values, ge.lat.values)]
ct = collections.Counter(cell(x, y) for x, y in gex)
v1 = [cn[c] for c in cells]; v2 = [ct[c] for c in cells]
rho2, p2 = stats.spearmanr(v1, v2)
R["grid"] = dict(cells=len(cells), rho=r3(rho2), p=float(p2), empty_named=int(sum(1 for c in cells if cn[c] == 0)),
                 named_but_no_trace=int(sum(1 for c in cells if cn[c] > 0 and ct[c] == 0)))
os_t[["name1", "local_type", "district", "county", "country", "lat", "lon", "first_trust_year", "n_trusts", "trace_km", "traces_5km"]].rename(
    columns={"name1": "name", "local_type": "os_type"}).round({"trace_km": 2}).sort_values(["country", "name"]).to_csv(os.path.join(DATA, "towns_today.csv"), index=False)

# ======================================================== growth panel
P = pd.read_csv(os.path.join(DATA, "panel.csv"))
for a_, b_, n_ in [(1801, 1831, 30), (1831, 1851, 20), (1851, 1881, 30)]:
    P[f"g{a_}_{b_}"] = 100 * np.log(P[f"pop{b_}"] / P[f"pop{a_}"]) / n_
P["near"] = (P.trace_km <= 1).astype(int)
P["named1800"] = ((P.named == 1) & (P.first_trust_year <= 1800)).astype(int)
P["lpop"] = np.log(P.pop1801)
P["area"] = np.where((P.lon > -0.6) & (P.lat > 51.9), "fens", np.where(P.lon < -2, "southwest", "other"))
P["rail1851"] = (P.rail_year <= 1851).astype(int)
G = ["g1801_1831", "g1831_1851", "g1851_1881"]
R["panel"] = dict(n=len(P), n_wikidata=int(P.source.str.startswith("Wikidata").sum()), n_vob=int((~P.source.str.startswith("Wikidata")).sum()),
                  near=int(P.near.sum()), named=int(P.named.sum()), named1800=int(P.named1800.sum()),
                  fens=int((P.area == "fens").sum()), southwest=int((P.area == "southwest").sum()), other=int((P.area == "other").sum()),
                  median_pop1801=int(P.pop1801.median()), n1881=int(P.pop1881.notna().sum()))
comp = {}
for var in ["near", "named1800"]:
    comp[var] = {}
    for g in G:
        a1 = P[P[var] == 1][g].dropna(); a0 = P[P[var] == 0][g].dropna()
        comp[var][g] = dict(yes=r3(a1.median()), no=r3(a0.median()), n_yes=len(a1), n_no=len(a0),
                            p=float(stats.mannwhitneyu(a1, a0).pvalue))
R["compare"] = comp
mods = {}
for g in G:
    d_ = P.dropna(subset=[g])
    m = smf.ols(f"{g} ~ near + named1800 + lpop + C(area)", data=d_).fit(cov_type="HC1")
    mods[g] = dict(n=int(m.nobs), r2=r3(m.rsquared), **{k: dict(b=r3(m.params[k]), lo=r3(m.conf_int().loc[k, 0]), hi=r3(m.conf_int().loc[k, 1]), p=float(m.pvalues[k]))
                                                          for k in ["near", "named1800", "lpop"]})
R["models"] = mods
# change in growth after the railway age began, named vs others
P["change"] = P.g1831_1851 - P.g1801_1831
P["change2"] = P.g1851_1881 - P.g1801_1831
R["change"] = dict(named=r3(P[P.named1800 == 1].change.median()), other=r3(P[P.named1800 == 0].change.median()),
                   p=float(stats.mannwhitneyu(P[P.named1800 == 1].change, P[P.named1800 == 0].change).pvalue),
                   named2=r3(P[P.named1800 == 1].change2.median()), other2=r3(P[P.named1800 == 0].change2.dropna().median()),
                   p2=float(stats.mannwhitneyu(P[P.named1800 == 1].change2.dropna(), P[P.named1800 == 0].change2.dropna()).pvalue))
m = smf.ols("g1851_1881 ~ named1800 + rail1851 + named1800:rail1851 + lpop + C(area)", data=P.dropna(subset=["g1851_1881"])).fit(cov_type="HC1")
R["rail_model"] = dict(n=int(m.nobs), **{k.replace(":", "_x_"): dict(b=r3(m.params[k]), lo=r3(m.conf_int().loc[k, 0]), hi=r3(m.conf_int().loc[k, 1]), p=float(m.pvalues[k]))
                                          for k in ["named1800", "rail1851", "named1800:rail1851"]})
R["panel_growth"] = {g: r3(P[g].median()) for g in G}
R["index"] = {str(y): r3((P[f"pop{y}"] / P.pop1801).median()) for y in (1801, 1811, 1821, 1831, 1841, 1851, 1881, 1901)}
R["index_named"] = {str(y): r3((P[P.named1800 == 1][f"pop{y}"] / P[P.named1800 == 1].pop1801).median()) for y in (1801, 1811, 1821, 1831, 1841, 1851, 1881, 1901)}
st = P[P.place == "Stilton"].iloc[0]
R["stilton_index"] = {str(y): r3(st[f"pop{y}"] / st.pop1801) for y in (1801, 1811, 1821, 1831, 1841, 1851, 1881, 1901)}
R["stilton"] = {str(y): int(st[f"pop{y}"]) for y in (1801, 1831, 1851, 1881, 1901)}
R["stilton"]["trace_m"] = int(round(st.trace_km * 1000))
R["stilton"]["first"] = int(st.first_trust_year)
# peak census year per place (among 1801..1901 where present)
yrs = [1801, 1811, 1821, 1831, 1841, 1851, 1881, 1901]
def peak(r):
    v = {y: r[f"pop{y}"] for y in yrs if not math.isnan(r[f"pop{y}"])}
    return max(v, key=v.get)
P["peak"] = P.apply(peak, axis=1)
R["peaks"] = dict(named_by1851=r3((P[P.named1800 == 1].peak <= 1851).mean()), other_by1851=r3((P[P.named1800 == 0].peak <= 1851).mean()),
                  near_by1851=r3((P[P.near == 1].peak <= 1851).mean()), far_by1851=r3((P[P.near == 0].peak <= 1851).mean()))

# ======================================================== big towns
Bt = pd.read_csv(os.path.join(DATA, "big_towns.csv"))
Bt["g"] = 100 * np.log(Bt.pop1861 / Bt.pop1801) / 60
b = Bt.dropna(subset=["g", "first_trust_year"])
r1, p1 = stats.spearmanr(b.first_trust_year, b.g); r2_, p2_ = stats.spearmanr(b.n_trusts, b.g)
R["big"] = dict(n=len(Bt), named=int(Bt.named.sum()), n_g=len(b), rho_first=r3(r1), p_first=float(p1), rho_hub=r3(r2_), p_hub=float(p2_),
                median_first=int(Bt.first_trust_year.median()), latest=dict(town=Bt.loc[Bt.first_trust_year.idxmax(), "town"], year=int(Bt.first_trust_year.max())))

# ======================================================== context quoted from Wikipedia (checked against the on-disk text)
R["context"] = dict(peak_trusts="over 1,000", peak_miles="30,000", gates="almost 8,000", tollhouses_1840="over 5,000",
                    first_turnpike=1663, first_trust_act=1706, mail_coach=1784, telford_from=45, telford_to=27, exeter_hours=17,
                    exeter_miles=170, rebecca_from=1839, rebecca_to=1843, lgact=1888, bolton_1846=3998, bolton_1849=1185)
R["gis"] = json.load(open(os.path.join(DATA, "_gis_status.json")))

json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))

# ======================================================== page data
KC = {"milestone": 0, "milepost": 1, "guide stone": 2, "toll house": 3}
trace_rows = [[round(r.lat, 4), round(r.lon, 4), KC[r.kind], 1 if isinstance(r.listed, str) and ("listed" in r.listed or "scheduled" in r.listed) else 0,
               int(r.year) if not math.isnan(r.year) else (-int(r.century) if not math.isnan(r.century) else None)] for r in T.itertuples()]
named_rows = [[r.name, round(r.lat, 4), round(r.lon, 4), int(r.first_trust_year) if not math.isnan(r.first_trust_year) else None, int(r.n_trusts),
               1 if r.os_type in ("City", "Town") else 0] for r in tn.itertuples()]
trust_ids = {}
for r in tp.itertuples():
    trust_ids.setdefault((r.os_name, round(r.lat, 4), round(r.lon, 4)), []).append(int(r.trust_id))
TR = {int(r.id): [r.trust, int(r.year) if not math.isnan(r.year) else None, r.county] for r in tr.itertuples()}
named_trusts = [[TR[i] for i in sorted(set(trust_ids.get((n[0], n[1], n[2]), [])))][:12] for n in named_rows]
towns_rows = [[r.name1, r.county if isinstance(r.county, str) and r.county else r.district, round(r.lat, 4), round(r.lon, 4),
               int(r.first_trust_year) if not math.isnan(r.first_trust_year) else None, int(r.n_trusts), round(r.trace_km, 2), int(r.traces_5km)]
              for r in os_t.itertuples()]
panel_rows = [[r.place, int(r.pop1801), r3(r.g1801_1831, 2), r3(r.g1831_1851, 2), r3(r.g1851_1881, 2), int(r.near), int(r.named1800)] for r in P.itertuples()]
cdens = [[r.county, r.nation, int(r.area_km2), int(r.milestones_and_mileposts), int(r.toll_houses), r.per_100km2] for r in cd.itertuples()]
big_rows = [[r.town, int(r.pop1801), int(r.pop1861) if not math.isnan(r.pop1861) else None, int(r.first_trust_year) if not math.isnan(r.first_trust_year) else None,
             int(r.n_trusts), r3(r.g, 2), int(r.rail_year) if not math.isnan(r.rail_year) else None] for r in Bt.itertuples()]
json.dump(dict(traces=trace_rows, named=named_rows, named_trusts=named_trusts, towns=towns_rows, panel=panel_rows, counties=cdens, big=big_rows),
          open(os.path.join(DATA, "page_data.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print(json.dumps({k: R[k] for k in ["trusts", "wave", "traces", "validate", "grid", "panel", "compare", "models", "change", "rail_model", "peaks", "big", "stilton", "counties"]}, indent=1, default=str)[:9000])
