"""Reddit collage for the turnpike towns study (2400 x 3000 px). Every number comes from ../data/results.json or ../data/page_data.json.
Run from this folder: python3 collage.py
"""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon, FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap, Normalize

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts") + "/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
BG = "#F2EBD9"; FG = "#1E2A22"; MUT = "#6A6656"; LAND = "#E4DAC2"; EDGE = "#CBBF9F"
GREEN = "#1F4E3D"; OCHRE = "#C98A1E"; RED = "#A33B2B"; STONE = "#FFFDF6"
CMAP = LinearSegmentedColormap.from_list("yr", ["#173F31", "#6E8A3A", "#D4931F"])
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
K = math.cos(math.radians(52.5))
LAND_POLYS = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LAND_POLYS.append(np.c_[a[:, 0] * K, a[:, 1]])

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.04, 0.967, "Did the turnpike make the town?", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(0.04, 0.915, f"England's {R['trusts']['unique']:,} turnpike trusts ran the main roads from 1663, charging tolls to mend them. Coloured dots:\n"
         f"places named in a trust. White dots: {R['traces']['total']:,} milestones, mileposts and toll houses still recorded today.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.35)

# hero map
ax = fig.add_axes([0.0, 0.285, 0.6, 0.575]); ax.set_facecolor(BG)
for a in LAND_POLYS: ax.add_patch(Polygon(a, closed=True, fc=LAND, ec=EDGE, lw=.6, zorder=0))
t = np.array([[r[0], r[1]] for r in P["traces"] if r[2] != 3]); th = np.array([[r[0], r[1]] for r in P["traces"] if r[2] == 3])
ax.scatter(t[:, 1] * K, t[:, 0], s=3.2, c=STONE, edgecolor="#8E876F", lw=.25, zorder=1, rasterized=True)
ax.scatter(th[:, 1] * K, th[:, 0], s=10, c=RED, lw=0, zorder=2, rasterized=True)
nm = sorted([r for r in P["named"] if r[3] is not None], key=lambda r: -r[3])
ax.scatter([r[2] * K for r in nm], [r[1] for r in nm], s=[(26 if r[5] else 11) + 3 * min(r[4], 8) for r in nm], c=[r[3] for r in nm],
           cmap=CMAP, norm=Normalize(1700, 1840), edgecolor=FG, lw=.35, alpha=.93, zorder=3, rasterized=True)
ax.set_xlim(-5.9 * K, 1.85 * K); ax.set_ylim(49.9, 55.85); ax.set_aspect("equal"); ax.axis("off")
# colour key
ck = fig.add_axes([0.62, 0.318, 0.22, 0.012])
ck.imshow(np.linspace(0, 1, 200)[None, :], aspect="auto", cmap=CMAP); ck.set_yticks([]); ck.set_xticks([0, 100, 199]); ck.set_xticklabels(["1700", "1770", "1840"], family=MONO, fontsize=10, color=FG)
for s in ck.spines.values(): s.set_visible(False)
fig.text(0.62, 0.335, "First named in a turnpike trust", family=MONO, fontsize=10.5, color=FG)
fig.text(0.62, 0.288, "Red dots: toll houses", family=MONO, fontsize=10.5, color=RED)
ax.annotate(f"{R['named']['hub_top'][0]['name']}: named in\n{R['named']['hub_top'][0]['n']} trusts", xy=(-1.549 * K, 53.80), xytext=(-0.25 * K, 54.75),
            family=MONO, fontsize=10, color=FG, arrowprops=dict(arrowstyle="-", color=FG, lw=.8))
ax.annotate(f"Wadesmill, 1663:\nthe first turnpike", xy=(-0.028 * K, 51.84), xytext=(0.15 * K, 50.45),
            family=MONO, fontsize=10, color=FG, arrowprops=dict(arrowstyle="-", color=FG, lw=.8))

# right column numbers
tx = fig.add_axes([0.6, 0.36, 0.38, 0.49]); tx.axis("off")
notes = [(f"{R['trusts']['peak_n']}", f"trusts founded in the 1750s alone: the\npeak of turnpike mania. {R['trusts']['share_1750_1772'] * 100:.0f}% of all dated\ntrusts came in 1750 to 1772.", OCHRE),
         (f"{R['wave']['bands'][3]['median'] - R['wave']['bands'][0]['median']} years", f"Towns near London got their first trust\nonly {R['wave']['bands'][3]['median'] - R['wave']['bands'][0]['median']} years before towns 200 km away\n(median {R['wave']['bands'][0]['median']} against {R['wave']['bands'][3]['median']}). The boom\nhappened almost everywhere at once.", GREEN),
         (f"{R['traces']['aroad_50'] * 100:.0f}%", f"of surviving milestones stand within\n50 m of a modern A-road. The turnpikes\nbecame today's main roads.", GREEN),
         (f"+{R['models']['g1801_1831']['named1800']['b']:.2f}", f"points a year: extra growth of places\nnamed in a trust, 1801 to 1831, once size\nis allowed for (95% interval {R['models']['g1801_1831']['named1800']['lo']:.2f}\nto +{R['models']['g1801_1831']['named1800']['hi']:.2f}). No clear turnpike effect.", RED)]
ys = [1.0, 0.74, 0.48, 0.24]
for (big, small, c), y in zip(notes, ys):
    tx.text(0, y, big, fontproperties=DISP, fontsize=34, color=c, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.075, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# bottom row
fig.text(0.04, 0.262, "TRUSTS FOUNDED PER DECADE", family=MONO, fontsize=11, color=MUT)
fig.text(0.37, 0.262, "STILTON, ON THE FIRST TURNPIKE", family=MONO, fontsize=11, color=MUT)
fig.text(0.70, 0.262, "MILESTONES PER 100 KM²", family=MONO, fontsize=11, color=MUT)
def style(a):
    a.set_facecolor(BG)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    for s in ("left", "bottom"): a.spines[s].set_color(MUT)
    a.tick_params(colors=FG, labelsize=10)
    for l in a.get_xticklabels() + a.get_yticklabels(): l.set_family(MONO)
a1 = fig.add_axes([0.06, 0.075, 0.27, 0.165])
D = R["decades"]; x = np.array([d["decade"] for d in D]); n = np.array([d["n"] for d in D])
a1.bar(x + 5, n, width=8, color=[OCHRE if 1750 <= v < 1780 else GREEN for v in x])
a1.set_xticks([1700, 1750, 1800, 1850]); a1.set_yticks([0, 100, 200]); style(a1)
a1.text(1764, n.max() * .98, f"1750s: {n.max()}", family=MONO, fontsize=10, color=FG, va="top")
a2 = fig.add_axes([0.42, 0.075, 0.25, 0.165])
Y = [1801, 1811, 1821, 1831, 1841, 1851, 1881, 1901]
a2.plot(Y, [R["index"][str(y)] for y in Y], color="#8E876F", lw=2.2)
a2.plot(Y, [R["stilton_index"][str(y)] for y in Y], color=GREEN, lw=3, marker="o", ms=4)
for y in (1801, 1851, 1901):
    a2.annotate(f"{R['stilton'][str(y)]:,}", (y, R["stilton_index"][str(y)]), xytext=(14, 6) if y == 1851 else (0, -15), textcoords="offset points", ha="center", family=MONO, fontsize=10, color=GREEN)
a2.text(1903, R["index"]["1901"], f"all {R['panel']['n']}\nplaces", family=MONO, fontsize=9, color=MUT, va="center")
a2.text(1850, 1.3, "Stilton", family=MONO, fontsize=9.5, color=GREEN)
a2.set_ylim(.85, 1.8); a2.set_xlim(1795, 1925); a2.set_xticks([1801, 1851, 1901]); a2.set_yticks([1, 1.25, 1.5, 1.75]); style(a2)
a2.set_ylabel("× 1801 population", family=MONO, fontsize=10, color=FG)
a3 = fig.add_axes([0.835, 0.075, 0.14, 0.165])
C = sorted([c for c in P["counties"] if c[1] == "England" and c[2] > 500], key=lambda c: -c[5]); sel = C[:4] + C[-3:]
yy = np.arange(len(sel))[::-1]
a3.barh(yy, [c[5] for c in sel], color=[GREEN] * 4 + [OCHRE] * 3, height=.7)
for y_, c in zip(yy, sel): a3.text(c[5] + .4, y_, f"{c[5]:.1f}", va="center", family=MONO, fontsize=9.5, color=FG)
a3.set_yticks(yy); a3.set_yticklabels([c[0] for c in sel]); a3.set_xticks([0, 10, 20]); a3.set_xlim(0, 27); style(a3)
for l in a3.get_yticklabels(): l.set_family(SER); l.set_fontsize(10)
fig.text(0.04, 0.012, "Data: Wikipedia lists of turnpike trusts by region (CC BY-SA 4.0); milestones and toll houses: Wikidata (CC0) and\n"
         "OpenStreetMap (© OpenStreetMap contributors, ODbL); census: Wikidata, A Vision of Britain through Time; OS Open Names (OGL v3).\n"
         "Milestones are survivors, recorded unevenly by county. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9, color=MUT, linespacing=1.4)
fig.savefig(os.path.join(HERE, "did_the_turnpike_make_the_town.png"), facecolor=BG, dpi=200)
print("ok")
