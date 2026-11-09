# Who named Antarctica? The nations, years and people behind twenty thousand Antarctic place names

A map and analysis of 20,151 named features in the SCAR Composite Gazetteer of Antarctica (39,187 names in 25 national gazetteers): which nation named each feature, when, and after what or whom, with the honoured people linked through Wikidata to their birthplaces. Click any name on the polar map to read its story and see where its namesake was born.

Interactive page: https://maps.tristanhotham.com/antarctica-names/
Paper: https://doi.org/10.5281/zenodo.24075309
Blog post: https://blog.tristanhotham.com/2026/10/31/antarctica-names/

## Headline results

- Naming nations: the United States named 5,253 features (26.1%), the United Kingdom 3,981 (19.8%); then Norway, Bulgaria, Australia, New Zealand and Russia (6 to 8% each).
- Meanings: of features whose narrative records it (81.2%), 57.2% honour a person and 18.2% are descriptive. 82.8% of American names honour a person; 86.0% of Japanese and 60.9% of Norwegian names are descriptive; 57.0% of Bulgarian names recall places in Bulgaria.
- Claims: claimants name mostly inside their sectors (Argentina 99.5%, Australia 95.8%) but name a minority of what they claim (Australia 37.9% of its territory, Argentina 5.5%). The United States named 48.0% of the Ross Dependency and 95.7% of Marie Byrd Land.
- When: 43.5% of dated names were given 1960 to 1979; peak decade the 1960s (5,384); 18.1% since 2000, 48.0% of them Bulgarian.
- People: commonest surnames Smith (35), Davis, Brown, Johnson, Wilson; 33.4% of people honoured were scientists or surveyors and 18.2% naval or military (30.4% on American names).
- Women: 315 of 9,353 person names (3.4%); before 1990 63.5% of them were royals or relatives; since 1990 women are 10.3% of people honoured.
- Birthplaces (Wikidata, 1,449 people placed on a continent): 74.0% born in Europe, 17.5% in North America.
- Different names: 1,038 features (8.7% of those in more than one list) carry names that differ by more than spelling, mostly on the Antarctic Peninsula.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`): a Leaflet polar map (EPSG:3031, in km) with a nation picker and colour modes, linked to a world map of birthplaces, plus charts. |
| `header.png` | Social card, 1200 x 630. |
| `data/features.csv.gz` | Gzipped (also unzipped in the Zenodo archive). One row per feature: SCAR common id, lead name, coordinates (lat/lon and EPSG:3031 km), type, gazetteers and all names, naming nation and the rule and text that decided it, naming year and its source, what it is named after (kind), the honoree text, person and surname, woman flag, Wikidata person. |
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

- Gazetteer names grouped by SCAR common id into 20,151 features (8 duplicate ids merged).
- Naming nation: the namer in the first naming statement ("named by US-ACAN", "by the BrAE", "by Charcot") in a fixed order of gazetteers (10,831 features); else the only national list holding it (6,397); else the expedition said to have discovered or charted it (1,559); else the earliest approval (956); 401 unknown; 7 corrected by hand after reading every land, coast, sea and ice shelf.
- Meaning: the words after "named for/after" sorted by rules into person, ship, place, description and so on. Naming year from the naming statement, else the first approval.
- Checks: every possible woman read by hand (368 candidates); every Wikidata link whose namesake is not in the feature's names read; 21 country or state-level birthplaces unmapped; duplicates merged; random audit of 60 features (7 first-pass faults, fixed); an independent review then corrected 196 more readings, added 106 missed women, removed 5 wrong Wikidata links and fixed 226 British approval dates stored a century early (1901 for 2001).

## Caveats

Narratives are uneven (many Russian, Argentine and Chinese entries have none in English): 18.8% of features have no recorded meaning. The rules misread some narratives, mostly by filing people as "other". Naming years are often approval years. Wikidata covers only part of the people honoured. Claims are drawn as sectors to 60 S; the 254 undersea features are counted but left out of every claim share, and Peter I Island counts with Norway's claim. Where no narrative names the namer, the discovering expedition stands in (1,559 features). Features named after a couple or family are not counted as honouring a woman.

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

Hotham, T. (2026) Who named Antarctica? The nations, years and people behind twenty thousand Antarctic place names. Zenodo. https://doi.org/10.5281/zenodo.24075309

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
