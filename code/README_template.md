# Turnpikes and coaching towns

From 1663 to the 1830s, turnpike trusts took over England's main roads, charged tolls and mended the roads with the money. This study lists the trusts, maps the milestones, mileposts and toll houses that survive, and asks whether being on a turnpike made a town grow.

**Interactive version:** https://tristan-hotham.github.io/turnpike-towns/

**Paper:** https://doi.org/10.5281/zenodo.23729648

This repository holds the interactive page, the derived datasets, the computed results and the analysis code for a data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- Wikipedia's eight regional lists name {{trusts.unique|int}} English turnpike trusts, {{trusts.with_year|int}} with the year of their first act. The busiest decade was the 1750s, with {{trusts.n_1750s|int}} new trusts, then the 1760s with {{trusts.n_1760s|int}}; {{trusts.n_1750_1772|int}} trusts ({{trusts.share_1750_1772|pct0}}) were founded in 1750 to 1772, and {{trusts.by1800|pct0}} by 1800. Only {{trusts.after1830|int}} came after 1830.
- The trusts did not spread out from London in a clear wave: towns named in a trust within 50 km of London have a median first year of {{wave.bands.0.median|raw}}, those more than 200 km away {{wave.bands.3.median|raw}} (Spearman {{wave.rho|f2}}, {{wave.n_towns|int}} towns). The North West was latest (median {{regions.7.median|raw}}).
- {{named.places|int}} places are named in at least one trust title; in England {{validate.named|int}} of {{validate.towns|int}} OS towns and cities ({{validate.named_share|pct0}}). The biggest hubs are {{named.hub_top.0.name|raw}} ({{named.hub_top.0.n|int}} trusts), {{named.hub_top.1.name|raw}} ({{named.hub_top.1.n|int}}) and {{named.hub_top.2.name|raw}} ({{named.hub_top.2.n|int}}).
- Wikidata and OpenStreetMap record {{traces.total|int}} surviving milestones, mileposts, guide stones and toll houses in the UK ({{traces.england|int}} in England, {{traces.wales|int}} in Wales). {{traces.aroad_50|pct0}} stand within 50 m of a modern A-road. Recorded density ranges from {{counties.top.0.d|f1}} per 100 km² in {{counties.top.0.county|raw}} to {{counties.bottom.5.d|f1}} in {{counties.bottom.5.county|raw}}.
- {{validate.named_trace2|pct0}} of English towns named in a trust have a surviving milestone within 2 km, against {{validate.other_trace2|pct0}} of other towns; across {{grid.cells|int}} 20 km squares, named places and surviving traces go together (Spearman {{grid.rho|f2}}).
- Growth, {{panel.n|int}} places with census series: places named in a trust by 1800 grew faster in 1801 to 1831 ({{compare.named1800.g1801_1831.yes|f2}}% against {{compare.named1800.g1801_1831.no|f2}}% a year), but after allowing for size and area the difference is {{models.g1801_1831.named1800.b|f2}} points (95% interval {{models.g1801_1831.named1800.lo|f2}} to {{models.g1801_1831.named1800.hi|f2}}). A milestone within 1 km makes no difference ({{models.g1801_1831.near.b|f2}}, {{models.g1801_1831.near.lo|f2}} to {{models.g1801_1831.near.hi|f2}}).
- In 1831 to 1851 the named places grew {{models.g1831_1851.named1800.b|abs2}} points a year more slowly than similar places (interval {{models.g1831_1851.named1800.lo|f2}} to {{models.g1831_1851.named1800.hi|f2}}): a weak hint that turnpike places lost ground as the railways came.
- Among the {{big.n_g|int}} largest towns of 1801 with 1861 figures, neither an early first trust (Spearman {{big.rho_first|f2}}) nor the number of trusts (Spearman {{big.rho_hub|f2}}) goes with faster growth.

These are associations, not causes, from incomplete lists and a small, regionally lopsided growth sample.

## The turnpike road GIS

The ideal source, the turnpike road GIS for England and Wales 1700 to 1838 by Rosevear, Bogart, Shaw-Taylor and Satchell (openICPSR 195126), was not available for this build. `code/03_towns.py` checks for it in `../_data12/turnpikes/` and, if present, reads its shapefiles (pyshp) or GeoJSON and adds, for every place, the earliest turnpike act year of any road within 1 km (`gis_year`), reporting the field it used in `data/_gis_status.json`. The analysis would then need to be re-pointed at `gis_year` and the text revised.

## Files

