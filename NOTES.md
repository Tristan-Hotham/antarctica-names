# antarctica-names: working notes
- Brief: /home/claude/work/new9/BRIEFS.md item 2 (+ shared rules new8/BRIEFS.md top, newdata/BRIEF.md).
- Raw: /home/claude/newdata/raw_new9/scar.csv.gz (SCAR CGA via AADC, CC BY 4.0), antarctica.tsv.gz (Wikidata via QLever, CC0).
- Wikidata QID labels: no labels for types/countries in the raw extract; label dictionary built in /home/claude/scratch/qlabels.json from header-matched
  QID/label column pairs across /home/claude/newdata TSVs, plus CoDEx English entity labels (github tsafavi/codex) and occupation lists (GitHub).
- Unit: a feature = one scar_common_id. Gazetteer country = country_name (which national committee lists the name, including adoptions/translations).
  Originating nation parsed from the "named by" clause of English narratives (US > UK > NZ > AU > others), else single-gazetteer country, else earliest dated.
- 01_clean.py done: 20,151 features (8 duplicate common ids merged), honour kind by rules in parse.py; women candidates all read by hand
  (overrides_women.csv, 209 yes); 21 country/state-level birthplaces left unmapped (overrides_people.csv); Wikidata link mismatches (120) read:
  transliterations, no wrong links found except kind fixes. Audit: first random sample 100 (pre-tuning, ~91% kind correct), second 60
  (data/audit_sample_60.csv: 7 first-pass faults of 58 decidable, 3 fixed by rules, 4 by override).
- Nation attribution: added 'discoverer' fallback (first expedition said to have discovered/charted the feature) after spotting
  Queen Maud Land etc. attributed to the US by earliest approval. Audit of all 153 Lands/Coasts/Seas/Ice shelves by eye: 8 nation
  overrides (overrides_features.csv). Remaining 'earliest approval' attributions (956) are the weakest; said in caveats.
- Steps done: 01_clean, 02_basemap (OFM z6 ocean -> coast incl shelves), 03_analysis, 04_build_site (+asserts), 05_figures, qa.js (24/24 ok).
- DONE (antarctica-names): page (QA 24/24 desktop+phone, no console errors), 8 figures, paper (11 pp, https://doi.org/10.5281/zenodo.24075309 placeholder, DOI env var
  fills it), blog (8 figs), zenodo zip+metadata, collage 3000x1900, header, post.md, README (all numbers from results.json; asserts in
  04/06/07). Study ~42 MB.
- References to verify (paper/blog): Alberts (ed.) 1995 Geographic Names of the Antarctic, 2nd ed., NSF/US BGN; Antarctic Treaty 1959,
  UNTS 402, 71; Stewart 2011 Antarctica: An Encyclopedia, 2nd ed., McFarland; Bast & Buchhold 2017 QLever CIKM 647-656; Vrandecic &
  Kroetzsch 2014 CACM 57(10) 78-85; SCAR CGA dataset citation (title/publisher only; exact AADC citation string not verified).
- Known weak spots: 956 features attributed by earliest approval date; 18.8% features no recorded meaning; occupation-like "roles" are
  keyword reads of narrative text.
- REVIEW (independent reviewer, 2026): pipeline re-run, reproducible. Fixes: (1) 226 UK date_named values 1901-1910 are 2001-2010
  (century slip; date_named_old confirms) -> +100 in 01_clean; heroic-age dated names 374 -> 148, wording softened (approval-date bias).
  (2) Women: 106 missed women added after reading candidates from word cues, gender-guesser first names, Slavic surnames, Wikidata P21
  (209 -> 315, 2.3% -> 3.4%); couples/families not counted. (3) 196 kind corrections (people in "other", Soviet descriptive names filed
  as people, myths etc.), applied before person/women parsing (block moved in 01_clean). (4) 5 wrong Wikidata P138 links removed.
  (5) Undersea = SCAR class 6 or GEBCO-only (254, was 80), excluded from claim shares; GEBCO/SCUFN not counted as a nation (26).
  (6) Peter I Island (59 features) counts with Norway's claim, not Marie Byrd Land (US share 91% -> 95.7%). (7) Texts: "Nobody was
  born in Antarctica" removed; "most ... by the US" -> "nearly half"; Argentina 99.5% not "100%"; merge distance "five km";
  refs verified (Alberts place Arlington VA; SCAR citation per AADC). Collage labels boxed; legend title wrapped; page "Ross Sea" label dropped.
  Remaining weak spots: 'discoverer' nation rule (1,559) can credit the photographing expedition; ~8% of stated kinds still misread
  in a 60-feature re-audit (4 to 5 'other' that are association/nature/descriptive).
