# Reddit post

## Title

[OC] Did the turnpike make the town? England's 1,245 turnpike trusts (1663 to 1866), the 10,927 milestones and toll houses still recorded, and whether towns on the turnpikes grew faster

## Body

I built a list of England's turnpike trusts from Wikipedia's regional lists, placed the towns named in each trust, mapped every milestone, milepost and toll house recorded in Wikidata and OpenStreetMap, and checked census growth from 1801.

- Turnpike mania was real: 254 trusts were founded in the 1750s alone, and 44% of dated trusts in 1750 to 1772. Towns near London were only about a decade ahead of the rest.
- 51% of surviving milestones stand within 50 m of a modern A-road.
- Places named in a trust grew faster in 1801 to 1831 (1.50% against 1.07% a year), but once size is allowed for the gap is 0.10 points (-0.13 to 0.34).

Caveat: the growth sample is 345 places, mostly villages in Cambridgeshire, Huntingdonshire and the south west, and milestones are survivors recorded unevenly by county.

Interactive version: https://tristan-hotham.github.io/turnpike-towns/

## Source comment

Source: Wikipedia, "Turnpike trusts in" South East England, the East of England, the East Midlands, the West Midlands, North East England, North West England, Yorkshire and South West England, plus "Turnpike trust" and "Mail coach" (CC BY-SA 4.0); milestones, mileposts and toll houses from Wikidata (CC0) and OpenStreetMap (© OpenStreetMap contributors, ODbL) via QLever; census populations 1801 to 1901 from Wikidata (CC0) and A Vision of Britain through Time (University of Portsmouth); OS Open Names (OGL v3, contains OS data © Crown copyright and database right 2026); Natural Earth coastline (public domain).

Tools: Python (pandas, numpy, scipy, statsmodels, pyproj, shapely, matplotlib).

Interactive version: https://tristan-hotham.github.io/turnpike-towns/
Blog post: https://blog.tristanhotham.com/2026/10/28/turnpike-towns/
Paper: https://doi.org/10.5281/zenodo.23729648