- `index.html`: the interactive page (map with a year slider and town search, charts, tables). Data embedded; works as a single file.
- `header.png`: social card (1200 by 630).
- `data/raw/trusts_*.txt`: the rows of seven Wikipedia regional lists of turnpike trusts, as read by an automated web reader on 28 October 2026 (County | Trust | Founded | Initial act). `data/raw/check_se_webfetch.txt`: Berkshire and Kent rows read the same way, used to check the reader against the wikitext.
- `data/trusts.csv`: {{trusts.unique|int}} trusts with region, county, name(s), founding year, initial act, source and the place names matched to OS Open Names.
- `data/trust_places.csv`: one row per trust and placed name, with the OS Open Names place, its type and coordinates, and how the match was made.
- `data/towns_named.csv`: one row per place named in at least one trust: number of trusts, first trust year, trust ids.
- `data/decades.csv`: trusts founded per decade.
- `data/traces.csv`: {{traces.total|int}} milestones, mileposts, guide stones and toll houses: source (Wikidata or OSM) and id, kind, name, coordinates, nation, county, year or century, listing, distance to the nearest A-road, OSM inscription.
- `data/county_density.csv`: surviving milestones and mileposts and toll houses per county or unitary area, per 100 km².
- `data/inscriptions.csv`: destinations and mileages parsed from OSM inscriptions.
- `data/towns_today.csv`: every OS Open Names city or town in England and Wales with its first trust year (if named), number of trusts, distance to the nearest surviving trace and the number within 5 km.
- `data/panel.csv`: the {{panel.n|int}} places with census series 1801 to 1901, with turnpike, milestone and railway measures.
- `data/big_towns.csv`: the largest towns of 1801 with populations 1801 to 1900 and the same measures.
- `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage. `data/page_data.json`: compact data for the page.
- `code/01_trusts.py` (trust gazetteer and place matching), `02_traces.py` (milestones and toll houses), `03_towns.py` (populations, measures, turnpike GIS hook), `04_analyse.py` (statistics), `05_build_site.py` (page and README), `06_header.py` (social card), `07_release_figs.py`, `08_paper.py`, `09_release.py` (paper, blog and Zenodo files).
- `release/`: the paper (PDF, LaTeX source and figures), the blog post and figures, and the Zenodo files. `reddit/`: the collage, its script and the post text.

## How to rerun

The scripts read the shared source files in place, one folder up: `_data12/wd_osm_bundle12.json.gz` and `_data12/wikipedia_batch12*.json.gz` (QLever and Wikipedia API, 28 October 2026), `_data9/wd_osm_bundle.json` (Wikidata historic populations), `_data11/wd_osm_bundle11.json.gz` (Wikidata railway stations), `osnames_gb.tsv` (OS Open Names), `how-roman-is-your-road/data/` (counties and OSM A-roads), `seaside-railways/data/` (A Vision of Britain through Time series) and `canal-mania/data/towns_historic.csv`.

```
cd code
python3 01_trusts.py && python3 02_traces.py && python3 03_towns.py && python3 04_analyse.py && python3 05_build_site.py
FONT_DIR=/path/to/fonts python3 06_header.py
FONT_DIR=/path/to/fonts python3 07_release_figs.py && python3 08_paper.py && python3 09_release.py
```

Python 3 with pandas, numpy, scipy, statsmodels, pyproj, shapely, matplotlib and pyshp; Playwright for the header; xelatex for the paper.

## Method in brief

- **Trusts.** The tables of Wikipedia's eight "Turnpike trusts in ..." lists for England. Rows without a trust name (later acts) dropped; a trust listed under two counties kept once. For the South East list, held as wikitext, the web reader's rows matched all {{trusts.fidelity.n|int}} Berkshire and Kent rows checked (names, years and acts).
- **Places.** Each trust name is split into place words, matched exactly (ignoring case, hyphens and punctuation) to OS Open Names populated places, preferring the trust's region, then towns, then the place nearest the trust's other matches. {{trusts.placed|int}} trusts ({{trusts.placed_share|pct0}}) have at least one placed name.
- **Traces.** Wikidata milestones and toll houses in the UK and OSM historic milestones, mileposts, toll houses and toll gates; an OSM object within 40 m of a Wikidata object of the same kind is the same object. Wikidata dates of exactly 1701, 1801 or 1901 are century dates.
- **Growth.** Yearly growth 100 × ln(P2/P1) / years. Exposure: named in a trust founded by 1800; a surviving trace within 1 km. OLS with robust standard errors, log population in 1801 and three areas (fens, south west, other).

## Known limits

- The Wikipedia lists are marked incomplete; {{trusts.sussex_no_year|int}} Sussex trusts have no year; Wales and Scotland have no dated lists.
- Naming is not routing: a town that a turnpike ran through without being in its title counts as not named.
- Milestones are survivors, and their recording varies by county; Scotland is barely covered.
- The growth panel is small and regionally lopsided ({{panel.fens|int}} of {{panel.n|int}} places in Cambridgeshire, Huntingdonshire and the fens), on census parish boundaries.

## Sources and licences

- Turnpike trusts: Wikipedia, "Turnpike trusts in South East England", "... in the East of England", "... in the East Midlands", "... in the West Midlands", "... in North East England", "... in North West England", "... in Yorkshire", "... in South West England"; and "Turnpike trust", "Mail coach", "Tollhouse", "Turnpike Roads Act 1773", "Toll roads in Great Britain", "Rebecca Riots"; retrieved 28 October 2026, CC BY-SA 4.0.
- Milestones and toll houses: Wikidata (CC0) and OpenStreetMap (© OpenStreetMap contributors, ODbL 1.0), via QLever, 28 October 2026.
- Census populations: Wikidata (CC0), and A Vision of Britain through Time, University of Portsmouth (https://www.visionofbritain.org.uk/), as transcribed for my seaside railways study; largest towns from Wikipedia, "List of towns and cities in England by historical population" (CC BY-SA 4.0).
- Railway stations: Wikidata (CC0).
- Places: OS Open Names, Ordnance Survey, Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026. Counties: ONS, Open Government Licence v3.0. A-roads: OpenStreetMap (ODbL).
- Base map tiles on the page: Esri. Map library: Leaflet.

The text and derived data are released under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), because they draw on Wikipedia. `data/traces.csv`, `data/county_density.csv` and `data/inscriptions.csv` contain OpenStreetMap data and are released under the Open Database License 1.0 (https://opendatacommons.org/licenses/odbl/1-0/). Code is MIT (see `LICENSE`).

Companion studies: [Canal Mania](https://tristan-hotham.github.io/canal-mania/), [Did the railway invent the seaside?](https://tristan-hotham.github.io/seaside-railways/) and [How Roman is your road?](https://tristan-hotham.github.io/how-roman-is-your-road/).

## Citation

Hotham, T. (2026) *Turnpikes and coaching towns: England's turnpike trusts, their surviving milestones and the growth of towns*. Zenodo. https://doi.org/10.5281/zenodo.23729648

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
