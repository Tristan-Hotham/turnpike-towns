"""Step 8. Build the paper PDF: fill paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Turnpike_Towns.tex and compile it with xelatex (figures from 07_release_figs.py).
Run: python3 08_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Turnpike_Towns"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "sf2": return f"{'+' if v >= 0 else '-'}{abs(v):.2f}"
    if f == "abs2": return f"{abs(v):.2f}"
    if f == "p": return "p $<$ 0.001" if v < 0.001 else f"p = {v:.3f}"
    return str(v).replace("&", "\\&").replace("%", "\\%").split(";")[0]


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


rows = ""
for r in R["regions"]:
    rows += f"{r['region']} & {r['n_all']:,} & {r['n']:,} & {r['first']} & {r['median']} & {r['by1772'] * 100:.0f} & {r['placed'] * 100:.0f}\\\\\n"
t = R["trusts"]
rows += f"\\midrule England & {t['unique']:,} & {t['with_year']:,} & {t['first_year']} & {t['median_year']} & {t['by1772'] * 100:.0f} & {t['placed_share'] * 100:.0f}\\\\\n"
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Turnpike trusts in Wikipedia's regional lists. Dated: trusts with a founding year. "
      "First and median: founding years. By 1772: share of dated trusts founded by 1772. Placed: share of trusts with at least one name matched to OS Open Names.}\\label{tab:regions}"
      "\\begin{tabular}{lrrrrrr}\\toprule Region & Trusts & Dated & First & Median & \\% by 1772 & \\% placed\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
G = [("g1801_1831", "1801 to 1831"), ("g1831_1851", "1831 to 1851"), ("g1851_1881", "1851 to 1881")]
rows = ""
for g, gl in G:
    c = R["compare"]; m = R["models"][g]
    rows += (f"{gl} & {c['named1800'][g]['yes']:.2f} & {c['named1800'][g]['no']:.2f} & {c['near'][g]['yes']:.2f} & {c['near'][g]['no']:.2f} & "
             f"{m['named1800']['b']:.2f} ({m['named1800']['lo']:.2f}, {m['named1800']['hi']:.2f}) & {m['near']['b']:.2f} ({m['near']['lo']:.2f}, {m['near']['hi']:.2f}) & {m['n']}\\\\\n")
TG = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Yearly population growth (per cent) of the census panel. Medians for places named in a trust by 1800 (named) or not, "
      "and with a surviving milestone, milepost or toll house within 1 km (stone) or not; and OLS estimates (percentage points, 95\\% interval) from regressions that also include "
      "log population in 1801 and three area dummies, with robust standard errors.}\\label{tab:growth}"
      "\\begin{tabular}{lrrrrllr}\\toprule & \\multicolumn{4}{c}{Median growth} & \\multicolumn{2}{c}{Regression estimate} & \\\\ Period & Named & Not & Stone & No stone & Named & Stone & N\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
s = open(os.path.join(HERE, "paper_template.tex")).read()
s = s.replace("{{TABLE_REGIONS}}", TR).replace("{{TABLE_GROWTH}}", TG)
s = re.sub(r"\{\{(.+?)\}\}", sub, s)
assert "{{" not in s
s = s.replace(" -0.", " $-$0.").replace("(-0.", "($-$0.")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(s)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print(r.stdout[-500:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
