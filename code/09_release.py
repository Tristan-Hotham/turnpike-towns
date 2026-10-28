"""Step 9. Blog post (release/blog/post.html from blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader.
Run: python3 09_release.py
"""
import json, os, re, shutil, zipfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "05_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = re.sub(r"\{\{(?!IMG\|)([^{}]+?)\}\}", b.sub, open(os.path.join(HERE, "blog_template.html")).read())
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m

title = "Turnpikes and Coaching Towns: England's Turnpike Trusts, Their Surviving Milestones and the Growth of Towns"
meta = dict(
    title="The turnpike towns: did the turnpike make the town grow?",
    slug="turnpike-towns",
    excerpt=(f"England's {R['trusts']['unique']:,} turnpike trusts were founded in a rush in the 1750s and 1760s, and {R['traces']['total']:,} of their milestones and toll houses "
             f"are still recorded. But did the towns on the turnpikes grow faster? Not that I can see."),
    seo_description=f"{R['trusts']['unique']:,} turnpike trusts, {R['traces']['total']:,} surviving milestones and toll houses, and whether turnpike towns grew faster.",
    tags=["turnpikes", "roads", "milestones", "coaching inns", "transport history", "towns", "maps", "data"],
    header_alt=(f"Title card reading 'The turnpike towns' on a parchment background, beside a map of England and Wales with about a thousand green and ochre dots "
                f"for places named in turnpike trusts and fine grey dots for surviving milestones. Text: {R['trusts']['unique']:,} turnpike trusts, a boom in the 1750s, "
                f"and {R['traces']['total']:,} milestones and toll houses still recorded."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

pt = open(os.path.join(ROOT, "release", "paper", "Hotham_Turnpike_Towns.tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("$<$", "<").replace("$-$", "-")
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title=title,
    description_html=(f"<p>{ab}</p><p>The trust gazetteer is derived from Wikipedia (CC BY-SA 4.0); the tables of milestones and toll houses contain OpenStreetMap data "
                      f"(&copy; OpenStreetMap contributors, ODbL 1.0) and Wikidata (CC0).</p>"
                      f"<p>Interactive version: https://tristan-hotham.github.io/turnpike-towns/. Data and code: https://github.com/Tristan-Hotham/turnpike-towns. Blog post: to follow.</p>"),
    keywords=["turnpike trusts", "turnpike roads", "milestones", "toll houses", "coaching", "transport history", "urban growth", "England", "Wikidata", "OpenStreetMap"],
    licence="cc-by-sa-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/turnpike-towns", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/turnpike-towns/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://en.wikipedia.org/wiki/Turnpike_trust", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://www.wikidata.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.openstreetmap.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.visionofbritain.org.uk/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://doi.org/10.5281/zenodo.23689966", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://doi.org/10.5281/zenodo.23727127", relation="isderivedfrom", resource_type="other"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", "Hotham_Turnpike_Towns.pdf"), Z)
for f in ["trusts.csv", "towns_named.csv", "traces.csv", "county_density.csv", "panel.csv", "towns_today.csv", "decades.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "turnpike-towns_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data", "data/raw"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"turnpike-towns/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"turnpike-towns/{f}")
print("release files written; post words:", len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t, flags=re.S)).split()), "abstract words:", len(ab.split()))
