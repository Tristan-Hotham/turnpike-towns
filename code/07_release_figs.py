"""Step 7. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png, 1520 px wide).
Maps are drawn from coordinates over the Natural Earth 1:10m land outline (no web tiles).
Every number comes from ../data/results.json or ../data/page_data.json.
Run: FONT_DIR=/path/to/fonts python3 07_release_figs.py
"""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    if os.path.exists(os.path.join(FD, f)): fm.fontManager.addfont(os.path.join(FD, f))
BG = "#F3EEE2"; FG = "#232A24"; MUT = "#66665A"; RULE = "#D9D0BC"; LAND = "#E6DFCB"
GREEN = "#2E5E4A"; GREENL = "#8FB3A0"; OCHRE = "#C08A2E"; RED = "#A33B2B"; STONE = "#7E7A6E"
MONO = "IBM Plex Mono"
CMAP = LinearSegmentedColormap.from_list("yr", ["#1E543E", "#7A8A3A", "#D69628"])
plt.rcParams.update({"font.family": "Source Serif 4", "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG, "axes.facecolor": BG, "figure.facecolor": BG})
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
PO = os.path.join(ROOT, "release", "paper"); BO = os.path.join(ROOT, "release", "blog")
os.makedirs(PO, exist_ok=True); os.makedirs(BO, exist_ok=True)
K = math.cos(math.radians(52.5))
LAND_POLYS = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LAND_POLYS.append(np.c_[a[:, 0] * K, a[:, 1]])


def basemap(ax, ext=(-6.0, 2.0, 49.9, 55.9)):
    for a in LAND_POLYS:
        ax.add_patch(Polygon(a, closed=True, fc=LAND, ec="#CFC6AE", lw=.5, zorder=0))
    ax.set_xlim(ext[0] * K, ext[1] * K); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def save(fig, name, blog):
    p = os.path.join(BO if blog else PO, ("b_" if blog else "f_") + name)
    fig.savefig(p, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=.2 if blog else .15); plt.close(fig)
    if blog:
        from PIL import Image
        im = Image.open(p)
        if im.size[0] != 1520: im = im.resize((1520, round(im.size[1] * 1520 / im.size[0])), Image.LANCZOS)
        im.save(p, optimize=True)


def fig_map(blog):
    fig, ax = plt.subplots(figsize=(7.6, 8.4) if blog else (6.2, 6.9))
    basemap(ax)
    t = np.array([[r[0], r[1]] for r in P["traces"] if r[2] != 3]); th = np.array([[r[0], r[1]] for r in P["traces"] if r[2] == 3])
    ax.scatter(t[:, 1] * K, t[:, 0], s=1.2, c=STONE, alpha=.45, lw=0, zorder=1)
    ax.scatter(th[:, 1] * K, th[:, 0], s=7, c=RED, alpha=.9, lw=0, zorder=2)
    nm = sorted([r for r in P["named"] if r[3] is not None], key=lambda r: -r[3])
    sc = ax.scatter([r[2] * K for r in nm], [r[1] for r in nm], s=[(16 if r[5] else 7) + 2 * min(r[4], 8) for r in nm], c=[r[3] for r in nm],
                    cmap=CMAP, norm=Normalize(1700, 1840), lw=.3, edgecolor=FG, alpha=.92, zorder=3)
    cax = ax.inset_axes([0.56, 0.055, 0.28, 0.018])
    cb = fig.colorbar(ScalarMappable(norm=Normalize(1700, 1840), cmap=CMAP), cax=cax, orientation="horizontal")
    cb.set_ticks([1700, 1770, 1840]); cb.ax.tick_params(labelsize=9.5 if blog else 8.5); cb.outline.set_visible(False)
    for l in cb.ax.get_xticklabels(): l.set_family(MONO)
    ax.text(0.56, 0.083, "First named in a trust", transform=ax.transAxes, family=MONO, fontsize=10 if blog else 9, color=FG)
    hs = [Line2D([], [], marker="o", ls="", ms=4, mfc=STONE, mec="none", label=f"Surviving milestone or milepost ({R['traces']['milestones'] + R['traces']['mileposts']:,})"),
          Line2D([], [], marker="o", ls="", ms=5, mfc=RED, mec="none", label=f"Toll house ({R['traces']['tollhouses']:,})")]
    ax.legend(handles=hs, loc="upper right", frameon=True, facecolor=BG, edgecolor=RULE, prop=dict(family=MONO, size=10 if blog else 8.5))
    save(fig, "map.png", blog)


def fig_decades(blog):
    D = R["decades"]; x = np.array([d["decade"] for d in D]); n = np.array([d["n"] for d in D])
    fig, ax = plt.subplots(figsize=(7.6, 4.2) if blog else (6.4, 3.4))
    ax.axvspan(1750, 1773, color=OCHRE, alpha=.13, lw=0)
    ax.bar(x + 5, n, width=7.6, color=[OCHRE if 1750 <= v < 1780 else GREEN for v in x])
    ax.axvline(1784, color=FG, ls="--", lw=1)
    ax.text(1786, max(n) * .78, "1784: first\nmail coach", family=MONO, fontsize=10 if blog else 8.5, va="top")
    pk = int(np.argmax(n)); ax.text(x[pk] + 5, n[pk] + 4, f"{x[pk]}s: {n[pk]}", family=MONO, fontsize=10.5 if blog else 9, va="bottom", ha="center"); ax.set_ylim(0, n[pk] * 1.12)
    ax.set_ylabel("Trusts founded per decade"); ax.set_xlim(1655, 1875); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
    save(fig, "decades.png", blog)


def fig_regions(blog):
    V = R["regions"][::-1]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 4.2) if blog else (6.6, 3.4), gridspec_kw=dict(width_ratios=[1.5, 1], wspace=.55 if blog else .7))
    y = np.arange(len(V))
    ax.hlines(y, [v["first"] for v in V], [v["median"] for v in V], color=GREENL, lw=4)
    ax.scatter([v["median"] for v in V], y, s=70, c=[v["median"] for v in V], cmap=CMAP, norm=Normalize(1700, 1840), zorder=3, edgecolor=FG, lw=.5)
    for i, v in enumerate(V): ax.text(v["median"] + 4, i, f"{v['median']}", va="center", family=MONO, fontsize=9.5 if blog else 8)
    ax.set_yticks(y); ax.set_yticklabels([v["region"] for v in V], fontsize=11 if blog else 9); ax.set_xlim(1655, 1810)
    ax.set_xlabel("Earliest trust to median founding year", fontsize=11 if blog else 9); ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
    B = R["wave"]["bands"]; labs = ["0 to 50", "50 to 100", "100 to 200", "200+"]
    ax2.bar(range(4), [b["median"] - 1700 for b in B], bottom=1700, color=GREEN, width=.65)
    for i, b in enumerate(B): ax2.text(i, b["median"] + 1, f"{b['median']}\n({b['n']})", ha="center", va="bottom", family=MONO, fontsize=9 if blog else 7.5)
    ax2.set_ylim(1700, 1775); ax2.set_xticks(range(4)); ax2.set_xticklabels(labs, fontsize=9.5 if blog else 7.5, rotation=0 if blog else 20)
    ax2.set_xlabel("km from London", fontsize=11 if blog else 9); ax2.set_ylabel("Median first trust year", fontsize=11 if blog else 9)
    save(fig, "regions.png", blog)


