"""Step 8: README.md and reddit/post.md from data/results.json."""
from common import *
R = jload(f"{DATA}/results.json"); NN = R["nation_n"]; C = R["claim_n"]; S = R["source"]
t = f"""# Who named Antarctica? The nations, years and people behind twenty thousand Antarctic place names

A map and analysis of {S['features']:,} named features in the SCAR Composite Gazetteer of Antarctica ({S['rows']:,} names in {S['gazetteers']} national gazetteers): which nation named each feature, when, and after what or whom, with the honoured people linked through Wikidata to their birthplaces. Click any name on the polar map to read its story and see where its namesake was born.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24075309}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/antarctica-names/}}

## Headline results

- Naming nations: the United States named {NN['United States']['n']:,} features ({NN['United States']['pct']:.1f}%), the United Kingdom {NN['United Kingdom']['n']:,} ({NN['United Kingdom']['pct']:.1f}%); then Norway, Bulgaria, Australia, New Zealand and Russia (6 to 8% each).
- Meanings: of features whose narrative records it ({S['stated_pct']:.1f}%), {R['kind']['person']['pct_stated']:.1f}% honour a person and {R['kind']['descriptive']['pct_stated']:.1f}% are descriptive. {NN['United States']['person_pct']:.1f}% of American names honour a person; {NN['Japan']['descriptive_pct']:.1f}% of Japanese and {NN['Norway']['descriptive_pct']:.1f}% of Norwegian names are descriptive; {NN['Bulgaria']['place_pct']:.1f}% of Bulgarian names recall places in Bulgaria.
- Claims: claimants name mostly inside their sectors (Argentina {NN['Argentina']['own_claim_pct']:.1f}%, Australia {NN['Australia']['own_claim_pct']:.1f}%) but name a minority of what they claim (Australia {C['Australia']['own_pct']:.1f}% of its territory, Argentina {C['Argentina']['own_pct']:.1f}%). The United States named {C['New Zealand']['top'][0]['pct']:.1f}% of the Ross Dependency and {C['Unclaimed']['top'][0]['pct']:.1f}% of Marie Byrd Land.
- When: {R['eras'][5]['pct']:.1f}% of dated names were given 1960 to 1979; peak decade the {R['peak_decade']}s ({R['peak_decade_n']:,}); {R['since2000_pct']:.1f}% since 2000, {R['bulg_since2000_pct']:.1f}% of them Bulgarian.
- People: commonest surnames Smith ({R['surnames'][0]['person']}), Davis, Brown, Johnson, Wilson; {R['roles']['All']['science']['pct']:.1f}% of people honoured were scientists or surveyors and {R['roles']['All']['military']['pct']:.1f}% naval or military ({R['roles']['United States']['military']['pct']:.1f}% on American names).
- Women: {R['women']['n']} of {R['kind']['person']['n']:,} person names ({R['women']['pct_person']:.1f}%); before 1990 {R['women']['pre1990_rel_pct']:.1f}% of them were royals or relatives; since 1990 women are {R['women']['since1990_pct']:.1f}% of people honoured.
- Birthplaces (Wikidata, {R['people']['located']:,} people placed on a continent): {R['people']['europe_pct']:.1f}% born in Europe, {R['people']['cont']['North America']['pct']:.1f}% in North America.
- Different names: {R['different']['n']:,} features ({R['different']['pct']:.1f}% of those in more than one list) carry names that differ by more than spelling, mostly on the Antarctic Peninsula.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`): a Leaflet polar map (EPSG:3031, in km) with a nation picker and colour modes, linked to a world map of birthplaces, plus charts. |
| `header.png` | Social card, 1200 x 630. |
| `data/features.csv` | One row per feature: SCAR common id, lead name, coordinates (lat/lon and EPSG:3031 km), type, gazetteers and all names, naming nation and the rule and text that decided it, naming year and its source, what it is named after (kind), the honoree text, person and surname, woman flag, Wikidata person. |
| `data/names.csv` | One row per gazetteer name (SCAR gaz_id), with its feature id, country list, coordinates and approval year. |
| `data/people.csv` | People in Wikidata that features are named after: birth year, birthplace coordinates, modern country and continent, nearest large town, features. |
| `data/overrides_*.csv` | Documented corrections: women read by hand (`overrides_women.csv`), kind and nation fixes (`overrides_features.csv`), birthplaces that are only a country or state (`overrides_people.csv`), duplicate common ids merged (`overrides_merge.csv`). |
| `data/audit_sample_60.csv` | Random audit of the rule-based reading, with verdicts. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/base_*.geojson`, `data/world.geojson` | Page data and base maps. |
| `code/` | Scripts, run in order (`parse.py` holds the narrative rules), templates, and `qa.js` for screenshots. |
| `release/` | Paper PDF and LaTeX (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots at desktop and phone widths. |

## Method in brief

- Gazetteer names grouped by SCAR common id into {S['features']:,} features ({S['merged']} duplicate ids merged).
- Naming nation: the namer in the first naming statement ("named by US-ACAN", "by the BrAE", "by Charcot") in a fixed order of gazetteers ({S['nation_src']['narrative']:,} features); else the only national list holding it ({S['nation_src']['only gazetteer']:,}); else the expedition said to have discovered or charted it ({S['nation_src']['discoverer']:,}); else the earliest approval ({S['nation_src']['earliest approval']:,}); {R['not_known']} unknown; {S['nation_src'].get('override', 0)} corrected by hand after reading every land, coast, sea and ice shelf.
- Meaning: the words after "named for/after" sorted by rules into person, ship, place, description and so on. Naming year from the naming statement, else the first approval.
- Checks: every possible woman read by hand ({R['checks']['women_read']} candidates); every Wikidata link whose namesake is not in the feature's names read; {R['checks']['bp_unmapped']} country or state-level birthplaces unmapped; duplicates merged; random audit of {R['checks']['audit_n']} features ({R['checks']['audit_first_faults']} first-pass faults, fixed); an independent review then corrected {R['checks']['review_kind']} more readings, added {R['checks']['review_women']} missed women, removed {R['checks']['links_removed']} wrong Wikidata links and fixed {R['checks']['uk_century_fixed']} British approval dates stored a century early (1901 for 2001).

## Caveats

Narratives are uneven (many Russian, Argentine and Chinese entries have none in English): {R['kind']['unknown']['pct']:.1f}% of features have no recorded meaning. The rules misread some narratives, mostly by filing people as "other". Naming years are often approval years. Wikidata covers only part of the people honoured. Claims are drawn as sectors to 60 S; the {S['undersea']} undersea features are counted but left out of every claim share, and Peter I Island counts with Norway's claim. Where no narrative names the namer, the discovering expedition stands in ({S['nation_src']['discoverer']:,} features). Features named after a couple or family are not counted as honouring a woman.

## Sources and licences

- Scientific Committee on Antarctic Research (SCAR), Composite Gazetteer of Antarctica, hosted by the Australian Antarctic Data Centre (CC BY 4.0).
- Wikidata contributors (CC0), queried with QLever.
- OpenStreetMap contributors (ODbL), vector tiles from OpenFreeMap; Natural Earth (public domain).
- Text, figures and derived data CC BY 4.0; code MIT (see LICENSE).

## How to rerun

```
cd code
python3 01_clean.py && python3 02_basemap.py && python3 03_analysis.py && python3 04_build_site.py && python3 05_figures.py && python3 06_paper.py
cd .. && python3 reddit/collage.py && python3 code/08_readme.py && cd code && python3 07_release.py
```
Raw input paths are documented in `code/common.py`. The label dictionary for Wikidata ids (`LABELS`) is optional: it only names countries in `people.csv`.

## Citation

Hotham, T. (2026) Who named Antarctica? The nations, years and people behind twenty thousand Antarctic place names. Zenodo. {{https://doi.org/10.5281/zenodo.24075309}}

{AI}
"""
for bad in ("—", "–", "--"): assert bad not in t.replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(t)
K = R["kind"]
p = f"""**Title:** [OC] Who named Antarctica? I mapped {S['features']:,} Antarctic place names by the nation that named them: the US and UK named {R['us_uk_pct']:.0f}%, and only {R['women']['pct_person']:.1f}% of the people honoured are women

**Body:**

Antarctica has no native place names: almost all of its twenty thousand names were given in the last two centuries, by two dozen countries at once. The SCAR Composite Gazetteer combines every national list, and most entries say who named the place and after what. I read those notes for every feature.

- The United States named {NN['United States']['pct']:.0f}% of features and the United Kingdom {NN['United Kingdom']['pct']:.0f}%. Then Norway, Bulgaria, Australia, New Zealand and Russia.
- {K['person']['pct_stated']:.0f}% of names with a recorded meaning honour a person. {NN['Japan']['descriptive_pct']:.0f}% of Japanese names are descriptive ("crescent rock"), and {NN['Bulgaria']['place_pct']:.0f}% of Bulgarian names are towns and rivers in Bulgaria.
- The US, which claims nothing, named {C['New Zealand']['top'][0]['pct']:.0f}% of the features in New Zealand's Ross Dependency. Argentina named only {C['Argentina']['own_pct']:.1f}% of the features in its own claim; Britain named {C['Argentina']['top'][0]['pct']:.0f}%.
- {R['eras'][5]['pct']:.0f}% of dated names were given between 1960 and 1979, after the International Geophysical Year.
- The commonest surnames on the map are Smith, Davis, Brown, Johnson and Wilson: lots of Navy aircrew, scientists and station staff.
- Before 1990, {R['women']['pre1990_rel_pct']:.0f}% of the women honoured were queens or the wives and daughters of explorers and patrons.

Interactive map (click any name to see who named it, when, after whom, and where that person was born): {PAGE}

**Source comment:**

Data: SCAR Composite Gazetteer of Antarctica (Australian Antarctic Data Centre, CC BY 4.0), {S['rows']:,} names in {S['gazetteers']} national gazetteers grouped into {S['features']:,} features. The naming nation and what each name honours are read from the gazetteer narratives by rules (a random audit found {R['checks']['audit_first_faults']} misreadings in {R['checks']['audit_decidable']}, mostly people filed as "other"), and every possible woman was read by hand. Birthplaces from Wikidata (CC0) for {R['people']['located']:,} people. Coast and ice shelves from OpenStreetMap via OpenFreeMap; Natural Earth. Tools: Python (pandas, geopandas, matplotlib), Leaflet. Paper, data and code: {REPO}
"""
for bad in ("—", "–", "--"): assert bad not in p, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(p)
print("README", len(t.split()), "words; post", len(p.split()))