def fig_counties(blog):
    C = [c for c in P["counties"] if c[1] == "England" and c[2] > 500]
    C = sorted(C, key=lambda c: -c[5]); sel = C[:10] + C[-6:]
    fig, ax = plt.subplots(figsize=(7.6, 5.6) if blog else (6.2, 4.6))
    y = np.arange(len(sel))[::-1]
    ax.barh(y, [c[5] for c in sel], color=[GREEN] * 10 + [OCHRE] * 6, height=.7)
    for yy, c in zip(y, sel): ax.text(c[5] + .3, yy, f"{c[5]:.1f}  ({c[3]:,})", va="center", family=MONO, fontsize=9.5 if blog else 8)
    ax.set_yticks(y); ax.set_yticklabels([c[0] for c in sel], fontsize=11 if blog else 9)
    ax.axhline(5.5, color=MUT, lw=.8, ls=":")
    ax.set_xlabel("Surviving milestones and mileposts per 100 km² (count)", fontsize=11 if blog else 9); ax.set_xlim(0, 26)
    ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
    save(fig, "counties.png", blog)


def fig_forest(blog):
    G = [("g1801_1831", "1801 to 1831"), ("g1831_1851", "1831 to 1851"), ("g1851_1881", "1851 to 1881")]
    rows = [(gl, lab, R["models"][g][c], col) for g, gl in G for c, lab, col in [("named1800", "named in a trust by 1800", GREEN), ("near", "milestone within 1 km", STONE)]]
    fig, ax = plt.subplots(figsize=(7.6, 4.0) if blog else (6.4, 3.3))
    y = np.arange(len(rows))[::-1]
    for yy, (gl, lab, v, col) in zip(y, rows):
        ax.plot([v["lo"], v["hi"]], [yy, yy], color=col, lw=2.2)
        sig = v["lo"] > 0 or v["hi"] < 0
        ax.scatter([v["b"]], [yy], s=60, color=col if sig else BG, edgecolor=col, lw=2, zorder=3)
    ax.axvline(0, color=FG, lw=1)
    ax.set_yticks(y); ax.set_yticklabels([f"{gl}: {lab}" for gl, lab, _, _ in rows], fontsize=10.5 if blog else 8.5)
    ax.set_xlabel("Difference in yearly growth, percentage points (95% interval)", fontsize=11 if blog else 9)
    ax.set_xlim(-.8, .8); ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
    save(fig, "forest.png", blog)


def fig_stilton(blog):
    Y = [1801, 1811, 1821, 1831, 1841, 1851, 1881, 1901]
    fig, ax = plt.subplots(figsize=(7.6, 4.2) if blog else (6.2, 3.4))
    ax.plot(Y, [R["index"][str(y)] for y in Y], color=STONE, lw=2.4, label=f"Median of all {R['panel']['n']} places")
    ax.plot(Y, [R["index_named"][str(y)] for y in Y], color=GREEN, lw=1.8, ls="--", label="Median of places named in a trust by 1800")
    ax.plot(Y, [R["stilton_index"][str(y)] for y in Y], color=GREEN, lw=3.2, marker="o", label="Stilton")
    for y in (1801, 1831, 1851, 1901):
        ax.annotate(f"{R['stilton'][str(y)]:,}", (y, R["stilton_index"][str(y)]), xytext=(0, -16 if y != 1831 else 9), textcoords="offset points",
                    ha="center", family=MONO, fontsize=9.5 if blog else 8, color=GREEN)
    ax.set_ylabel("Population, multiple of 1801"); ax.set_ylim(.85, 2.05); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
    ax.legend(frameon=False, prop=dict(family=MONO, size=9.5 if blog else 8), loc="upper left")
    save(fig, "stilton.png", blog)


if __name__ == "__main__":
    for blog in (False, True):
        for f in (fig_map, fig_decades, fig_regions, fig_counties, fig_forest, fig_stilton):
            f(blog)
    print("figures written")
